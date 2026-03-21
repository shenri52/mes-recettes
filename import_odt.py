import streamlit as st
import json, time, re, io, zipfile
from odf import opendocument, text, teletype
from datetime import datetime

# Import de tes fonctions existantes
from utils import envoyer_donnees_github, get_index_options, traiter_et_compresser_image, mettre_a_jour_index

def extraire_images_du_zip(fichier_bytes):
    """Extrait toutes les images du dossier Pictures/ de l'ODT et les compresse."""
    images_dict = {}
    try:
        with zipfile.ZipFile(io.BytesIO(fichier_bytes)) as z:
            for name in z.namelist():
                if name.startswith('Pictures/') and name.lower().endswith(('.png', '.jpg', '.jpeg')):
                    img_data = z.read(name)
                    # On utilise TA fonction de compression de utils.py
                    img_compressee = traiter_et_compresser_image(io.BytesIO(img_data))
                    if img_compressee:
                        # On garde le nom court pour la correspondance texte
                        short_name = name.split('/')[-1].split('.')[0]
                        images_dict[short_name] = img_compressee
    except Exception as e:
        st.error(f"Erreur extraction images : {e}")
    return images_dict

def analyser_odt(fichier_bytes):
    """Découpe le document ODT en bloc de recettes."""
    doc = opendocument.load(io.BytesIO(fichier_bytes))
    tous_les_p = doc.getElementsByType(text.P)
    lignes = [teletype.get_string(p) for p in tous_les_p if teletype.get_string(p).strip()]
    
    # Extraction des images compressées
    bibliotheque_images = extraire_images_du_zip(fichier_bytes)
    
    recettes = []
    bloc_actuel = []
    
    # Logique de découpe : une nouvelle recette commence quand on trouve "Ingrédients"
    # on considère que la ligne juste avant est le titre.
    for i, ligne in enumerate(lignes):
        if "Ingrédients" in ligne and i > 0:
            if bloc_actuel:
                # Le titre est la dernière ligne du bloc précédent
                titre = bloc_actuel.pop(-1)
                recettes.append({"titre": titre, "contenu": bloc_actuel})
            bloc_actuel = [ligne]
        else:
            bloc_actuel.append(ligne)
            
    # Ajouter la dernière recette
    if bloc_actuel:
        titre = bloc_actuel[0] # Simplification pour le dernier bloc
        recettes.append({"titre": titre, "contenu": bloc_actuel})

    # Structuration fine de chaque recette
    resultats = []
    for r in recettes:
        texte_complet = "\n".join(r['contenu'])
        
        # 1. Extraction Ingrédients
        ing_list = []
        m_ing = re.search(r"Ingrédients\s*:(.*?)(?=Préparation|$)", texte_complet, re.S | re.I)
        if m_ing:
            for line in m_ing.group(1).strip().split('\n'):
                # Tentative de séparation Quantité / Nom (ex: 180g de farine)
                m = re.match(r"(\d+\s*\w*)\s*(?:de|d')?\s*(.*)", line.strip())
                if m: ing_list.append({"Ingrédient": m.group(2).capitalize(), "Quantité": m.group(1)})
                else: ing_list.append({"Ingrédient": line.strip(), "Quantité": ""})

        # 2. Extraction Étapes
        etapes = ""
        m_etape = re.search(r"Préparation\s*:(.*)", texte_complet, re.S | re.I)
        if m_etape: etapes = m_etape.group(1).strip()

        # 3. Association Image (si un nom de fichier type DSCF est présent)
        image_flux = None
        for img_name, flux in bibliotheque_images.items():
            if img_name in texte_complet:
                image_flux = flux
                break

        resultats.append({
            "nom": r['titre'],
            "ingredients": ing_list,
            "etapes": etapes,
            "image_data": image_flux,
            "categorie": "Desserts" # Valeur par défaut
        })
    
    return resultats

def afficher():
    st.header("⚡ FlashImport ODT")
    
    # Initialisation des variables de session
    if 'import_idx' not in st.session_state: st.session_state.import_idx = 0
    if 'data_odt' not in st.session_state: st.session_state.data_odt = []

    file = st.file_uploader("Glisser le fichier .odt ici", type="odt")

    if file and not st.session_state.data_odt:
        with st.spinner("Analyse et compression des images en cours..."):
            st.session_state.data_odt = analyser_odt(file.read())
            st.rerun()

    if st.session_state.data_odt:
        idx = st.session_state.import_idx
        if idx < len(st.session_state.data_odt):
            recette = st.session_state.data_odt[idx]
            
            st.subheader(f"Recette {idx+1} / {len(st.session_state.data_odt)}")
            st.progress((idx + 1) / len(st.session_state.data_odt))

            # --- FORMULAIRE DE CONTRÔLE ---
            col_text, col_img = st.columns([2, 1])
            
            with col_text:
                nom = st.text_input("Nom de la recette", value=recette['nom'], key=f"n_{idx}")
                _, cats = get_index_options()
                cat = st.selectbox("Catégorie", options=cats, index=cats.index("Desserts") if "Desserts" in cats else 0)
                
                st.write("**Ingrédients :**")
                ing_df = st.data_editor(recette['ingredients'], num_rows="dynamic", use_container_width=True, key=f"ed_{idx}")
                
                etapes = st.text_area("Préparation", value=recette['etapes'], height=200, key=f"et_{idx}")

            with col_img:
                st.write("**Image détectée :**")
                if recette['image_data']:
                    st.image(recette['image_data'])
                else:
                    st.info("Aucune image trouvée pour cette recette.")

            # --- ACTIONS ---
            c1, c2, c3 = st.columns([1,1,1])
            
            if c1.button("⏭️ Passer"):
                st.session_state.import_idx += 1
                st.rerun()

            if c2.button("🗑️ Supprimer de la liste"):
                st.session_state.data_odt.pop(idx)
                st.rerun()

            if c3.button("✅ Valider & Enregistrer", type="primary"):
                with st.spinner("Envoi vers GitHub..."):
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    nom_fic = nom.lower().replace(" ", "_")
                    liste_medias = []

                    # Si image présente, on l'envoie (elle est déjà compressée)
                    if recette['image_data']:
                        ch_m = f"data/images/{ts}_{nom_fic}.jpg"
                        if envoyer_donnees_github(ch_m, recette['image_data'], "📸 Import ODT Photo", True):
                            liste_medias.append(ch_m)

                    # Envoi du JSON
                    ch_r = f"data/recettes/{ts}_{nom_fic}.json"
                    final_json = {
                        "nom": nom, "categorie": cat, "appareil": "Aucun",
                        "temps_preparation": "", "temps_cuisson": "",
                        "ingredients": ing_df, "etapes": etapes, "images": liste_medias
                    }
                    
                    if envoyer_donnees_github(ch_r, json.dumps(final_json, indent=4, ensure_ascii=False), f"📥 Import ODT: {nom}"):
                        mettre_a_jour_index({
                            "nom": nom, "categorie": cat, "appareil": "Aucun",
                            "ingredients": [i['Ingrédient'] for i in ing_df if i.get('Ingrédient')],
                            "chemin": ch_r
                        })
                        st.success("Enregistré !")
                        time.sleep(1)
                        st.session_state.import_idx += 1
                        st.rerun()
        else:
            st.balloons()
            st.success("Toutes les recettes ont été traitées ! 👩‍🍳")
            if st.button("Importer un autre fichier"):
                st.session_state.data_odt = []
                st.session_state.import_idx = 0
                st.rerun()
