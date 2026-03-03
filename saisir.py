import streamlit as st
import json
import base64
import requests
from datetime import datetime

# --- 1. CONFIGURATION RÉCUPÉRÉE DE STREAMLIT SECRETS ---
try:
    token = st.secrets["GITHUB_TOKEN"]
    owner = st.secrets["REPO_OWNER"]
    repo = st.secrets["REPO_NAME"]
except Exception as e:
    st.error("⚠️ Les Secrets GitHub ne sont pas configurés dans Streamlit Cloud.")
    st.stop()

# --- 2. FONCTION D'ENVOI VERS GITHUB ---
def envoyer_vers_github(chemin_fichier, contenu, message, est_binaire=False):
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{chemin_fichier}"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    
    # Encodage
    if est_binaire:
        contenu_final = base64.b64encode(contenu).decode('utf-8')
    else:
        contenu_final = base64.b64encode(contenu.encode('utf-8')).decode('utf-8')
    
    data = {"message": message, "content": contenu_final, "branch": "main"}
    
    res = requests.put(url, headers=headers, json=data)
    
    if res.status_code not in [200, 201]:
        st.error(f"❌ Erreur GitHub ({res.status_code})")
        st.json(res.json()) # Affiche l'erreur précise si ça rate
        return False
    return True

# --- 3. L'INTERFACE DE SAISIE ---
def afficher():
    st.header("📝 Saisir une nouvelle recette Facebook")

    # Champs de texte
    nom_plat = st.text_input("Nom du plat", placeholder="Ex: Gratin de courgettes")
    
    # Gestion des ingrédients (on garde ta logique de session_state)
    if 'ingredients_recette' not in st.session_state:
        st.session_state.ingredients_recette = []

    col1, col2 = st.columns([2, 1])
    with col1:
        ing = st.text_input("Ingrédient")
    with col2:
        qte = st.text_input("Quantité")
    
    if st.button("➕ Ajouter l'ingrédient"):
        if ing:
            st.session_state.ingredients_recette.append({"Ingrédient": ing, "Quantité": qte})

    # Affichage de la liste actuelle
    if st.session_state.ingredients_recette:
        st.write("🛒 **Liste actuelle :**")
        for i in st.session_state.ingredients_recette:
            st.write(f"- {i['Quantité']} {i['Ingrédient']}")

    etapes = st.text_area("Étapes de préparation", height=150)
    
    # Capture Facebook
    photo_fb = st.file_uploader("📸 Capture d'écran Facebook (Image)", type=["jpg", "png", "jpeg"])

    # --- BOUTON ENREGISTRER ---
    if st.button("💾 SAUVEGARDER DANS MA BASE CLOUD", use_container_width=True):
        if not nom_plat or not photo_fb:
            st.warning("⚠️ Il manque le nom ou la photo !")
        else:
            with st.spinner("Envoi en cours vers GitHub..."):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                nom_fic = nom_plat.replace(" ", "_").lower()

                # A. Envoi de l'image
                chemin_img = f"data/images/{timestamp}_{nom_fic}.png"
                img_ok = envoyer_vers_github(chemin_img, photo_fb.getvalue(), f"Photo: {nom_plat}", est_binaire=True)

                # B. Envoi des données JSON
                if img_ok:
                    data_recette = {
                        "nom": nom_plat,
                        "ingredients": st.session_state.ingredients_recette,
                        "etapes": etapes,
                        "image_path": chemin_img,
                        "date": timestamp
                    }
                    chemin_json = f"data/recettes/{timestamp}_{nom_fic}.json"
                    json_ok = envoyer_vers_github(chemin_json, json.dumps(data_recette, indent=4, ensure_ascii=False), f"Data: {nom_plat}")
                    
                    if json_ok:
                        st.success(f"✅ '{nom_plat}' a bien été ajouté à ta base !")
                        st.balloons()
                        # On vide la liste pour la prochaine fois
                        st.session_state.ingredients_recette = []
