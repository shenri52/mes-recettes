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

def recuperer_donnees_index():
    conf = config_github()
    url = f"https://raw.githubusercontent.com/{conf['owner']}/{conf['repo']}/main/data/index_recettes.json?t={int(time.time())}"
    try:
        res = requests.get(url)
        ingredients = [""]
        categories = [""]
        if res.status_code == 200:
            index_data = res.json()
            for r in index_data:
                for ing in r.get('ingredients', []):
                    if ing and ing not in ingredients: ingredients.append(ing)
                cat = r.get('categorie')
                if cat and cat not in categories: categories.append(cat)
        return sorted(list(set(ingredients))), sorted(list(set(categories)))
    except:
        return [""], [""]

def envoyer_vers_github(chemin_fichier, contenu, message, est_binaire=False):
    conf = config_github()
    url = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/{chemin_fichier}"
    
    res_get = requests.get(url, headers=conf['headers'])
    sha = res_get.json().get('sha') if res_get.status_code == 200 else None
    
    if est_binaire:
        contenu_final = base64.b64encode(contenu).decode('utf-8')
    else:
        contenu_final = base64.b64encode(contenu.encode('utf-8')).decode('utf-8')
    
    data = {"message": message, "content": contenu_final, "branch": "main"}
    if sha: data["sha"] = sha
    
    res = requests.put(url, headers=conf['headers'], json=data)
    return res.status_code in [200, 201]

def afficher():
    st.header("✍️ Ajouter une recette")

    if 'form_count' not in st.session_state: st.session_state.form_count = 0
    if 'ingredients_recette' not in st.session_state: st.session_state.ingredients_recette = []
    if 'liste_choix' not in st.session_state: st.session_state.liste_choix = [""]
    if 'liste_categories' not in st.session_state: st.session_state.liste_categories = [""]
    if 'cat_fixee' not in st.session_state: st.session_state.cat_fixee = ""

    if len(st.session_state.liste_choix) <= 1:
        with st.spinner("📦 Synchronisation..."):
            st.session_state.liste_choix, st.session_state.liste_categories = recuperer_donnees_index()

    with st.container():
        nom_plat = st.text_input("Nom de la recette", key=f"nom_{st.session_state.form_count}")
        
        c_app, c_prep, c_cuis = st.columns(3)
        with c_app:
            options_app = sorted(["Aucun", "Cookeo", "Thermomix", "Ninja"])
            type_appareil = st.selectbox("Appareil utilisé", options=options_app, key=f"app_{st.session_state.form_count}")
        with c_prep:
            tps_prep = st.text_input("Temps préparation", key=f"prep_{st.session_state.form_count}", placeholder="ex: 15 min")
        with c_cuis:
            tps_cuis = st.text_input("Temps cuisson", key=f"cuis_{st.session_state.form_count}", placeholder="ex: 20 min")

        # --- SECTION CATÉGORIE ---
        col_cat, col_btn_cat = st.columns([2, 0.5])
        with col_cat:
            opts_cat = st.session_state.liste_categories + ["➕ Ajouter une nouvelle..."]
            choix_cat = st.selectbox("Catégorie", options=opts_cat, key=f"scat_{st.session_state.form_count}")
            cat_input = st.text_input("Nom nouvelle catégorie", key=f"ncat_{st.session_state.form_count}") if choix_cat == "➕ Ajouter une nouvelle..." else choix_cat
        with col_btn_cat:
            st.write(" ")
            st.write(" ")
            if st.button("Ajouter", key=f"bcat_{st.session_state.form_count}"):
                if cat_input:
                    st.session_state.cat_fixee = cat_input
                    if cat_input not in st.session_state.liste_categories: st.session_state.liste_categories.append(cat_input)
                    st.toast(f"Catégorie : {cat_input}")

        if st.session_state.cat_fixee:
            st.write(f"📂 Sélection : **{st.session_state.cat_fixee}**")

        # --- SECTION INGRÉDIENTS ---
        col_ing, col_qte, col_btn_add = st.columns([2, 1, 0.6])
        with col_ing:
            options = st.session_state.liste_choix + ["➕ Ajouter un nouveau..."]
            choix = st.selectbox("Ingrédient", options=options, key=f"sel_{st.session_state.form_count}")
            ing_final = st.text_input("Nom nouveau", key=f"new_ing_{st.session_state.form_count}") if choix == "➕ Ajouter un nouveau..." else choix
        with col_qte:
            qte = st.text_input("Quantité", key=f"qte_{st.session_state.form_count}")
        with col_btn_add:
            st.write(" ")
            st.write(" ")
            if st.button("Ajouter", key=f"btn_add_{st.session_state.form_count}"):
                if ing_final:
                    st.session_state.ingredients_recette.append({"Ingrédient": ing_final, "Quantité": qte})
                    if ing_final not in st.session_state.liste_choix: 
                        st.session_state.liste_choix.append(ing_final)
                    st.rerun()

        for i in st.session_state.ingredients_recette:
            st.write(f"✅ {i['Quantité']} {i['Ingrédient']}")

        st.markdown("---")
        etapes = st.text_area("Étapes", height=150, key=f"et_saisir_{st.session_state.form_count}")
        photos_fb = st.file_uploader("Médias", type=["jpg", "png", "jpeg", "pdf"], key=f"ph_{st.session_state.form_count}", accept_multiple_files=True)

    if st.button("💾 Enregistrer la recette", use_container_width=True):
        final_category = st.session_state.cat_fixee if st.session_state.cat_fixee else cat_input
        if nom_plat:
            with st.spinner("Enregistrement..."):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                nom_fic = nom_plat.replace(" ", "_").lower()
                liste_medias = []
                img_ok = True

                if photos_fb:
                    for idx, f in enumerate(photos_fb):
                        ext = f.name.lower().split('.')[-1]
                        chemin_media = f"data/images/{timestamp}_{nom_fic}_{idx}.{ext}"
                        if ext in ["jpg", "jpeg", "png"]:
                            image = Image.open(f)
                            if image.mode in ("RGBA", "P"): image = image.convert("RGB")
                            buf = io.BytesIO()
                            image.save(buf, format="JPEG", quality=85)
                            cnt = buf.getvalue()
                        else: cnt = f.getvalue()
                        
                        if envoyer_vers_github(chemin_media, cnt, f"Media {idx}", True):
                            liste_medias.append(chemin_media)
                        else: img_ok = False

                if img_ok:
                    chemin_json = f"data/recettes/{timestamp}_{nom_fic}.json"
                    data = {
                        "nom": nom_plat, 
                        "categorie": final_category,
                        "appareil": type_appareil, 
                        "temps_preparation": tps_prep,
                        "temps_cuisson": tps_cuis,
                        "ingredients": st.session_state.ingredients_recette, 
                        "etapes": etapes, 
                        "images": liste_medias
                    }
                    if envoyer_vers_github(chemin_json, json.dumps(data, indent=4, ensure_ascii=False), "Nouveau"):
                        # MAJ INDEX
                        conf = config_github()
                        url_idx = f"https://raw.githubusercontent.com/{conf['owner']}/{conf['repo']}/main/data/index_recettes.json"
                        res_idx = requests.get(url_idx)
                        index_data = res_idx.json() if res_idx.status_code == 200 else []
                        
                        index_data.append({
                            "nom": nom_plat,
                            "categorie": final_category,
                            "appareil": type_appareil,
                            "ingredients": [i['Ingrédient'] for i in st.session_state.ingredients_recette],
                            "chemin": chemin_json
                        })
                        envoyer_vers_github("data/index_recettes.json", json.dumps(index_data, indent=4, ensure_ascii=False), "MAJ Index")

                        st.success("Enregistré !")
                        st.session_state.ingredients_recette = []
                        st.session_state.cat_fixee = ""
                        if 'index_recettes' in st.session_state: del st.session_state.index_recettes
                        st.session_state.form_count += 1
                        st.rerun()
