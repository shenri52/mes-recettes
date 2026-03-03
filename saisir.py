import streamlit as st
import json
import base64
import requests
from datetime import datetime

# --- CONFIGURATION SÉCURISÉE ---
try:
    token = st.secrets["GITHUB_TOKEN"]
    owner = st.secrets["REPO_OWNER"]
    repo = st.secrets["REPO_NAME"]
except Exception:
    st.error("Configuration Secrets manquante.")
    st.stop()

def envoyer_vers_github(chemin_fichier, contenu, message, est_binaire=False):
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{chemin_fichier}"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    if est_binaire:
        contenu_final = base64.b64encode(contenu).decode('utf-8')
    else:
        contenu_final = base64.b64encode(contenu.encode('utf-8')).decode('utf-8')
    data = {"message": message, "content": contenu_final, "branch": "main"}
    res = requests.put(url, headers=headers, json=data)
    if res.status_code not in [200, 201]:
        st.error(f"Erreur technique : {res.status_code}")
        st.json(res.json())
        return False
    return True

def afficher():
    # --- TON STYLE INITIAL ---
    st.markdown("""
        <style>
        /* On enlève les couleurs rouges imposées */
        .stButton > button { 
            border-radius: 5px;
            font-weight: normal;
        }
        h2 { font-family: sans-serif; color: #31333F; }
        </style>
    """, unsafe_allow_html=True)

    st.header("Ajouter une nouvelle recette")

    # Formulaire
    nom_plat = st.text_input("Nom de la recette")

    if 'ingredients_recette' not in st.session_state:
        st.session_state.ingredients_recette = []

    col1, col2 = st.columns([2, 1])
    with col1:
        ing = st.text_input("Ingrédient")
    with col2:
        qte = st.text_input("Quantité")

    if st.button("Ajouter l'ingrédient"):
        if ing:
            st.session_state.ingredients_recette.append({"Ingrédient": ing, "Quantité": qte})

    # Liste des ingrédients
    for i in st.session_state.ingredients_recette:
        st.write(f"• {i['Quantité']} {i['Ingrédient']}")

    etapes = st.text_area("Étapes", height=150)
    photo_fb = st.file_uploader("Capture Facebook", type=["jpg", "png", "jpeg"])

    # Bouton Enregistrer
    if st.button("Enregistrer la recette", use_container_width=True):
        if nom_plat and photo_fb:
            with st.spinner("Enregistrement..."):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                nom_fic = nom_plat.replace(" ", "_").lower()

                # 1. Image
                ext = photo_fb.name.split('.')[-1]
                chemin_img = f"data/images/{timestamp}_{nom_fic}.{ext}"
                img_ok = envoyer_vers_github(chemin_img, photo_fb.getvalue(), f"Photo {nom_plat}", est_binaire=True)

                # 2. JSON
                if img_ok:
                    data_recette = {
                        "nom": nom_plat,
                        "ingredients": st.session_state.ingredients_recette,
                        "etapes": etapes,
                        "image_path": chemin_img,
                        "date": timestamp
                    }
                    chemin_json = f"data/recettes/{timestamp}_{nom_fic}.json"
                    json_ok = envoyer_vers_github(chemin_json, json.dumps(data_recette, indent=4, ensure_ascii=False), f"Data {nom_plat}")
                    
                    if json_ok:
                        st.success("C'est enregistré !")
                        st.session_state.ingredients_recette = []
        else:
            st.warning("Complète le nom et la photo.")
