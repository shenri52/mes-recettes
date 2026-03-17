import streamlit as st
import json, base64, requests, time, io
from datetime import datetime
from PIL import Image

def config_github():
    return {
        "headers": {"Authorization": f"token {st.secrets['GITHUB_TOKEN']}", "Accept": "application/vnd.github.v3+json"},
        "owner": st.secrets["REPO_OWNER"], "repo": st.secrets["REPO_NAME"]
    }

def recuperer_donnees_index():
    conf = config_github()
    url = f"https://raw.githubusercontent.com/{conf['owner']}/{conf['repo']}/main/data/index_recettes.json?t={int(time.time())}"
    try:
        res = requests.get(url)
        if res.status_code == 200:
            idx = res.json()
            ing = {i for r in idx for i in r.get('ingredients', []) if i}
            cat = {r.get('categorie') for r in idx if r.get('categorie')}
            return sorted(list(ing)), sorted(list(cat))
    except: pass
    return [""], [""]

def envoyer_vers_github(chemin, contenu, message, binaire=False):
    conf = config_github()
    url = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/{chemin}"
    res_get = requests.get(url, headers=conf['headers'])
    sha = res_get.json().get('sha') if res_get.status_code == 200 else None
    cnt = base64.b64encode(contenu if binaire else contenu.encode('utf-8')).decode('utf-8')
    payload = {"message": message, "content": cnt, "branch": "main", "sha": sha} if sha else {"message": message, "content": cnt, "branch": "main"}
    return requests.put(url, headers=conf['headers'], json=payload).status_code in [200, 201]

def afficher():
    st.header("📥 Importer une recette")
    st.divider()
    
    # Initialisation session_state
    for k, v in {'form_count_img': 0, 'ingredients_img': [], 'liste_choix_img': [""], 'liste_categories_img': [""], 'cat_selectionnee': ""}.items():
        if k not in st.session_state: st.session_state[k] = v

    if len(st.session_state.liste_choix_img) <= 1:
        st.session_state.liste_choix_img, st.session_state.liste_categories_img = recuperer_donnees_index()

    f_id = st.session_state.form_count_img
    nom_plat = st.text_input("Nom de la recette", key=f"ni_{f_id}")
    
    c_app, c_prep, c_cuis = st.columns(3)
    type_appareil = c_app.selectbox("Appareil", options=sorted(["Aucun", "Cookeo", "Thermomix", "Ninja"]), key=f"ai_{f_id}")
    tps_prep = c_prep.text_input("Temps préparation", key=f"pri_{f_id}", placeholder="ex: 10 min")
    tps_cuis = c_cuis.text_input("Temps cuisson", key=f"cui_{f_id}", placeholder="ex: 5 min")

    # --- SECTION CATÉGORIE (Structure conservée) ---
    col_cat, col_btn_cat = st.columns([2, 0.5])
    with col_cat:
        opts_cat = sorted(st.session_state.liste_categories_img) + ["➕ Ajouter une nouvelle..."]
        choix_cat = st.selectbox("Catégorie", options=opts_cat, key=f"scat_{f_id}")
        cat_finale = st.text_input("Nom nouvelle catégorie", key=f"ncat_{f_id}") if choix_cat == "➕ Ajouter une nouvelle..." else choix_cat
    with col_btn_cat:
        st.write(" "); st.write(" ")
        if st.button("Ajouter", key=f"bcat_{f_id}") and cat_finale:
            st.session_state.cat_selectionnee = cat_finale
            if cat_finale not in st.session_state.liste_categories_img: st.session_state.liste_categories_img.append(cat_finale)
            st.toast(f"Catégorie fixée : {cat_finale}")

    if st.session_state.cat_selectionnee: st.info(f"📂 Catégorie retenue : **{st.session_state.cat_selectionnee}**")

    # --- SECTION INGRÉDIENTS (Structure conservée) ---
    col_ing, col_btn_add = st.columns([2, 0.5])
    with col_ing:
        opts_ing = sorted(st.session_state.liste_choix_img) + ["➕ Ajouter un nouveau..."]
        choix = st.selectbox("Ingrédient", options=opts_ing, key=f"si_{f_id}")
        ing_final = st.text_input("Nom", key=f"nwi_{f_id}") if choix == "➕ Ajouter un nouveau..." else choix
    with col_btn_add:
        st.write(" "); st.write(" ")
        if st.button("Ajouter", key=f"bi_{f_id}") and ing_final:
            st.session_state.ingredients_img.append({"Ingrédient": ing_final, "Quantité": ""})
            if ing_final not in st.session_state.liste_choix_img: st.session_state.liste_choix_img.append(ing_final)
            st.rerun()

    for i in st.session_state.ingredients_img: st.write(f"✅ {i['Ingrédient']}")
    photos_fb = st.file_uploader("Fichiers", type=["jpg", "png", "jpeg", "pdf"], key=f"fi_{f_id}", accept_multiple_files=True)

    if st.button("💾 Enregistrer", use_container_width=True) and nom_plat:
        with st.spinner("Enregistrement..."):
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            nom_fic, liste_medias = nom_plat.replace(" ", "_").lower(), []
            f_cat = st.session_state.cat_selectionnee if st.session_state.cat_selectionnee else cat_finale
            
            if photos_fb:
                for idx, f in enumerate(photos_fb):
                    ext, data_env = f.name.lower().split('.')[-1], f.getvalue()
                    if ext in ["jpg", "jpeg", "png"]:
                        img = Image.open(f).convert("RGB")
                        img.thumbnail((1200, 1200)) # Gain de place automatique
                        buf = io.BytesIO()
                        img.save(buf, format="JPEG", quality=80, optimize=True)
                        data_env, ext = buf.getvalue(), "jpg"
                    
                    ch_m = f"data/images/{ts}_{nom_fic}_{idx}.{ext}"
                    if envoyer_vers_github(ch_m, data_env, "Media", True): liste_medias.append(ch_m)

            ch_r = f"data/recettes/{ts}_{nom_fic}.json"
            rec_data = {"nom": nom_plat, "categorie": f_cat, "appareil": type_appareil, "temps_preparation": tps_prep, "temps_cuisson": tps_cuis, "ingredients": st.session_state.ingredients_img, "etapes": "Voir image jointe", "images": liste_medias}
            
            if envoyer_vers_github(ch_r, json.dumps(rec_data, indent=4, ensure_ascii=False), "Import"):
                res_idx = requests.get(f"https://raw.githubusercontent.com/{st.secrets['REPO_OWNER']}/{st.secrets['REPO_NAME']}/main/data/index_recettes.json")
                idx_data = res_idx.json() if res_idx.status_code == 200 else []
                idx_data.append({"nom": nom_plat, "categorie": f_cat, "appareil": type_appareil, "ingredients": [i['Ingrédient'] for i in st.session_state.ingredients_img], "chemin": ch_r})
                envoyer_vers_github("data/index_recettes.json", json.dumps(idx_data, indent=4, ensure_ascii=False), "MAJ Index")

                st.success("Importé !")
                st.session_state.ingredients_img, st.session_state.cat_selectionnee = [], ""
                if 'index_recettes' in st.session_state: del st.session_state.index_recettes
                st.session_state.form_count_img += 1
                st.rerun()
    st.divider()
