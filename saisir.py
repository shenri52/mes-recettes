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
                            if nom and nom not in ingredients_trouves:
                                ingredients_trouves.append(nom)
        return sorted(list(set(ingredients_trouves)))
    except:
        return [""]

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

def afficher():
    st.header("✍️ Ajouter une recette")

    if 'form_count' not in st.session_state: st.session_state.form_count = 0
    if 'ingredients_recette' not in st.session_state: st.session_state.ingredients_recette = []
    if 'liste_choix' not in st.session_state: st.session_state.liste_choix = [""]

    if len(st.session_state.liste_choix) <= 1:
        with st.spinner("📦 Synchronisation..."):
            st.session_state.liste_choix = recuperer_ingredients_existants()

    with st.container():
        nom_plat = st.text_input("Nom de la recette", key=f"nom_{st.session_state.form_count}")
        
        c_app, c_prep, c_cuis = st.columns(3)
        with c_app:
            # Modification : Appareils classés par ordre alphabétique
            options_app = sorted(["Aucun", "Cookeo", "Thermomix", "Ninja"])
            type_appareil = st.selectbox("Appareil utilisé", options=options_app, key=f"app_{st.session_state.form_count}")
        with c_prep:
            tps_prep = st.text_input("Temps préparation", key=f"prep_{st.session_state.form_count}", placeholder="ex: 15 min")
        with c_cuis:
            tps_cuis = st.text_input("Temps cuisson", key=f"cuis_{st.session_state.form_count}", placeholder="ex: 20 min")

        col_ing, col_qte, col_btn_add, col_btn_ref = st.columns([2, 1, 0.6, 0.4])
        
        with col_ing:
            # Modification : "Ajouter un nouveau" en haut de la liste
            options = ["➕ Ajouter un nouveau..."] + [i for i in st.session_state.liste_choix if i]
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
                        st.session_state.liste_choix.sort() # Maintien de l'ordre alphabétique
                    st.rerun()

        with col_btn_ref:
            st.write(" ")
            st.write(" ")
            if st.button("🔄", key=f"btn_ref_{st.session_state.form_count}"):
                st.session_state.liste_choix = recuperer_ingredients_existants()
                st.rerun()

        # Modification : Liste des ingrédients ajoutés classée par ordre alphabétique
        ingredients_tries = sorted(st.session_state.ingredients_recette, key=lambda x: x['Ingrédient'].lower())
        for i in ingredients_tries:
            st.write(f"✅ {i['Quantité']} {i['Ingrédient']}")

        st.markdown("---")
        etapes = st.text_area("Étapes", height=150, key=f"et_saisir_{st.session_state.form_count}")
        photos_fb = st.file_uploader("Médias", type=["jpg", "png", "jpeg", "pdf"], key=f"ph_{st.session_state.form_count}", accept_multiple_files=True)

    if st.button("💾 Enregistrer la recette", use_container_width=True):
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
                    data = {
                        "nom": nom_plat, 
                        "appareil": type_appareil, 
                        "temps_preparation": tps_prep,
                        "temps_cuisson": tps_cuis,
                        "ingredients": st.session_state.ingredients_recette, 
                        "etapes": etapes, 
                        "images": liste_medias
                    }
                    if envoyer_vers_github(f"data/recettes/{timestamp}_{nom_fic}.json", json.dumps(data, indent=4, ensure_ascii=False), "Nouveau"):
                        st.success("Enregistré !")
                        st.session_state.ingredients_recette = []
                        if 'toutes_recettes' in st.session_state: del st.session_state.toutes_recettes
                        st.session_state.form_count += 1
                        st.rerun()
