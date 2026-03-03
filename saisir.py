import streamlit as st
import json
import base64
import requests
from datetime import datetime

# --- FONCTION D'ENVOI GITHUB ---
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

    # 1. Initialisation des listes en mémoire
    if 'ingredients_recette' not in st.session_state:
        st.session_state.ingredients_recette = []
    
    # C'est ici qu'on gère la liste déroulante pour qu'elle mémorise les ajouts
    if 'liste_choix' not in st.session_state:
        st.session_state.liste_choix = ["", "Farine", "Sucre", "Œuf", "Lait", "Beurre", "Chocolat"]

    nom_plat = st.text_input("Nom de la recette")

    # --- LIGNE D'AJOUT D'INGRÉDIENTS ---
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        # On ajoute l'option d'ajout à la fin de la liste mémorisée
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
                # 1. On ajoute à la recette en cours
                st.session_state.ingredients_recette.append({"Ingrédient": ing_final, "Quantité": qte})
                
                # 2. SI c'est un nouvel ingrédient, on l'ajoute à la liste déroulante pour après
                if ing_final not in st.session_state.liste_choix:
                    st.session_state.liste_choix.append(ing_final)
                
                st.rerun()

    # Affichage de la liste actuelle
    if st.session_state.ingredients_recette:
        for i in st.session_state.ingredients_recette:
            st.write(f"✅ {i['Quantité']} {i['Ingrédient']}")

    st.markdown("---")
    etapes = st.text_area("Étapes de préparation", height=150)
    photo_fb = st.file_uploader("Capture Facebook", type=["jpg", "png", "jpeg"])

    if st.button("Enregistrer la recette", use_container_width=True):
        if nom_plat and photo_fb:
            with st.spinner("Enregistrement..."):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                nom_fic = nom_plat.replace(" ", "_").lower()

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
        else:
            st.warning("Complète le nom et la photo.")
