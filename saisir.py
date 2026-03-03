import streamlit as st
import json
import base64
import requests
from datetime import datetime
import io
from PIL import Image

# --- FONCTION D'ENVOI GITHUB (INVISIBLE) ---
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
    st.header("✍️ Ajouter une recette")

    # Initialisation pour la remise à zéro automatique
    if 'form_count' not in st.session_state:
        st.session_state.form_count = 0

    # Initialisation des listes en mémoire
    if 'ingredients_recette' not in st.session_state:
        st.session_state.ingredients_recette = []
    
    if 'liste_choix' not in st.session_state:
        st.session_state.liste_choix = [""]

    # On utilise un conteneur avec une clé unique pour tout vider d'un coup
    with st.container():
        nom_plat = st.text_input("Nom de la recette", key=f"nom_{st.session_state.form_count}")
        
        # --- CHOIX DE L'APPAREIL SOUS LE NOM ---
        type_appareil = st.selectbox(
            "Appareil utilisé", 
            options=["Aucun", "Cookeo", "Thermomix", "Ninja"], 
            key=f"appareil_{st.session_state.form_count}"
        )

        # --- LIGNE D'AJOUT D'INGRÉDIENTS ---
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            options = st.session_state.liste_choix + ["➕ Ajouter un nouveau..."]
            choix = st.selectbox("Choisir l'ingrédient", options=options, key=f"sel_{st.session_state.form_count}")
            
            ing_final = ""
            if choix == "➕ Ajouter un nouveau...":
                ing_final = st.text_input("Nom du nouvel ingrédient", key=f"new_ing_{st.session_state.form_count}")
            else:
                ing_final = choix

        with col2:
            qte = st.text_input("Quantité", key=f"qte_{st.session_state.form_count}")

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
        etapes = st.text_area("Étapes de préparation", height=150, key=f"etapes_{st.session_state.form_count}")
        photos_fb = st.file_uploader("Images ou PDF (plusieurs possibles)", type=["jpg", "png", "jpeg", "pdf"], key=f"photo_{st.session_state.form_count}", accept_multiple_files=True)

    # --- BOUTON DE SAUVEGARDE ---
    if st.button("💾 Enregistrer la recette", use_container_width=True):
        if nom_plat:
            with st.spinner("Enregistrement..."):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                nom_fic = nom_plat.replace(" ", "_").lower()
                chemin_img = ""
                img_ok = True  # Correction de l'indentation ici

                if photo_fb:
                    nom_fichier_origine = photo_fb.name.lower()
                    extension = nom_fichier_origine.split('.')[-1]
                    chemin_img = f"data/images/{timestamp}_{nom_fic}.{extension}"
                    
                    if extension in ["jpg", "jpeg", "png"]:
                        # --- COMPRESSION IMAGE SANS PERTE VISIBLE ---
                        image = Image.open(photo_fb)
                        # Conversion en RGB si nécessaire (pour éviter les erreurs avec les JPEG)
                        if image.mode in ("RGBA", "P"):
                            image = image.convert("RGB")
                        
                        buffer = io.BytesIO()
                        if extension == "png":
                            image.save(buffer, format="PNG", optimize=True)
                        else:
                            image.save(buffer, format="JPEG", quality=85, optimize=True)
                        
                        contenu_a_envoyer = buffer.getvalue()
                    else:
                        # --- PDF : ON GARDE LE FICHIER TEL QUEL ---
                        contenu_a_envoyer = photo_fb.getvalue()
                    
                    img_ok = envoyer_vers_github(chemin_img, contenu_a_envoyer, "Document recette", est_binaire=True)

                if img_ok:
                    data = {
                        "nom": nom_plat, 
                        "appareil": type_appareil,
                        "ingredients": st.session_state.ingredients_recette, 
                        "etapes": etapes, 
                        "image": chemin_img
                    }
                    chemin_json = f"data/recettes/{timestamp}_{nom_fic}.json"
                    if envoyer_vers_github(chemin_json, json.dumps(data, indent=4, ensure_ascii=False), "Data"):
                        st.success("Enregistré sur GitHub !")
                        
                        # --- RÉINITIALISATION ---
                        st.session_state.ingredients_recette = []
                        st.session_state.form_count += 1 
                        st.rerun()
        else:
            st.warning("Complète au moins le nom de la recette.")
