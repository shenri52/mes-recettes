import streamlit as st
import json
import base64
import requests
from datetime import datetime

# --- FONCTION D'ENVOI GITHUB (INVISIBILE) ---
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
    st.header("Ajouter une recette")

    # Initialisation des listes en mémoire
    if 'ingredients_recette' not in st.session_state:
        st.session_state.ingredients_recette = []
    
    if 'liste_choix' not in st.session_state:
        st.session_state.liste_choix = ["", "Farine", "Sucre", "Œuf", "Lait", "Beurre", "Chocolat"]

    nom_plat = st.text_input("Nom de la recette")

    # --- LIGNE D'AJOUT D'INGRÉDIENTS ---
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        options = st.session_state.liste_choix + ["➕ Ajouter un nouveau..."]
        choix = st.selectbox("Choisir l'ingrédient", options=options)
        
        ing_final = ""
        if choix == "➕ Ajouter un nouveau...":
            ing_final = st.text_input("Nom du nouvel ingrédient")
        else:
            ing_final = choix

    with col2:
        qte = st.text_input("Quantité")

    with col3:
        st.write(" ") 
        st.write(" ") 
        if st.button("Ajouter"):
            if ing_final:
                st.session_state.ingredients_recette.append({"Ingrédient": ing_final, "Quantité": qte})
                if ing_final not in st.session_state.liste_choix:
                    st.session_state.liste_choix.append(ing_final)
                st.rerun()

    if st.session_state.ingredients_recette:
        for i in st.session_state.ingredients_recette:
            st.write(f"✅ {i['Quantité']} {i['Ingrédient']}")

    st.markdown("---")
    etapes = st.text_area("Étapes de préparation", height=150)
    photo_fb = st.file_uploader("Capture Facebook", type=["jpg", "png", "jpeg"])

    # --- BOUTON DE SAUVEGARDE AVEC EMOJI ---
    if st.button("💾 Enregistrer la recette", use_container_width=True):
        if nom_plat: # Seul le nom est obligatoire maintenant
            with st.spinner("Enregistrement..."):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                nom_fic = nom_plat.replace(" ", "_").lower()
                chemin_img = ""

                # Envoi de l'image seulement si elle existe
                img_ok = True
                if photo_fb:
                    chemin_img = f"data/images/{timestamp}_{nom_fic}.png"
                    img_ok = envoyer_vers_github(chemin_img, photo_fb.getvalue(), "Photo", est_binaire=True)

                if img_ok:
                    data = {
                        "nom": nom_plat, 
                        "ingredients": st.session_state.ingredients_recette, 
                        "etapes": etapes, 
                        "image": chemin_img
                    }
                    chemin_json = f"data/recettes/{timestamp}_{nom_fic}.json"
                    if envoyer_vers_github(chemin_json, json.dumps(data, indent=4, ensure_ascii=False), "Data"):
                        st.success("Enregistré sur GitHub !")
                        st.session_state.ingredients_recette = []
                        st.rerun()
        else:
            st.warning("Complète au moins le nom de la recette.")
