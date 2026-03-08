import streamlit as st
import json
import base64
import requests
from datetime import datetime
import io
from PIL import Image
import time

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

def recuperer_ingredients_existants():
    conf = config_github()
    url = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/data/recettes?t={int(time.time())}"
    try:
        res = requests.get(url, headers=conf['headers'])
        ingredients_trouves = [""]
        if res.status_code == 200:
            fichiers = res.json()
            for f in fichiers:
                if f['name'].endswith('.json'):
                    r_res = requests.get(f"{f['download_url']}?v={f['sha']}")
                    if r_res.status_code == 200:
                        data = r_res.json()
                        for ing in data.get('ingredients', []):
                            nom = ing.get('Ingrédient')
                            if nom and nom not in ingredients_trouves: ingredients_trouves.append(nom)
        return sorted(list(set(ingredients_trouves)))
    except: return [""]

def envoyer_vers_github(chemin, contenu, message, binaire=False):
    conf = config_github()
    url = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/{chemin}"
    
    # Récupération du SHA pour permettre la mise à jour (nécessaire pour l'index)
    res_get = requests.get(url, headers=conf['headers'])
    sha = res_get.json().get('sha') if res_get.status_code == 200 else None
    
    cnt = base64.b64encode(contenu if binaire else contenu.encode('utf-8')).decode('utf-8')
    payload = {"message": message, "content": cnt, "branch": "main"}
    if sha: payload["sha"] = sha
    
    res = requests.put(url, headers=conf['headers'], json=payload)
    return res.status_code in [200, 201]

def afficher():
    st.header("📥 Importer une recette")

    if 'form_count_img' not in st.session_state: st.session_state.form_count_img = 0
    if 'ingredients_img' not in st.session_state: st.session_state.ingredients_img = []
    if 'liste_choix_img' not in st.session_state: st.session_state.liste_choix_img = [""]

    if len(st.session_state.liste_choix_img) <= 1:
        st.session_state.liste_choix_img = recuperer_ingredients_existants()

    with st.container():
        nom_plat = st.text_input("Nom de la recette", key=f"ni_{st.session_state.form_count_img}")
        
        c_app, c_prep, c_cuis = st.columns(3)
        with c_app:
            type_appareil = st.selectbox("Appareil", options=sorted(["Aucun", "Cookeo", "Thermomix", "Ninja"]), key=f"ai_{st.session_state.form_count_img}")
        with c_prep:
            tps_prep = st.text_input("Temps préparation", key=f"pri_{st.session_state.form_count_img}", placeholder="ex: 10 min")
        with c_cuis:
            tps_cuis = st.text_input("Temps cuisson", key=f"cui_{st.session_state.form_count_img}", placeholder="ex: 5 min")

        col_ing, col_btn_add = st.columns([2, 0.5])
        
        with col_ing:
            options = sorted(st.session_state.liste_choix_img) + ["➕ Ajouter un nouveau..."]
            choix = st.selectbox("Ingrédient", options=options, key=f"si_{st.session_state.form_count_img}")
            ing_final = st.text_input("Nom", key=f"nwi_{st.session_state.form_count_img}") if choix == "➕ Ajouter un nouveau..." else choix

        with col_btn_add:
            st.write(" ")
            st.write(" ")
            if st.button("Ajouter", key=f"bi_{st.session_state.form_count_img}"):
                if ing_final:
                    st.session_state.ingredients_img.append({"Ingrédient": ing_final, "Quantité": ""})
                    if ing_final not in st.session_state.liste_choix_img: st.session_state.liste_choix_img.append(ing_final)
                    st.rerun()

        for i in st.session_state.ingredients_img: st.write(f"✅ {i['Ingrédient']}")
        photos_fb = st.file_uploader("Fichiers", type=["jpg", "png", "jpeg", "pdf"], key=f"fi_{st.session_state.form_count_img}", accept_multiple_files=True)

    if st.button("💾 Enregistrer l'import", use_container_width=True):
        if nom_plat:
            with st.spinner("Enregistrement..."):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                nom_fic = nom_plat.replace(" ", "_").lower()
                liste_medias = []
                
                if photos_fb:
                    for idx, f in enumerate(photos_fb):
                        ext = f.name.lower().split('.')[-1]
                        ch = f"data/images/{timestamp}_{nom_fic}_{idx}.{ext}"
                        if envoyer_vers_github(ch, f.getvalue(), "Media", True):
                            liste_medias.append(ch)

                chemin_recette = f"data/recettes/{timestamp}_{nom_fic}.json"
                data = {
                    "nom": nom_plat, 
                    "appareil": type_appareil, 
                    "temps_preparation": tps_prep,
                    "temps_cuisson": tps_cuis,
                    "ingredients": st.session_state.ingredients_img, 
                    "etapes": "Voir image jointe", 
                    "images": liste_medias
                }
                
                # Enregistrement du fichier recette
                if envoyer_vers_github(chemin_recette, json.dumps(data, indent=4, ensure_ascii=False), "Import"):
                    
                    # --- MISE À JOUR DE L'INDEX ---
                    conf = config_github()
                    url_idx = f"https://raw.githubusercontent.com/{conf['owner']}/{conf['repo']}/main/data/index_recettes.json"
                    res_idx = requests.get(url_idx)
                    
                    index_data = res_idx.json() if res_idx.status_code == 200 else []
                    
                    index_data.append({
                        "nom": nom_plat,
                        "categorie": "Importé",
                        "appareil": type_appareil,
                        "ingredients": [i['Ingrédient'] for i in st.session_state.ingredients_img],
                        "chemin": chemin_recette
                    })
                    
                    envoyer_vers_github("data/index_recettes.json", json.dumps(index_data, indent=4, ensure_ascii=False), "MAJ Index")
                    # --- FIN MISE À JOUR INDEX ---

                    st.success("Importé !")
                    st.session_state.ingredients_img = []
                    if 'index_recettes' in st.session_state: del st.session_state.index_recettes
                    if 'toutes_recettes' in st.session_state: del st.session_state.toutes_recettes
                    st.session_state.form_count_img += 1
                    st.rerun()
