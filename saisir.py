import streamlit as st
import json
import base64
import requests
from datetime import datetime

# --- CONFIGURATION CACHÉE ---
def envoyer_vers_github(chemin_fichier, contenu, message, est_binaire=False):
    try:
        token = st.secrets["GITHUB_TOKEN"]
        owner = st.secrets["REPO_OWNER"]
        repo = st.secrets["REPO_NAME"]
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{chemin_fichier}"
        headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
        
        if est_binaire:
            contenu_final = base64.b64encode(contenu).decode('utf-8')
        else:
            contenu_final = base64.b64encode(contenu.encode('utf-8')).decode('utf-8')
        
        data = {"message": message, "content": contenu_final, "branch": "main"}
        res = requests.put(url, headers=headers, json=data)
        return res.status_code in [200, 201]
    except:
        return False

def afficher():
    st.header("Saisir une nouvelle recette")

    # 1. Nom du plat
    nom_plat = st.text_input("Nom de la recette")

    # 2. Ingrédients sur LA MÊME LIGNE
    if 'ingredients_recette' not in st.session_state:
        st.session_state.ingredients_recette = []

    # On utilise 3 colonnes pour que l'ingrédient, la quantité et le bouton soient alignés
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        ing = st.text_input("Ingrédient", key="new_ing")
    with col2:
        qte = st.text_input("Quantité", key="new_qte")
    with col3:
        st.write(" ") # Petit décalage pour aligner le bouton avec les champs
        if st.button("➕ Ajouter"):
            if ing:
                st.session_state.ingredients_recette.append({"Ingrédient": ing, "Quantité": qte})
                st.rerun()

    # Affichage de la liste (ta liste déroulante/liste simple)
    if st.session_state.ingredients_recette:
        for i in st.session_state.ingredients_recette:
            st.write(f"• {i['Quantité']} {i['Ingrédient']}")

    # 3. Étapes
    etapes = st.text_area("Étapes de préparation", height=150)
    
    # 4. Photo Facebook
    photo_fb = st.file_uploader("Capture Facebook", type=["jpg", "png", "jpeg"])

    # 5. Bouton Enregistrer
    if st.button("Enregistrer la recette", use_container_width=True):
        if nom_plat and photo_fb:
            with st.spinner("Enregistrement en cours..."):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                nom_fic = nom_plat.replace(" ", "_").lower()

                # Envoi Image
                chemin_img = f"data/images/{timestamp}_{nom_fic}.png"
                img_ok = envoyer_vers_github(chemin_img, photo_fb.getvalue(), "Photo", est_binaire=True)

                # Envoi JSON
                if img_ok:
                    data = {"nom": nom_plat, "ingredients": st.session_state.ingredients_recette, "etapes": etapes, "image": chemin_img}
                    chemin_json = f"data/recettes/{timestamp}_{nom_fic}.json"
                    if envoyer_vers_github(chemin_json, json.dumps(data, indent=4), "Data"):
                        st.success("C'est enregistré sur GitHub !")
                        st.session_state.ingredients_recette = []
        else:
            st.warning("Veuillez remplir le nom et ajouter une photo.")
