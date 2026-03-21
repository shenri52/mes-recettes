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
    # Correction : on utilise extractText
    lignes = [teletype.extractText(p) for p in doc.getElementsByType(text.P) if teletype.extractText(p).strip()]
    
    recettes = []
    bloc_actuel = []
    
    # Stratégie de découpage plus robuste
    for ligne in lignes:
        # Si la ligne ressemble à un titre (souvent avant "Ingrédients")
        # ou si c'est le tout début du fichier
        if "Ingrédients" in ligne and bloc_actuel:
            # Le titre est probablement la dernière ligne du bloc précédent
            titre = bloc_actuel.pop(-1) if bloc_actuel else "Nouvelle Recette"
            recettes.append({"nom": titre, "contenu_complet": bloc_actuel})
            bloc_actuel = [ligne]
        else:
            bloc_actuel.append(ligne)
    
    # Ajouter la dernière recette
    if bloc_actuel:
        recettes.append({"nom": bloc_actuel[0] if bloc_actuel else "Sans titre", "contenu_complet": bloc_actuel})

    # Nettoyage de chaque recette
    for r in recettes:
        lignes_r = r['contenu_complet']
        
        # 1. Extraction des ingrédients (tout ce qui ressemble à une dose/unité)
        r['ing_list'] = [parser_ligne_ingredient(l) for l in lignes_r if parser_ligne_ingredient(l)]
        
        # 2. Extraction de la préparation (On prend TOUT le texte qui n'est pas un ingrédient)
        # On filtre pour ne garder que les lignes de texte pur qui ne sont pas des ingrédients
        etapes_filtrees = []
        for l in lignes_r:
            if not parser_ligne_ingredient(l) and "Ingrédients" not in l:
                etapes_filtrees.append(l)
        
        r['prep_propre'] = "\n".join(etapes_filtrees).strip()
    
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
            
            # --- FORMULAIRE DE MODIFICATION ---
            nom = st.text_input("Titre de la recette", value=r['nom'], key=f"n{idx}")
            
            col_cat, col_app = st.columns(2)
            
            with col_cat:
                # Gestion des catégories (avec option ajout)
                _, cats_existantes = get_index_options()
                options_cat = cats_existantes + ["➕ Ajouter une catégorie..."]
                # On essaie de mettre "Desserts" par défaut
                def_idx = cats_existantes.index("Desserts") if "Desserts" in cats_existantes else 0
                choix_cat = st.selectbox("Catégorie", options_cat, index=def_idx, key=f"c{idx}")
                
                if choix_cat == "➕ Ajouter une catégorie...":
                    cat = st.text_input("Nom de la nouvelle catégorie", key=f"nc{idx}")
                else:
                    cat = choix_cat

            with col_app:
                # Ajout du bouton Appareil
                appareils = ["Aucun", "Cookeo", "Thermomix", "Ninja"]
                appareil = st.selectbox("Appareil utilisé", options=appareils, key=f"a{idx}")

            # Zone Ingrédients (Tableau éditable)
            st.subheader("Ingrédients détectés")
            ing_df = st.data_editor(r['ing_list'], num_rows="dynamic", use_container_width=True, key=f"ed{idx}")
            
            # Zone Préparation (Texte filtré)
            st.subheader("Instructions de préparation")
            etapes = st.text_area("Texte de la recette", value=r['prep_propre'], height=300, key=f"et{idx}")

            # --- ACTIONS ---
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
                    # On passe None pour l'image puisqu'on a retiré la détection
                    if sauvegarder_recette_complete(nom, cat, ing_df, etapes, None, appareil=appareil):
                        st.success(f"'{nom}' enregistré avec succès !")
                        time.sleep(1)
                        st.session_state.import_idx += 1
                        st.rerun()
        else:
            st.balloons()
            st.success("Toutes les recettes ont été traitées ! ✨")
            if st.button("Charger un nouveau fichier ODT"):
                st.session_state.liste_odt = []
                st.session_state.import_idx = 0
                st.rerun()
