import streamlit as st
import json
import base64
import requests
from datetime import datetime
import io
from PIL import Image

# 1. CONFIGURATION GITHUB
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

# 2. RÉCUPÉRATION DES INGRÉDIENTS (ANTI-CACHE)
def recuperer_ingredients_existants():
    conf = config_github()
    # On ajoute un timestamp à l'URL du dossier pour forcer GitHub à l'actualiser
    import time
    url = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/data/recettes?t={int(time.time())}"
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

# 3. ENVOI VERS GITHUB
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

# 4. AFFICHAGE DE LA PAGE
def afficher():
    st.header("...") # Votre titre actuel

    # Initialisation des ingrédients si absent
    if 'liste_choix' not in st.session_state:
        st.session_state.liste_choix = [""]

    # AJOUT D'UN BOUTON DE SYNCHRO (Optionnel mais recommandé)
    # Ou forcez le chargement au premier affichage de la page
    if st.sidebar.button("🔄 Actualiser les ingrédients"):
        with st.spinner("Synchronisation..."):
            st.session_state.liste_choix = recuperer_ingredients_existants()
            st.rerun()

    # Si la liste est encore vide (premier lancement), on la charge
    if len(st.session_state.liste_choix) <= 1:
        st.session_state.liste_choix = recuperer_ingredients_existants()

    # --- FORMULAIRE ---
    with st.container():
        nom_plat = st.text_input("Nom de la recette", key=f"nom_{st.session_state.form_count}")
        
        type_appareil = st.selectbox(
            "Appareil utilisé", 
            options=["Aucun", "Cookeo", "Thermomix", "Ninja"], 
            key=f"appareil_{st.session_state.form_count}"
        )

        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            options = st.session_state.liste_choix + ["➕ Ajouter un nouveau..."]
            choix = st.selectbox("Choisir l'ingrédient", options=options, key=f"sel_{st.session_state.form_count}")
            ing_final = st.text_input("Nom du nouvel ingrédient", key=f"new_ing_{st.session_state.form_count}") if choix == "➕ Ajouter un nouveau..." else choix

        with col2:
            qte = st.text_input("Quantité", key=f"qte_{st.session_state.form_count}")

        with col3:
            st.write(" ")
            st.write(" ")
            if st.button("Ajouter", key=f"add_{st.session_state.form_count}"):
                if ing_final:
                    st.session_state.ingredients_recette.append({"Ingrédient": ing_final, "Quantité": qte})
                    if ing_final not in st.session_state.liste_choix:
                        st.session_state.liste_choix.append(ing_final)
                    st.rerun()

        for i in st.session_state.ingredients_recette:
            st.write(f"✅ {i['Quantité']} {i['Ingrédient']}")

        st.markdown("---")
        etapes = st.text_area("Étapes de préparation", height=150, key=f"etapes_{st.session_state.form_count}")
        photos_fb = st.file_uploader("Images ou PDF", type=["jpg", "png", "jpeg", "pdf"], key=f"photo_{st.session_state.form_count}", accept_multiple_files=True)

    # --- SAUVEGARDE ---
    if st.button("💾 Enregistrer la recette", use_container_width=True):
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
                        "ingredients": st.session_state.ingredients_recette, 
                        "etapes": etapes, 
                        "images": liste_medias
                    }
                    chemin_json = f"data/recettes/{timestamp}_{nom_fic}.json"
                    if envoyer_vers_github(chemin_json, json.dumps(data, indent=4, ensure_ascii=False), "Data"):
                        st.success("Enregistré sur GitHub !")
                        st.session_state.ingredients_recette = []
                        st.session_state.form_count += 1 
                        st.rerun()
        else:
            st.warning("Le nom de la recette est obligatoire.")
