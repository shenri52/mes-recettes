import streamlit as st
import io, time, re
from odf import opendocument, text, teletype

from utils import (
    sauvegarder_recette_complete, 
    parser_ligne_ingredient, 
    get_index_options,
    verifier_doublon_recette
)

def extraire_donnees_odt(file_bytes):
    doc = opendocument.load(io.BytesIO(file_bytes))
    lignes = [teletype.extractText(p).strip() for p in doc.getElementsByType(text.P) if teletype.extractText(p).strip()]
    
    recettes = []
    # On repère les sections par le mot "Ingrédients"
    indices_recettes = [i for i, l in enumerate(lignes) if "Ingrédients" in l]
    
    for start_idx in indices_recettes:
        # Titre : ligne juste avant "Ingrédients"
        titre = lignes[start_idx - 1] if start_idx > 0 else "Nouvelle Recette"
        
        next_indices = [i for i in indices_recettes if i > start_idx]
        end_idx = next_indices[0] if next_indices else len(lignes)
        
        bloc_recette = lignes[start_idx:end_idx]
        texte_bloc = "\n".join(bloc_recette)
        
        # limitation zone Préparation
        idx_prep = next((i for i, l in enumerate(bloc_recette) if re.search(r"Préparation|Instructions", l, re.I)), len(bloc_recette))
        
        lignes_ingredients = bloc_recette[1:idx_prep] 
        lignes_preparation = bloc_recette[idx_prep:]
        
        # --- TECTION S TEMPS (STRICTE & VI PAR FAUT) ---
        t_prep, t_cuisson = "", ""
        
        # Cherche uniquement si format "Préparation : 10 min" est présent
        found_p = re.search(r"Préparation\s*[:\-]?\s*(\d+\s*(?:min|h|minutes))", texte_bloc, re.I)
        if found_p: t_prep = found_p.group(1)
            
        found_c = re.search(r"Cuisson\s*[:\-]?\s*(\d+\s*(?:min|h|minutes))", texte_bloc, re.I)
        if found_c: t_cuisson = found_c.group(1)

        # --- PARSING S INGRÉDIENTS (Séparation Chiffre / Nom) ---
        ing_list = []
        for l in lignes_ingredients:
            # On vérifie si la ligne commence par un chiffre (ex: "3 pommes" ou "200g sucre")
            match_nombre = re.match(r"^(\d+[g\s]*[a-zA-Z]*)\s+(.*)", l)
            if match_nombre:
                ing_list.append({"Ingrédient": match_nombre.group(2).strip(), "Quantité": match_nombre.group(1).strip()})
            else:
                parsed = parser_ligne_ingredient(l)
                if parsed:
                    ing_list.append(parsed)
                else:
                    ing_list.append({"Ingrédient": l, "Quantité": ""})
        
        recettes.append({
            "nom": titre, 
            "ing_list": ing_list, 
            "prep_propre": "\n".join(lignes_preparation),
            "t_prep": t_prep, 
            "t_cuisson": t_cuisson
        })
    
    return recettes

def afficher():

    if 'import_idx' not in st.session_state: st.session_state.import_idx = 0
    if 'liste_odt' not in st.session_state: st.session_state.liste_odt = []

    file = st.file_uploader("Charger un document ODT", type="odt")

    if file and not st.session_state.liste_odt:
        with st.spinner("Analyse du document..."):
            st.session_state.liste_odt = extraire_donnees_odt(file.getvalue())
            st.rerun()

    if st.session_state.liste_odt:
        idx = st.session_state.import_idx
        if idx < len(st.session_state.liste_odt):
            r = st.session_state.liste_odt[idx]
            
            st.write(f"### Vérification : {idx+1} / {len(st.session_state.liste_odt)}")
            st.progress((idx + 1) / len(st.session_state.liste_odt))
            
            nom = st.text_input("Titre de la recette", value=r['nom'], key=f"n{idx}")
            if verifier_doublon_recette(nom):
                st.warning("⚠️ Ce nom existe déjà. À l'enregistrement, la date du jour sera ajoutée pour éviter d'écraser l'ancienne.")
            
            col_cat, col_app = st.columns(2)
            with col_cat:
                _, cats_existantes = get_index_options()
                # On force le choix avec "---" en premier
                options_cat = ["---"] + sorted([c for c in cats_existantes if c]) + ["➕ Ajouter une catégorie..."]
                
                choix_cat = st.selectbox("Catégorie", options_cat, index=0, key=f"c{idx}")
                
                # Détermination de la catégorie finale
                if choix_cat == "➕ Ajouter une catégorie...":
                    cat_finale = st.text_input("Nom de la catégorie", key=f"nc{idx}").strip()
                else:
                    cat_finale = choix_cat

            with col_app:
                appareils = ["Aucun", "Cookeo", "Thermomix", "Ninja", "Four"]
                appareil = st.selectbox("Appareil utilisé", options=appareils, key=f"a{idx}")

            # Champs temps (Vides si non détectés)
            col_t1, col_t2 = st.columns(2)
            t_prep = col_t1.text_input("⏳ Temps Préparation", value=r['t_prep'], key=f"tp{idx}", placeholder="Non détecté")
            t_cuis = col_t2.text_input("🔥 Temps Cuisson", value=r['t_cuisson'], key=f"tc{idx}", placeholder="Non détecté")

            st.subheader("Ingrédients détectés")
            ing_df = st.data_editor(r['ing_list'], num_rows="dynamic", use_container_width=True, key=f"ed{idx}")
                       
            # --- BLOC PRÉPARATION ---
            st.subheader("Instructions de préparation")

            # La zone de texte avec ton titre "Texte de la recette"
            etapes = st.text_area("", value=r['prep_propre'], height=300, key=f"et{idx}")

            st.divider()
            c_skip, c_del, c_save = st.columns([1,1,1])
            
            if c_skip.button("⏭️ Passer", use_container_width=True):
                st.session_state.import_idx += 1
                st.rerun()
                
            if c_del.button("🗑️ Supprimer", use_container_width=True):
                st.session_state.liste_odt.pop(idx)
                st.rerun()

            if c_save.button("✅ Enregistrer", type="primary", use_container_width=True):
                # Sécurité Catégorie Obligatoire
                if not cat_finale or cat_finale == "---":
                    st.error("⚠️ Veuillez choisir ou ajouter une catégorie.")
                else:
                    with st.spinner("Sauvegarde..."):
                        # Correction API : Gestion des doublons avant l'envoi
                        nom_propre = nom.strip()
                        if verifier_doublon_recette(nom_propre):
                            # On ajoute la date pour que le nom de fichier soit unique sur GitHub
                            nom_propre = f"{nom_propre} ({time.strftime('%d-%m-%Y')})"
                        
                        # Appel de la sauvegarde avec les bonnes variables
                        if sauvegarder_recette_complete(nom_propre, cat_finale, ing_df, etapes, None, appareil=appareil, t_prep=t_prep, t_cuisson=t_cuis):
                            st.success(f"'{nom_propre}' enregistré !")
                            time.sleep(0.5)
                            st.session_state.liste_odt.pop(idx)
                            st.rerun()
        else:
            st.balloons()
            st.success("Toutes les recettes ont été traitées ! ✨")
            if st.button("Charger un nouveau fichier ODT"):
                st.session_state.liste_odt = []
                st.session_state.import_idx = 0
                st.rerun()
