import streamlit as st
import io, zipfile, time

from odf import opendocument, text, teletype
from utils import (
    sauvegarder_recette_complete, 
    traiter_et_compresser_image, 
    parser_ligne_ingredient, 
    get_index_options
)

def extraire_donnees_odt(file_bytes):
    doc = opendocument.load(io.BytesIO(file_bytes))
    lignes = [teletype.get_string(p) for p in doc.getElementsByType(text.P) if teletype.get_string(p).strip()]
    
    # Extraction et compression des images du document
    biblio_img = {}
    with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
        for name in z.namelist():
            if name.startswith('Pictures/'):
                img_comp = traiter_et_compresser_image(io.BytesIO(z.read(name)))
                if img_comp:
                    # On stocke l'image avec son nom court (ex: DSCF3495)
                    biblio_img[name.split('/')[-1].split('.')[0]] = img_comp

    recettes = []
    bloc = []
    # Découpage : on change de recette dès qu'on voit "Ingrédients"
    for i, ligne in enumerate(lignes):
        if "Ingrédients" in ligne and i > 0:
            titre = bloc.pop(-1) if bloc else "Sans titre"
            recettes.append({"nom": titre, "brut": "\n".join(bloc), "img": None})
            bloc = [ligne]
        else:
            bloc.append(ligne)
    if bloc: 
        recettes.append({"nom": bloc[0], "brut": "\n".join(bloc), "img": None})

    # Nettoyage final pour chaque bloc trouvé
    for r in recettes:
        # Correspondance image
        for name, data in biblio_img.items():
            if name in r['brut']: 
                r['img'] = data
                break
        
        # Extraction des ingrédients
        lignes_r = r['brut'].split('\n')
        r['ing_list'] = [parser_ligne_ingredient(l) for l in lignes_r if parser_ligne_ingredient(l)]
        
        # Nettoyage simple du texte des étapes
        r['etapes_brutes'] = r['brut'].split("Préparation :")[-1].strip() if "Préparation :" in r['brut'] else r['brut']
    
    return recettes

def afficher():
    st.header("⚡ FlashImport ODT")
    
    if 'import_idx' not in st.session_state: st.session_state.import_idx = 0
    if 'liste_odt' not in st.session_state: st.session_state.liste_odt = []

    file = st.file_uploader("Charger un document ODT de recettes", type="odt")

    if file and not st.session_state.liste_odt:
        with st.spinner("Analyse du document et compression des images..."):
            st.session_state.liste_odt = extraire_donnees_odt(file.read())
            st.rerun()

    if st.session_state.liste_odt:
        idx = st.session_state.import_idx
        if idx < len(st.session_state.liste_odt):
            r = st.session_state.liste_odt[idx]
            
            st.write(f"### Vérification : {idx+1} / {len(st.session_state.liste_odt)}")
            st.progress((idx + 1) / len(st.session_state.liste_odt))
            
            col1, col2 = st.columns([2, 1])
            with col1:
                nom = st.text_input("Titre de la recette", value=r['nom'], key=f"n{idx}")
                _, cats = get_index_options()
                # On force 'Desserts' par défaut pour ton fichier
                cat = st.selectbox("Catégorie", options=cats, index=cats.index("Desserts") if "Desserts" in cats else 0)
                ing_df = st.data_editor(r['ing_list'], num_rows="dynamic", use_container_width=True, key=f"ed{idx}")
                etapes = st.text_area("Préparation", value=r['etapes_brutes'], height=250, key=f"et{idx}")

            with col2:
                if r['img']:
                    st.image(r['img'], caption="Image trouvée dans l'ODT")
                else:
                    st.info("Aucune image liée détectée.")

            c_skip, c_del, c_save = st.columns([1,1,1])
            if c_skip.button("⏭️ Passer"):
                st.session_state.import_idx += 1
                st.rerun()
                
            if c_del.button("🗑️ Ignorer"):
                st.session_state.liste_odt.pop(idx)
                st.rerun()

            if c_save.button("✅ Enregistrer sur GitHub", type="primary"):
                with st.spinner("Sauvegarde en cours..."):
                    if sauvegarder_recette_complete(nom, cat, ing_df, etapes, r['img']):
                        st.success(f"'{nom}' ajouté !")
                        time.sleep(1)
                        st.session_state.import_idx += 1
                        st.rerun()
        else:
            st.balloons()
            st.success("Toutes les recettes ont été traitées ! ✨")
            if st.button("Charger un autre fichier"):
                st.session_state.liste_odt = []
                st.session_state.import_idx = 0
                st.rerun()
