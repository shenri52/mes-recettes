import streamlit as st
import json
import base64
import requests
from datetime import datetime
import io
from PIL import Image
import time

# 1. LA CONFIGURATION (DOIT ÊTRE EN HAUT)
def config_github():
    return {
        "token": st.secrets["GITHUB_TOKEN"],
        "owner": st.secrets["REPO_OWNER"],
        "repo": st.secrets["REPO_NAME"],
        "headers": {
            "Authorization": f"token {st.secrets['GITHUB_TOKEN']}",
            "Accept": "application/vnd.github.v3+json"
        }
    }

# 2. LA RÉCUPÉRATION DES INGRÉDIENTS (ANTI-CACHE)
def recuperer_ingredients_existants():
    conf = config_github()
    # On ajoute un timestamp à l'URL du dossier pour forcer GitHub à l'actualiser
    url = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/data/recettes?t={int(time.time())}"
    try:
        res = requests.get(url, headers=conf['headers'])
        ingredients_trouves = [""]
        
        if res.status_code == 200:
            fichiers = res.json()
            for f in fichiers:
                if f['name'].endswith('.json'):
                    # On utilise le SHA pour lire le contenu réel sans cache
                    r_res = requests.get(f"{f['download_url']}?v={f['sha']}")
                    if r_res.status_code == 200:
                        data = r_res.json()
                        for ing in data.get('ingredients', []):
                            nom = ing.get('Ingrédient')
                            if nom and nom not in ingredients_trouves:
                                ingredients_trouves.append(nom)
        return sorted(list(set(ingredients_trouves)))
    except:
        return [""]

# 3. L'ENVOI VERS GITHUB
def envoyer_vers_github(chemin_fichier, contenu, message, est_binaire=False):
    try:
        conf = config_github()
        url = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/{chemin_fichier}"
        if est_binaire:
            contenu_final = base64.b64encode(contenu).decode('utf-8')
        else:
            contenu_final = base64.b64encode(contenu.encode('utf-8')).decode('utf-8')
        
        data = {"message": message, "content": contenu_final, "branch": "main"}
        res = requests.put(url, headers=conf['headers'], json=data)
        return res.status_code in [200, 201]
    except:
        return False

# 4. L'AFFICHAGE DE LA PAGE
def afficher():
    st.header("📸 Importer photo")

    # --- INITIALISATION DES VARIABLES (SÉCURITÉ) ---
    if 'form_count_img' not in st.session_state:
        st.session_state.form_count_img = 0
    if 'ingredients_img' not in st.session_state:
        st.session_state.ingredients_img = []
    if 'liste_choix_img' not in st.session_state:
        st.session_state.liste_choix_img = [""]

    # --- SYNCHRONISATION INITIALE ---
    if len(st.session_state.liste_choix_img) <= 1:
        with st.spinner("📦 Synchronisation des ingrédients..."):
            st.session_state.liste_choix_img = recuperer_ingredients_existants()

    # --- FORMULAIRE ---
    with st.container():
        nom_plat = st.text_input("Nom de la recette", key=f"nom_img_{st.session_state.form_count_img}")
        
        type_appareil = st.selectbox(
            "Appareil utilisé", 
            options=["Aucun", "Cookeo", "Thermomix", "Ninja"], 
            key=f"app_img_{st.session_state.form_count_img}"
        )

        col1, col3 = st.columns([3, 1])
        with col1:
            options = st.session_state.liste_choix_img + ["➕ Ajouter un nouveau..."]
            choix = st.selectbox("Choisir l'ingrédient", options=options, key=f"sel_img_{st.session_state.form_count_img}")
            ing_final = st.text_input("Nom du nouvel ingrédient", key=f"new_ing_img_{st.session_state.form_count_img}") if choix == "➕ Ajouter un nouveau..." else choix

        with col3:
            st.write(" ")
            st.write(" ")
            # Sous-colonnes pour aligner les deux boutons sur la même ligne
            btn_col_add, btn_col_ref = st.columns([1, 1])
            with btn_col_add:
                if st.button("Ajouter", key=f"btn_add_img_{st.session_state.form_count_img}"):
                    if ing_final:
                        st.session_state.ingredients_img.append({"Ingrédient": ing_final, "Quantité": ""})
                        if ing_final not in st.session_state.liste_choix_img:
                            st.session_state.liste_choix_img.append(ing_final)
                        st.rerun()
            with btn_col_ref:
                if st.button("🔄", key=f"btn_ref_img_{st.session_state.form_count_img}", help="Actualiser"):
                    st.session_state.liste_choix_img = recuperer_ingredients_existants()
                    st.rerun()

        for i in st.session_state.ingredients_img:
            st.write(f"✅ {i['Ingrédient']}")

        st.markdown("---")
        photos_fb = st.file_uploader("Images ou PDF", type=["jpg", "png", "jpeg", "pdf"], key=f"file_img_{st.session_state.form_count_img}", accept_multiple_files=True)

    # --- SAUVEGARDE ---
    if st.button("💾 Enregistrer la recette photo", use_container_width=True):
        if nom_plat:
            with st.spinner("Enregistrement..."):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                nom_fic = nom_plat.replace(" ", "_").lower()
                
                liste_medias = []
                img_ok = True

                if photos_fb:
                    for idx, fichier in enumerate(photos_fb):
                        ext = fichier.name.lower().split('.')[-1]
                        chemin_media = f"data/images/{timestamp}_{nom_fic}_{idx}.{ext}"
                        
                        if ext in ["jpg", "jpeg", "png"]:
                            image = Image.open(fichier)
                            if image.mode in ("RGBA", "P"): image = image.convert("RGB")
                            buffer = io.BytesIO()
                            if ext == "png": image.save(buffer, format="PNG", optimize=True)
                            else: image.save(buffer, format="JPEG", quality=85, optimize=True)
                            contenu = buffer.getvalue()
                        else:
                            contenu = fichier.getvalue()
                        
                        if envoyer_vers_github(chemin_media, contenu, f"Media {idx}", est_binaire=True):
                            liste_medias.append(chemin_media)
                        else:
                            img_ok = False

                if img_ok:
                    data = {
                        "nom": nom_plat, 
                        "appareil": type_appareil,
                        "ingredients": st.session_state.ingredients_img, 
                        "etapes": "Voir image/PDF joint", 
                        "images": liste_medias
                    }
                    chemin_json = f"data/recettes/{timestamp}_{nom_fic}.json"
                    if envoyer_vers_github(chemin_json, json.dumps(data_recette, indent=4, ensure_ascii=False), f"Ajout: {nom_recette}"):
                        st.success(f"Recette '{nom_recette}' importée !")
                        
                        # --- LA MODIFICATION ICI ---
                        # On vide simplement la liste pour forcer recettes.py à tout recharger
                        if 'toutes_recettes' in st.session_state:
                            del st.session_state.toutes_recettes
                        
                        # Reset des champs (selon votre demande précédente)
                        st.session_state.url_import = "" 
                        time.sleep(1)
                        st.rerun()
        else:
            st.warning("Le nom de la recette est obligatoire.")
