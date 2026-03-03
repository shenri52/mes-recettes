import streamlit as st
import json
import base64
import requests
from datetime import datetime

# --- CONFIGURATION SÉCURISÉE (Via Streamlit Secrets) ---
try:
    token = st.secrets["GITHUB_TOKEN"]
    owner = st.secrets["REPO_OWNER"]
    repo = st.secrets["REPO_NAME"]
except Exception:
    st.error("⚠️ Configuration GitHub manquante dans les Secrets.")
    st.stop()

# --- FONCTION D'ENVOI GITHUB ---
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
        st.error(f"❌ Erreur GitHub ({res.status_code})")
        st.json(res.json())
        return False
    return True

# --- L'INTERFACE (TON STYLE) ---
def afficher():
    # Style CSS personnalisé (on remet tes polices et couleurs)
    st.markdown("""
        <style>
        .stTextInput > div > div > input { border-radius: 10px; }
        .stTextArea > div > div > textarea { border-radius: 10px; }
        .stButton > button { 
            border-radius: 20px; 
            background-color: #FF4B4B; 
            color: white;
            font-weight: bold;
            border: none;
        }
        h2 { color: #FF4B4B; font-family: 'Trebuchet MS'; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<h2>🍳 Saisir une Nouvelle Recette</h2>", unsafe_allow_html=True)

    # Formulaire principal
    nom_plat = st.text_input("Nom de la recette", placeholder="Le nom qui donne faim...")

    # Section Ingrédients
    st.markdown("### 🛒 Ingrédients")
    if 'ingredients_recette' not in st.session_state:
        st.session_state.ingredients_recette = []

    c1, c2 = st.columns([2, 1])
    with c1:
        ing = st.text_input("Ingrédient", key="ing_input")
    with c2:
        qte = st.text_input("Quantité", key="qte_input")

    if st.button("➕ Ajouter à la liste"):
        if ing:
            st.session_state.ingredients_recette.append({"Ingrédient": ing, "Quantité": qte})
            st.rerun()

    # Affichage de la liste d'ingrédients
    for i, item in enumerate(st.session_state.ingredients_recette):
        st.write(f"📍 {item['Quantité']} {item['Ingrédient']}")

    st.markdown("---")
    
    # Étapes et Photo
    etapes = st.text_area("📝 Étapes de préparation", placeholder="Décris la magie ici...", height=150)
    
    st.markdown("### 📸 Capture Facebook")
    photo_fb = st.file_uploader("Choisir la photo du plat", type=["jpg", "png", "jpeg"])

    # --- BOUTON DE SAUVEGARDE ---
    if st.button("💾 ENREGISTRER DANS MON CLOUD", use_container_width=True):
        if nom_plat and photo_fb:
            with st.spinner("Envoi vers ta base de données sécurisée..."):
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
                        st.success(f"🌟 '{nom_plat}' a bien été sauvegardé !")
                        st.balloons()
                        st.session_state.ingredients_recette = []
        else:
            st.warning("⚠️ N'oublie pas de mettre un nom et une photo !")
