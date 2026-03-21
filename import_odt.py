import streamlit as st
import io, time
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
    # On repère les indices des lignes contenant "Ingrédients"
    indices_recettes = [i for i, l in enumerate(lignes) if "Ingrédients" in l]
    
    for start_idx in indices_recettes:
        # Le titre est la ligne juste avant "Ingrédients"
        titre = lignes[start_idx - 1] if start_idx > 0 else "Nouvelle Recette"
        
        # Délimitation de la recette actuelle
        next_ingredients = [i for i in indices_recettes if i > start_idx]
        end_idx = next_ingredients[0] if next_ingredients else len(lignes)
        
        bloc_recette = lignes[start_idx:end_idx]
        
        # Séparation Ingrédients / Préparation (on cherche le mot Préparation ou Cuisson)
        idx_prep = next((i for i, l in enumerate(bloc_recette) if "Préparation" in l or "Cuisson" in l), len(bloc_recette))
        
        lignes_ingredients = bloc_recette[1:idx_prep] 
        lignes_preparation = bloc_recette[idx_prep:]
        
        # Traitement des ingrédients via ton parser habituel
        ing_list = [parser_ligne_ingredient(l) for l in lignes_ingredients if parser_ligne_ingredient(l)]
        
        # Si des lignes de la zone ingrédient ne sont pas parsées (ex: texte pur), on les garde en notes
        ing_bruts = [l for l in lignes_ingredients if not parser_ligne_ingredient(l)]
        
        prep_finale = "\n".join(lignes_preparation)
        if ing_bruts:
            prep_finale = "NOTES INGRÉDIENTS :\n" + "\n".join(ing_bruts) + "\n\n" + prep_finale

        recettes.append({
            "nom": titre,
            "ing_list": ing_list,
            "prep_propre": prep_finale
        })
    
    return recettes

def afficher():
    # TITRE EXACT
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
            
            # Formulaire avec tes clés de session pour le reset automatique
            nom = st.text_input("Titre de la recette", value=r['nom'], key=f"n{idx}")
            
            col_cat, col_app = st.columns(2)
            with col_cat:
                _, cats_existantes = get_index_options()
                options_cat = cats_existantes + ["➕ Ajouter une catégorie..."]
                def_idx = cats_existantes.index("Desserts") if "Desserts" in cats_existantes else 0
                choix_cat = st.selectbox("Catégorie", options_cat, index=def_idx, key=f"c{idx}")
                
                if choix_cat == "➕ Ajouter une catégorie...":
                    cat = st.text_input("Nom de la nouvelle catégorie", key=f"nc{idx}")
                else:
                    cat = choix_cat

            with col_app:
                # LISTE APPAREILS EXACTE
                appareils = ["Aucun", "Cookeo", "Thermomix", "Ninja"]
                appareil = st.selectbox("Appareil utilisé", options=appareils, key=f"a{idx}")

            st.subheader("Ingrédients détectés")
            ing_df = st.data_editor(r['ing_list'], num_rows="dynamic", use_container_width=True, key=f"ed{idx}")
            
            st.subheader("Instructions de préparation")
            etapes = st.text_area("Texte de la recette", value=r['prep_propre'], height=300, key=f"et{idx}")

            st.divider()
            # BOUTONS AVEC TES LABELS
            c_skip, c_del, c_save = st.columns([1,1,1])
            
            if c_skip.button("⏭️ Passer", use_container_width=True):
                st.session_state.import_idx += 1
                st.rerun()
                
            if c_del.button("🗑️ Supprimer", use_container_width=True):
                st.session_state.liste_odt.pop(idx)
                st.rerun()

            if c_save.button("✅ Enregistrer", type="primary", use_container_width=True):
                with st.spinner("Sauvegarde..."):
                    if sauvegarder_recette_complete(nom, cat, ing_df, etapes, None, appareil=appareil):
                        st.success(f"'{nom}' enregistré avec succès !")
                        time.sleep(1)
                        st.session_state.import_idx += 1
                        st.rerun()
        else:
            st.success("Toutes les recettes ont été traitées !")
            if st.button("Charger un nouveau fichier ODT"):
                st.session_state.liste_odt = []
                st.session_state.import_idx = 0
                st.rerun()
