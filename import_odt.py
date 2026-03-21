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
    # On repère les sections par le mot "Ingrédients"
    indices_recettes = [i for i, l in enumerate(lignes) if "Ingrédients" in l]
    
    for start_idx in indices_recettes:
        # Titre : ligne juste avant "Ingrédients"
        titre = lignes[start_idx - 1] if start_idx > 0 else "Nouvelle Recette"
        
        next_indices = [i for i in indices_recettes if i > start_idx]
        end_idx = next_indices[0] if next_indices else len(lignes)
        
        bloc_recette = lignes[start_idx:end_idx]
        texte_bloc = "\n".join(bloc_recette)
        
        # Délimitation zone Préparation
        idx_prep = next((i for i, l in enumerate(bloc_recette) if re.search(r"Préparation|Instructions", l, re.I)), len(bloc_recette))
        
        lignes_ingredients = bloc_recette[1:idx_prep] 
        lignes_preparation = bloc_recette[idx_prep:]
        
        # --- DÉTECTION DES TEMPS (STRICTE & VIDE PAR DÉFAUT) ---
        t_prep, t_cuisson = "", ""
        
        # Cherche uniquement si format "Préparation : 10 min" est présent
        found_p = re.search(r"Préparation\s*[:\-]?\s*(\d+\s*(?:min|h|minutes))", texte_bloc, re.I)
        if found_p: t_prep = found_p.group(1)
            
        found_c = re.search(r"Cuisson\s*[:\-]?\s*(\d+\s*(?:min|h|minutes))", texte_bloc, re.I)
        if found_c: t_cuisson = found_c.group(1)

        # --- PARSING DES INGRÉDIENTS (Séparation Chiffre / Nom) ---
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
    st.header("🖋️ Importer des recettes ODT")
    
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
            
            col_cat, col_app = st.columns(2)
            with col_cat:
                _, cats_existantes = get_index_options()
                options_cat = cats_existantes + ["➕ Ajouter une catégorie..."]
                def_idx = cats_existantes.index("Desserts") if "Desserts" in cats_existantes else 0
                choix_cat = st.selectbox("Catégorie", options_cat, index=def_idx, key=f"c{idx}")
                cat = st.text_input("Nom de la catégorie", key=f"nc{idx}") if choix_cat == "➕ Ajouter une catégorie..." else choix_cat

            with col_app:
                appareils = ["Aucun", "Cookeo", "Thermomix", "Ninja", "Four"]
                appareil = st.selectbox("Appareil utilisé", options=appareils, key=f"a{idx}")

            # Champs temps (Vides si non détectés)
            col_t1, col_t2 = st.columns(2)
            t_prep = col_t1.text_input("⏳ Temps Préparation", value=r['t_prep'], key=f"tp{idx}", placeholder="Non détecté")
            t_cuis = col_t2.text_input("🔥 Temps Cuisson", value=r['t_cuisson'], key=f"tc{idx}", placeholder="Non détecté")

            st.subheader("Ingrédients détectés")
            ing_df = st.data_editor(r['ing_list'], num_rows="dynamic", use_container_width=True, key=f"ed{idx}")
            
            # --- BLOC BOUTON ET ZONE DE TEXTE ---
            st.subheader("Préparation")
            
            if st.button("Corriger le texte", key=f"clean{idx}"):
                # 1. Récupération du texte actuel
                t = r['prep_propre']
                
                # 2. Correction orthographe (oeufs -> œufs)
                t = re.sub(r'oeufs?', lambda m: 'œuf' if m.group().lower() == 'oeuf' else 'œufs', t, flags=re.I)
                
                # 3. Majuscule en début de chaque phrase et nettoyage
                phrases = [s.strip().capitalize() for s in t.split('.') if s.strip()]
                t_corrige = ". ".join(phrases)
                if t_corrige and not t_corrige.endswith('.'):
                    t_corrige += "."
                
                # 4. MISE À JOUR CRITIQUE : on modifie la source dans la session_state
                st.session_state.liste_odt[idx]['prep_propre'] = t_corrige
                
                # 5. On force le rechargement pour afficher le texte propre
                st.rerun()

            # La zone de texte utilise la valeur mise à jour
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
                    if sauvegarder_recette_complete(nom, cat, ing_df, etapes, None, appareil=appareil, t_prep=t_prep, t_cuisson=t_cuis):
                        st.success(f"'{nom}' enregistré !")
                        time.sleep(0.5)
                        st.session_state.import_idx += 1
                        st.rerun()
        else:
            st.balloons()
            st.success("Toutes les recettes ont été traitées ! ✨")
            if st.button("Charger un nouveau fichier ODT"):
                st.session_state.liste_odt = []
                st.session_state.import_idx = 0
                st.rerun()
