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

    # Initialisation des listes en mémoire
    if 'ingredients_recette' not in st.session_state:
        st.session_state.ingredients_recette = []
    
    if 'liste_choix' not in st.session_state:
        st.session_state.liste_choix = ["", "Farine", "Sucre", "Œuf", "Lait", "Beurre", "Chocolat"]

    # Utilisation de clés (key) pour pouvoir réinitialiser les champs
    nom_plat = st.text_input("Nom de la recette", key="nom_recette_input")

    # --- LIGNE D'AJOUT D'INGRÉDIENTS ---
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        options = st.session_state.liste_choix + ["➕ Ajouter un nouveau..."]
        choix = st.selectbox("Choisir l'ingrédient", options=options, key="sel_ing")
        
        ing_final = ""
        if choix == "➕ Ajouter un nouveau...":
            ing_final = st.text_input("Nom du nouvel ingrédient", key="new_ing_name")
        else:
            ing_final = choix

    with col2:
        qte = st.text_input("Quantité", key="qte_input")

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
    etapes = st.text_area("Étapes de préparation", height=150, key="etapes_input")
    photo_fb = st.file_uploader("Capture Facebook", type=["jpg", "png", "jpeg"], key="photo_input")

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
                        
                        # --- REMISE À ZÉRO DES CHAMPS ---
                        st.session_state.ingredients_recette = []
                        # On vide les champs via les clés
                        for key in ["nom_recette_input", "etapes_input", "qte_input", "new_ing_name"]:
                            if key in st.session_state:
                                st.session_state[key] = ""
                        st.rerun() # Relance pour vider l'affichage
        else:
            st.warning("Complète le nom et la photo.")
