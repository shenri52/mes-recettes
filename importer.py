import streamlit as st
import json, base64, requests, time, io

from datetime import datetime
from PIL import Image
from utils import config_github, envoyer_vers_github

def recuperer_donnees_index():
    conf = config_github()
    url = f"https://raw.githubusercontent.com/{conf['owner']}/{conf['repo']}/main/data/index_recettes.json?t={int(time.time())}"
    try:
        res = requests.get(url)
        if res.status_code == 200:
            idx = res.json()
            ing = {i for r in idx for i in r.get('ingredients', []) if i}
            cat = {r.get('categorie') for r in idx if r.get('categorie')}
            ingredients = ["---"] + sorted(list(ing))
            categories = ["---"] + sorted(list(cat))
            return ingredients, categories
    except: pass
    return [""], [""]

def afficher():
    st.divider()
    
    # Initialisation session_state
    for k, v in {'form_count_img': 0, 'ingredients_img': [], 'liste_choix_img': ["---"], 'liste_categories_img': ["---"], 'cat_fixee': ""}.items():
        if k not in st.session_state: st.session_state[k] = v

    if len(st.session_state.liste_choix_img) <= 1:
        st.session_state.liste_choix_img, st.session_state.liste_categories_img = recuperer_donnees_index()

    f_id = st.session_state.form_count_img
    nom_plat = st.text_input("Nom de la recette", key=f"ni_{f_id}")
    
    c_app, c_prep, c_cuis = st.columns(3)
    type_appareil = c_app.selectbox("Appareil", options=sorted(["Aucun", "Cookeo", "Thermomix", "Ninja"]), key=f"ai_{f_id}")
    tps_prep = c_prep.text_input("Temps préparation", key=f"pri_{f_id}", placeholder="ex: 10 min")
    tps_cuis = c_cuis.text_input("Temps cuisson", key=f"cui_{f_id}", placeholder="ex: 5 min")

    # --- LOGIQUE CALLBACKS ---
    def ajouter_cat_img_nettoyer():
        nom_nouveau = st.session_state.get(f"ncat_{f_id}", "").strip()
        if nom_nouveau:
            if nom_nouveau not in st.session_state.liste_categories_img:
                st.session_state.liste_categories_img.append(nom_nouveau)
            st.session_state[f"scat_{f_id}"] = "---"
            st.session_state[f"ncat_{f_id}"] = ""

    def ajouter_ing_img_nettoyer():
        nom_nouveau = st.session_state.get(f"new_ing_{f_id}", "").strip()
        choix_actuel = st.session_state[f"sel_{f_id}"]
        ing_final = nom_nouveau if choix_actuel == "➕ Ajouter un nouveau..." else choix_actuel
        qte_val = st.session_state[f"qte_{f_id}"]
        if ing_final and ing_final != "---":
            st.session_state.ingredients_img.append({"Ingrédient": ing_final, "Quantité": qte_val})
            if ing_final not in st.session_state.liste_choix_img:
                st.session_state.liste_choix_img.append(ing_final)
            st.session_state[f"qte_{f_id}"] = ""
            st.session_state[f"new_ing_{f_id}"] = ""
            st.session_state[f"sel_{f_id}"] = "---"

    # --- CATÉGORIE ---
    col_cat, col_btn_cat = st.columns([2, 0.5])
    with col_cat:
        cat_sans_tiret = [c for c in st.session_state.liste_categories_img if c != "---"]
        opts_cat = ["---", "➕ Ajouter une nouvelle..."] + sorted(cat_sans_tiret)
        choix_cat = st.selectbox("Catégorie", options=opts_cat, key=f"scat_{f_id}")
        if choix_cat == "➕ Ajouter une nouvelle...":
            st.text_input("Nom de la catégorie", key=f"ncat_{f_id}")
        else:
            st.session_state.cat_fixee = choix_cat

    with col_btn_cat:
        st.write(" "); st.write(" ")
        if choix_cat == "➕ Ajouter une nouvelle...":
            st.button("➕", key=f"bcat_{f_id}", on_click=ajouter_cat_img_nettoyer)

    # --- INGRÉDIENTS ---
    col_ing, col_qte, col_btn_add = st.columns([2, 1, 0.6])
    with col_ing:
        liste_sans_tiret = [i for i in st.session_state.liste_choix_img if i != "---"]    
        opts_ing = ["---", "➕ Ajouter un nouveau..."] + sorted(liste_sans_tiret)
        choix_i = st.selectbox("Ingrédient", options=opts_ing, key=f"sel_{f_id}")
        if choix_i == "➕ Ajouter un nouveau...":
            st.text_input("Nom de l'ingrédient", key=f"new_ing_{f_id}")
        
    with col_qte:
        st.text_input("Quantité", key=f"qte_{f_id}")
            
    with col_btn_add:
        st.write(" "); st.write(" ") 
        if choix_i != "---":
            st.button("➕", key=f"btn_add_{f_id}", on_click=ajouter_ing_img_nettoyer)

    # --- SECTION MÉDIAS  ---
    photos_fb = st.file_uploader("📷 Photos de la recette", type=["jpg", "png", "jpeg"], key=f"fi_{f_id}", accept_multiple_files=True)

    # --- BLOC BOUTON ENREGISTRER ---
    if st.button("💾 Enregistrer", use_container_width=True):
        f_cat = st.session_state.cat_fixee
        
        # --- RECHERCHE DES DOUBLONS ---
        conf = config_github()
        url_idx = f"https://raw.githubusercontent.com/{conf['owner']}/{conf['repo']}/main/data/index_recettes.json?t={int(time.time())}"
        res_idx = requests.get(url_idx)
        idx_data_check = res_idx.json() if res_idx.status_code == 200 else []
        # On crée une liste des noms existants en MAJUSCULES pour comparer sans erreur
        noms_existants = [r['nom'].strip().upper() for r in idx_data_check]

        if not nom_plat:
            st.error("⚠️ Le nom de la recette est obligatoire.")
        elif nom_plat.strip().upper() in noms_existants:
            st.error(f"⚠️ La recette '{nom_plat.upper()}' existe déjà dans votre index.")
        elif not f_cat or f_cat == "---":
            st.error("⚠️ Veuillez choisir ou ajouter une catégorie.")
        elif not photos_fb:
            st.error("⚠️ L'ajout d'au moins une image est obligatoire.")
        else:
            with st.spinner("🚀 Envoi vers GitHub..."):
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                nom_fic, liste_medias = nom_plat.replace(" ", "_").lower(), []
                
                if photos_fb:
                    for idx, f in enumerate(photos_fb):
                        # Traitement de l'image (optimisation)
                        ext = f.name.lower().split('.')[-1]
                        data_env = f.getvalue()
                        if ext in ["jpg", "jpeg", "png"]:
                            img = Image.open(f).convert("RGB")
                            img.thumbnail((1200, 1200))
                            buf = io.BytesIO()
                            img.save(buf, format="JPEG", quality=80, optimize=True)
                            data_env, ext = buf.getvalue(), "jpg"
                        
                        ch_m = f"data/images/{ts}_{nom_fic}_{idx}.{ext}"
                        if envoyer_vers_github(ch_m, data_env, "Media", True): 
                            liste_medias.append(ch_m)

                # Création du JSON de la recette
                ch_r = f"data/recettes/{ts}_{nom_fic}.json"
                rec_data = {
                    "nom": nom_plat, 
                    "categorie": f_cat, 
                    "appareil": type_appareil, 
                    "temps_preparation": tps_prep, 
                    "temps_cuisson": tps_cuis, 
                    "ingredients": st.session_state.ingredients_img, 
                    "etapes": "Voir image jointe", 
                    "images": liste_medias
                }
                
                # Envoi Recette + Mise à jour Index
                if envoyer_vers_github(ch_r, json.dumps(rec_data, indent=4, ensure_ascii=False), "Import"):
                    conf = config_github()
                    url_idx = f"https://raw.githubusercontent.com/{conf['owner']}/{conf['repo']}/main/data/index_recettes.json"
                    res_idx = requests.get(url_idx)
                    idx_data = res_idx.json() if res_idx.status_code == 200 else []
                    
                    idx_data.append({
                        "nom": nom_plat, 
                        "categorie": f_cat, 
                        "appareil": type_appareil, 
                        "ingredients": [i['Ingrédient'] for i in st.session_state.ingredients_img], 
                        "chemin": ch_r
                    })
                    
                    envoyer_vers_github("data/index_recettes.json", json.dumps(idx_data, indent=4, ensure_ascii=False), "MAJ Index")

                    st.success("✅ Recette importée avec succès !")
                    
                    # --- RESET COMPLET ---
                    st.session_state.ingredients_img = []
                    st.session_state.cat_fixee = ""
                    # On force le changement d'ID de formulaire pour vider les widgets natifs
                    st.session_state.form_count_img += 1
                    
                    if 'index_recettes' in st.session_state: 
                        del st.session_state.index_recettes
                    
                    time.sleep(1)
                    st.rerun()
