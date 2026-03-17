import streamlit as st
import json, base64, requests, time, io
from datetime import datetime
from PIL import Image

# --- CONFIGURATION ET API ---
def config_github():
    return {
        "headers": {
            "Authorization": f"token {st.secrets['GITHUB_TOKEN']}",
            "Accept": "application/vnd.github.v3+json"
        },
        "base_url": f"https://api.github.com/repos/{st.secrets['REPO_OWNER']}/{st.secrets['REPO_NAME']}/contents/"
    }

def envoyer_vers_github(chemin, contenu, message, binaire=False):
    conf = config_github()
    url = f"{conf['base_url']}{chemin}"
    res_get = requests.get(f"{url}?t={int(time.time())}", headers=conf['headers'])
    sha = res_get.json().get('sha') if res_get.status_code == 200 else None
    cnt = base64.b64encode(contenu if binaire else contenu.encode('utf-8')).decode('utf-8')
    payload = {"message": message, "content": cnt, "branch": "main"}
    if sha: payload["sha"] = sha
    return requests.put(url, headers=conf['headers'], json=payload).status_code in [200, 201]

def recuperer_donnees_index():
    url = f"https://raw.githubusercontent.com/{st.secrets['REPO_OWNER']}/{st.secrets['REPO_NAME']}/main/data/index_recettes.json?t={int(time.time())}"
    try:
        res = requests.get(url)
        if res.status_code == 200:
            index_data = res.json()
            ing = {i for r in index_data for i in r.get('ingredients', []) if i}
            cat = {r.get('categorie') for r in index_data if r.get('categorie')}
            return sorted(list(ing)), sorted(list(cat))
    except: pass
    return [""], [""]

# --- INTERFACE ---
def afficher():
    st.header("📥 Importer une recette")
    st.divider()
    
    # Initialisation session_state
    for key, val in {'form_count_img': 0, 'ingredients_img': [], 'liste_choix_img': [""], 'liste_categories_img': [""], 'cat_selectionnee': ""}.items():
        if key not in st.session_state: st.session_state[key] = val

    if len(st.session_state.liste_choix_img) <= 1:
        st.session_state.liste_choix_img, st.session_state.liste_categories_img = recuperer_donnees_index()

    f_id = st.session_state.form_count_img
    nom_plat = st.text_input("Nom de la recette", key=f"ni_{f_id}")
    
    c_app, c_prep, c_cuis = st.columns(3)
    type_appareil = c_app.selectbox("Appareil", options=sorted(["Aucun", "Cookeo", "Thermomix", "Ninja"]), key=f"ai_{f_id}")
    tps_prep = c_prep.text_input("Préparation", key=f"pri_{f_id}", placeholder="ex: 10 min")
    tps_cuis = c_cuis.text_input("Cuisson", key=f"cui_{f_id}", placeholder="ex: 5 min")

    # Section Catégorie
    col_cat, col_btn_cat = st.columns([2, 0.5])
    choix_cat = col_cat.selectbox("Catégorie", options=sorted(st.session_state.liste_categories_img) + ["➕ Ajouter une nouvelle..."], key=f"scat_{f_id}")
    cat_finale = col_cat.text_input("Nom nouvelle catégorie", key=f"ncat_{f_id}") if choix_cat == "➕ Ajouter une nouvelle..." else choix_cat
    
    col_btn_cat.write(" ") # Alignement
    if col_btn_cat.button("Ajouter", key=f"bcat_{f_id}") and cat_finale:
        st.session_state.cat_selectionnee = cat_finale
        if cat_finale not in st.session_state.liste_categories_img: st.session_state.liste_categories_img.append(cat_finale)
        st.toast(f"Catégorie fixée : {cat_finale}")

    if st.session_state.cat_selectionnee: st.info(f"📂 Sélection : **{st.session_state.cat_selectionnee}**")

    # Section Ingrédients
    col_ing, col_btn_add = st.columns([2, 0.5])
    choix_ing = col_ing.selectbox("Ingrédient", options=sorted(st.session_state.liste_choix_img) + ["➕ Ajouter un nouveau..."], key=f"si_{f_id}")
    ing_final = col_ing.text_input("Nom", key=f"nwi_{f_id}") if choix_ing == "➕ Ajouter un nouveau..." else choix_ing
    
    col_btn_add.write(" ") # Alignement
    if col_btn_add.button("Ajouter", key=f"bi_{f_id}") and ing_final:
        st.session_state.ingredients_img.append({"Ingrédient": ing_final, "Quantité": ""})
        if ing_final not in st.session_state.liste_choix_img: st.session_state.liste_choix_img.append(ing_final)
        st.rerun()

    for i in st.session_state.ingredients_img: st.write(f"✅ {i['Ingrédient']}")
    photos_fb = st.file_uploader("Fichiers (Images/PDF)", type=["jpg", "png", "jpeg", "pdf"], key=f"fi_{f_id}", accept_multiple_files=True)

    if st.button("💾 Enregistrer l'import", use_container_width=True) and nom_plat:
        with st.spinner("Enregistrement..."):
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            nom_fic = nom_plat.replace(" ", "_").lower()
            liste_medias, final_cat = [], st.session_state.cat_selectionnee or cat_finale
            
            if photos_fb:
                for idx, f in enumerate(photos_fb):
                    ext = f.name.lower().split('.')[-1]
                    data_img = f.getvalue()
                    if ext in ["jpg", "jpeg", "png"]:
                        img = Image.open(f).convert("RGB")
                        img.thumbnail((1200, 1200)) # Optimisation taille
                        buf = io.BytesIO()
                        img.save(buf, format="JPEG", quality=75, optimize=True)
                        data_img, ext = buf.getvalue(), "jpg"
                    
                    ch_img = f"data/images/{ts}_{nom_fic}_{idx}.{ext}"
                    if envoyer_vers_github(ch_img, data_img, "Media", True): liste_medias.append(ch_img)

            ch_recette = f"data/recettes/{ts}_{nom_fic}.json"
            recette_data = {"nom": nom_plat, "categorie": final_cat, "appareil": type_appareil, "temps_preparation": tps_prep, "temps_cuisson": tps_cuis, "ingredients": st.session_state.ingredients_img, "etapes": "Voir image jointe", "images": liste_medias}
            
            if envoyer_vers_github(ch_recette, json.dumps(recette_data, indent=4, ensure_ascii=False), "Import"):
                # Mise à jour index
                url_idx = f"https://raw.githubusercontent.com/{st.secrets['REPO_OWNER']}/{st.secrets['REPO_NAME']}/main/data/index_recettes.json"
                res_idx = requests.get(url_idx)
                index_list = res_idx.json() if res_idx.status_code == 200 else []
                index_list.append({"nom": nom_plat, "categorie": final_cat, "appareil": type_appareil, "ingredients": [i['Ingrédient'] for i in st.session_state.ingredients_img], "chemin": ch_recette})
                envoyer_vers_github("data/index_recettes.json", json.dumps(index_list, indent=4, ensure_ascii=False), "MAJ Index")

                st.success("Importé !")
                st.session_state.ingredients_img, st.session_state.cat_selectionnee = [], ""
                st.session_state.form_count_img += 1
                st.rerun()

    st.divider()
