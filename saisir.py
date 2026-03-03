import streamlit as st
import json
import base64
import requests
from datetime import datetime

# --- CONFIGURATION GITHUB ---
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO_OWNER = st.secrets["REPO_OWNER"]
REPO_NAME = st.secrets["REPO_NAME"]
BRANCH = "main"

def save_to_github(file_path, file_content, message, is_binary=False):
    """Fonction magique pour envoyer un fichier vers ton dossier /data"""
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{file_path}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # On encode le contenu en Base64 (obligatoire pour l'API GitHub)
    if is_binary:
        content_encoded = base64.b64encode(file_content).decode('utf-8')
    else:
        content_encoded = base64.b64encode(file_content.encode('utf-8')).decode('utf-8')
        
    data = {
        "message": message,
        "content": content_encoded,
        "branch": BRANCH
    }

    # On tente d'envoyer le fichier
    res = requests.put(url, headers=headers, json=data)

    if res.status_code not in [200, 201]:
        st.error(f"Erreur GitHub {res.status_code}")
        st.json(res.json()) # Cela va afficher l'erreur précise envoyée par GitHub
        
    return res.status_code

def afficher():
    st.markdown("<h2 style='text-align: center;'>📸 Ajouter une Recette Facebook</h2>", unsafe_allow_html=True)

    # --- FORMULAIRE ---
    nom_plat = st.text_input("Nom de la recette", placeholder="Ex: Gratin Dauphinois de Facebook")
    
    # On initialise la liste des ingrédients si elle n'existe pas
    if 'ingredients_recette' not in st.session_state:
        st.session_state.ingredients_recette = []

    # (Ici tu peux garder ton bloc d'ajout d'ingrédients habituel)
    
    # --- CAPTURE FACEBOOK ---
    fichiers = st.file_uploader("Upload la capture d'écran ou le PDF", type=["jpg", "png", "pdf"])

    if st.button("🚀 Enregistrer durablement sur GitHub", use_container_width=True):
        if nom_plat and fichiers:
            with st.spinner("Envoi vers ta base de données..."):
                # Générer un nom unique avec la date et l'heure
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                nom_nettoye = nom_plat.replace(" ", "_").lower()
                
                # 1. Enregistrer l'IMAGE dans /data/images/
                ext = fichiers.name.split('.')[-1]
                chemin_image = f"data/images/{timestamp}_{nom_nettoye}.{ext}"
                img_res = save_to_github(chemin_image, fichiers.getvalue(), f"Ajout photo {nom_plat}", is_binary=True)
                
                # 2. Enregistrer le TEXTE dans /data/recettes/
                chemin_json = f"data/recettes/{timestamp}_{nom_nettoye}.json"
                recette_dict = {
                    "nom": nom_plat,
                    "date": timestamp,
                    "image_url": chemin_image,
                    "ingredients": st.session_state.ingredients_recette
                }
                json_res = save_to_github(chemin_json, json.dumps(recette_dict, indent=4, ensure_ascii=False), f"Ajout data {nom_plat}")

                if img_res in [200, 201] and json_res in [200, 201]:
                    st.success(f"✅ Génial ! '{nom_plat}' est maintenant dans ton dossier /data !")
                    st.balloons()
                else:
                    st.error(f"Zut, erreur GitHub. Code image: {img_res}, Code JSON: {json_res}")
        else:
            st.warning("Pense à mettre un nom et une image !")
