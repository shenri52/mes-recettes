import streamlit as st
import io, time, re
from odf import opendocument, text, teletype

from utils import (
    sauvegarder_recette_complete, 
    parser_ligne_ingredient, 
    get_index_options
)

def extraire_donnees_odt(file_bytes):
    doc = opendocument.load(io.BytesIO(file_bytes))
    lignes = [teletype.extractText(p).strip() for p in doc.getElementsByType(text.P) if teletype.extractText(p).strip()]
    
    recettes = []
    indices_recettes = [i for i, l in enumerate(lignes) if "Ingrédients" in l]
    
    for start_idx in indices_recettes:
        titre = lignes[start_idx - 1] if start_idx > 0 else "Nouvelle Recette"
        next_ingredients = [i for i in indices_recettes if i > start_idx]
        end_idx = next_ingredients[0] if next_ingredients else len(lignes)
        
        bloc_recette = lignes[start_idx:end_idx]
        idx_prep = next((i for i, l in enumerate(bloc_recette) if "Préparation" in l or "Cuisson" in l), len(bloc_recette))
        
        lignes_ingredients = bloc_recette[1:idx_prep] 
        lignes_preparation = bloc_recette[idx_prep:]
        
        # --- DÉTECTION DES TEMPS (Regex) ---
        t_prep, t_cuisson = "15 min", "30 min" # Valeurs par défaut
        texte_complet = " ".join(bloc_recette)
        
        m_prep = re.search(r"Préparation\s*[:\-]?\s*(\d+\s*(min|h|minutes))", texte_complet, re.IGNORECASE)
        if m_prep: t_prep = m_prep.group(1)
        
        m_cuis = re.search(r"Cuisson\s*[:\-]?\s*(\d+\s*(min|h|minutes))", texte_complet, re.IGNORECASE)
        if m_cuis: t_cuisson = m_cuis.group(1)

        # --- TRAITEMENT DES INGRÉDIENTS AVEC SPLIT FORCÉ ---
        ing_list = []
        ing_bruts = []
        for l in lignes_ingredients:
            parsed = parser_ligne_ingredient(l)
            # Si le parser échoue à trouver une quantité (ex: "3 pommes" mis tout en ingrédient)
            if parsed and not parsed.get('Quantité'):
                # On tente un split manuel sur le premier chiffre
                match = re.match(r"^(\d+)\s*(.*)", l)
                if match:
                    parsed = {"Ingrédient": match.group(2).strip(), "Quantité": match.group(1).strip()}
            
            if parsed and parsed.get('Ingrédient'):
                ing_list.append(parsed)
            else:
                ing_bruts.append(l)
        
        prep_finale = "\n".join(lignes_preparation)
        if ing_bruts:
            prep_finale = "NOTES INGRÉDIENTS :\n" + "\n".join(ing_bruts) + "\n\n" + prep_finale

        recettes.append({
            "nom": titre, "ing_list": ing_list, "prep_propre": prep_finale,
            "t_prep": t_prep, "t_cuisson": t_cuisson
        })
    
    return recettes

def afficher():
    st.header("🖋️ Importer des recettes ODT")
    
    if 'import_idx' not in st.session_state: st.session_state.import_idx = 0
    if 'liste_odt' not in st.session_state: st.session_state.liste_odt = []

    file = st.file_uploader("Charger un document ODT", type="odt")

    if file and not st.session_state.liste_odt:
        with st.spinner("Analyse du texte..."):
            st.session_state.liste_odt = extraire_donnees_odt(file.getvalue())
            st.rerun()

    if st.session_state.liste_odt:
        idx = st.session_state.import_idx
        if idx < len(st.session_state.liste_odt):
            r = st.session_state.liste_odt[idx]
            
            st.write(f"### Vérification : {idx+1} / {len(st.session_state.liste_odt)}")
            st.progress((idx + 1) / len(st.session_state.liste_odt))
            
            nom = st.text_input("Titre de la recette", value=r['nom'], key=f"n{idx}")
            
            col_cat, col_app = st.columns(2)
            with col_cat:
                _, cats_existantes = get_index_options()
                options_cat = cats_existantes + ["➕ Ajouter une catégorie..."]
                def_idx = cats_existantes.index("Desserts") if "Desserts" in cats_existantes else 0
                choix_cat = st.selectbox("Catégorie", options_cat, index=def_idx, key=f"c{idx}")
                cat = st.text_input("Nom de la catégorie", key=f"nc{idx}") if choix_cat == "➕ Ajouter une catégorie..." else choix_cat

            with col_app:
                appareil = st.selectbox("Appareil utilisé", options=["Aucun", "Cookeo", "Thermomix", "Ninja", "Four"], key=f"a{idx}")

            # --- NOUVEAUX CHAMPS TEMPS ---
            col_t1, col_t2 = st.columns(2)
            t_prep = col_t1.text_input("⏳ Temps Préparation", value=r['t_prep'], key=f"tp{idx}")
            t_cuis = col_t2.text_input("🔥 Temps Cuisson", value=r['t_cuisson'], key=f"tc{idx}")

            st.subheader("Ingrédients détectés")
            ing_df = st.data_editor(r['ing_list'], num_rows="dynamic", use_container_width=True, key=f"ed{idx}")
            
            st.subheader("Instructions de préparation")
            # --- OPTION NETTOYAGE TEXTE ---
            if st.button("🪄 Nettoyer le texte (Majuscules & Espaces)", key=f"clean{idx}"):
                texte = r['prep_propre']
                # On remet une majuscule après chaque point et on réduit les espaces
                texte = ". ".join([s.strip().capitalize() for s in texte.split('.')])
                r['prep_propre'] = texte
                st.rerun()

            etapes = st.text_area("Texte de la recette", value=r['prep_propre'], height=300, key=f"et{idx}")

            st.divider()
            c_skip, c_del, c_save = st.columns([1,1,1])
            
            if c_skip.button("⏭️ Passer", use_container_width=True):
                st.session_state.import_idx += 1
                st.rerun()
                
            if c_del.button("🗑️ Supprimer", use_container_width=True):
                st.session_state.liste_odt.pop(idx)
                st.rerun()

            if c_save.button("✅ Enregistrer", type="primary", use_container_width=True):
                with st.spinner("Sauvegarde..."):
                    # On ajoute t_prep et t_cuisson à la sauvegarde
                    if sauvegarder_recette_complete(nom, cat, ing_df, etapes, None, appareil=appareil, t_prep=t_prep, t_cuisson=t_cuis):
                        st.success(f"'{nom}' enregistré !")
                        time.sleep(1)
                        st.session_state.import_idx += 1
                        st.rerun()
        else:
            st.balloons()
            st.success("Terminé ! ✨")
            if st.button("Charger un nouveau fichier ODT"):
                st.session_state.liste_odt = []
                st.session_state.import_idx = 0
                st.rerun()
