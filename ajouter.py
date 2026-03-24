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
            st.session_state.index_recettes_complet = idx # Sauvegardé pour la vérification des doublons
            ing = {i for r in idx for i in r.get('ingredients', []) if i}
            cat = {r.get('categorie') for r in idx if r.get('categorie')}
            return ["---"] + sorted(list(ing)), ["---"] + sorted(list(cat))
    except: pass
    return ["---"], ["---"]

def verifier_doublon_recette(nom_saisi):
    """Fonction dédiée à la vérification des doublons (comparaison en majuscules)"""
    if 'index_recettes_complet' not in st.session_state:
        conf = config_github()
        url = f"https://raw.githubusercontent.com/{conf['owner']}/{conf['repo']}/main/data/index_recettes.json?t={int(time.time())}"
        try:
            res = requests.get(url)
            if res.status_code == 200:
                st.session_state.index_recettes_complet = res.json()
            else:
                return False
        except:
            return False
    
    # Comparaison stricte en MAJUSCULES
    noms_existants = [str(r.get('nom', '')).strip().upper() for r in st.session_state.index_recettes_complet]
    return nom_saisi.strip().upper() in noms_existants

def envoyer_vers_github(chemin, contenu, message, binaire=False):
    conf = config_github()
    url = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/{chemin}"
    res_get = requests.get(url, headers=conf['headers'])
    sha = res_get.json().get('sha') if res_get.status_code == 200 else None
    cnt = base64.b64encode(contenu if binaire else contenu.encode('utf-8')).decode('utf-8')
    payload = {"message": message, "content": cnt, "branch": "main", "sha": sha} if sha else {"message": message, "content": cnt, "branch": "main"}
    return requests.put(url, headers=conf['headers'], json=payload).status_code in [200, 201]

def afficher():
    st.header("✍️ Ajouter une recette")

    for k, v in {'form_count': 0, 'ingredients_recette': [], 'liste_choix': [""], 'liste_categories': [""], 'cat_fixee': ""}.items():
        if k not in st.session_state: st.session_state[k] = v

    if len(st.session_state.liste_choix) <= 1:
        with st.spinner("📦 Synchronisation..."):
            st.session_state.liste_choix, st.session_state.liste_categories = recuperer_donnees_index()

    f_id = st.session_state.form_count
    with st.container():
        nom_plat = st.text_input("Nom de la recette", key=f"nom_{f_id}")
        
        c_app, c_prep, c_cuis = st.columns(3)
        type_appareil = c_app.selectbox("Appareil utilisé", options=sorted(["Aucun", "Cookeo", "Thermomix", "Ninja"]), key=f"app_{f_id}")
        tps_prep = c_prep.text_input("Temps préparation", key=f"prep_{f_id}", placeholder="ex: 15 min")
        tps_cuis = c_cuis.text_input("Temps cuisson", key=f"cuis_{f_id}", placeholder="ex: 20 min")
              
        # --- CATÉGORIE ---
        def ajouter_cat_et_nettoyer():
            nom_nouveau = st.session_state.get(f"ncat_{f_id}", "").strip()
            if nom_nouveau:
                if nom_nouveau not in st.session_state.liste_categories:
                    st.session_state.liste_categories.append(nom_nouveau)
                st.session_state[f"scat_{f_id}"] = "---"
                st.session_state[f"ncat_{f_id}"] = ""

        col_cat, col_btn_cat = st.columns([2, 0.5])
        with col_cat:
            cats_existantes = sorted([c for c in st.session_state.liste_categories if c and c != "---"])
            opts_cat = ["---"] + cats_existantes + ["➕ Ajouter une nouvelle..."]
            choix_cat = st.selectbox("Catégorie", options=opts_cat, key=f"scat_{f_id}")
            
            if choix_cat == "➕ Ajouter une nouvelle...":
                st.text_input("Nom de la catégorie", key=f"ncat_{f_id}")
            else:
                st.session_state.cat_fixee = choix_cat

        with col_btn_cat:
            st.write(" "); st.write(" ")
            if choix_cat == "➕ Ajouter une nouvelle...":
                st.button("➕", key=f"bcat_valider_{f_id}", on_click=ajouter_cat_et_nettoyer)

        # ---  INGRÉDIENTS  ---
        def ajouter_ing_et_nettoyer():
            nom_nouveau = st.session_state.get(f"new_ing_{f_id}", "")
            choix_actuel = st.session_state[f"sel_{f_id}"]
            
            ing_final = nom_nouveau if choix_actuel == "➕ Ajouter un nouveau..." else choix_actuel
            qte_val = st.session_state[f"qte_{f_id}"]

            if ing_final and ing_final != "---":
                st.session_state.ingredients_recette.append({
                    "Ingrédient": ing_final, 
                    "Quantité": qte_val
                })
                
                if ing_final not in st.session_state.liste_choix:
                    st.session_state.liste_choix.append(ing_final)
                
                if f"new_ing_{f_id}" in st.session_state: 
                    st.session_state[f"new_ing_{f_id}"] = ""
                st.session_state[f"qte_{f_id}"] = ""
                st.session_state[f"sel_{f_id}"] = "---"

        col_ing, col_qte, col_btn_add = st.columns([2, 1, 0.6])
        with col_ing:
            opts_ing = st.session_state.liste_choix[:1] + ["➕ Ajouter un nouveau..."] + st.session_state.liste_choix[1:]
            choix_i = st.selectbox("Ingrédient", options=opts_ing, key=f"sel_{f_id}")
            if choix_i == "➕ Ajouter un nouveau...":
                st.text_input("Nom de l'ingrédient", key=f"new_ing_{f_id}")
        
        with col_qte:
            st.text_input("Quantité", key=f"qte_{f_id}")
        
        with col_btn_add:
            st.write(" "); st.write(" ")
            if choix_i != "---":
                st.button("➕", key=f"btn_add_ing_{f_id}", on_click=ajouter_ing_et_nettoyer)

        for i in st.session_state.ingredients_recette:
            st.write(f"✅ {i['Quantité']} {i['Ingrédient']}")


    # --- ÉTAPES ---
    etapes_plat = st.text_area("Étapes de la recette", key=f"etapes_{f_id}", placeholder="Saisissez les étapes ici...")
        
    # --- SECTION MÉDIAS  ---
    photos_fb = st.file_uploader(
        "📸 Photos de la recette", 
        type=["jpg", "png", "jpeg"], 
        key=f"fi_{f_id}", 
        accept_multiple_files=True
    )
    
    # --- BLOC BOUTON ENREGISTRER  ---
    if st.button("💾 Enregistrer", use_container_width=True):
        f_cat = st.session_state.cat_fixee
        
        # --- VÉRIFICATIONS OBLIGATOIRES ET DOUBLONS ---
        if not nom_plat or nom_plat.strip() == "":
            st.error("⚠️ Le nom de la recette est obligatoire.")
        elif verifier_doublon_recette(nom_plat):
            st.error(f"⚠️ Une recette nommée '{nom_plat}' existe déjà dans votre base de données !")
        elif not f_cat or f_cat == "---":
            st.error("⚠️ Veuillez choisir ou ajouter une catégorie.")
        else:
            with st.spinner("Enregistrement en cours..."):
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                nom_fic, liste_medias = nom_plat.replace(" ", "_").lower(), []
                
                if photos_fb:
                    for idx, f in enumerate(photos_fb):
                        ext, data_env = f.name.lower().split('.')[-1], f.getvalue()
                        if ext in ["jpg", "jpeg", "png"]:
                            img = Image.open(f).convert("RGB")
                            img.thumbnail((1200, 1200))
                            buf = io.BytesIO()
                            img.save(buf, format="JPEG", quality=80, optimize=True)
                            data_env, ext = buf.getvalue(), "jpg"
                        
                        ch_m = f"data/images/{ts}_{nom_fic}_{idx}.{ext}"
                        if envoyer_vers_github(ch_m, data_env, "Media", True): 
                            liste_medias.append(ch_m)

                ch_r = f"data/recettes/{ts}_{nom_fic}.json"
                rec_data = {
                    "nom": nom_plat, 
                    "categorie": f_cat, 
                    "appareil": type_appareil, 
                    "temps_preparation": tps_prep, 
                    "temps_cuisson": tps_cuis, 
                    "ingredients": st.session_state.ingredients_recette, 
                    "etapes": etapes_plat if etapes_plat.strip() else "Voir image jointe", 
                    "images": liste_medias
                }
                
                if envoyer_vers_github(ch_r, json.dumps(rec_data, indent=4, ensure_ascii=False), "Import"):
                    res_idx = requests.get(f"https://raw.githubusercontent.com/{st.secrets['REPO_OWNER']}/{st.secrets['REPO_NAME']}/main/data/index_recettes.json")
                    idx_data = res_idx.json() if res_idx.status_code == 200 else []
                    
                    # On garde la casse saisie par l'utilisateur pour l'index
                    idx_data.append({
                        "nom": nom_plat, 
                        "categorie": f_cat, 
                        "appareil": type_appareil, 
                        "ingredients": [i['Ingrédient'] for i in st.session_state.ingredients_recette], 
                        "chemin": ch_r
                    })
                    envoyer_vers_github("data/index_recettes.json", json.dumps(idx_data, indent=4, ensure_ascii=False), "MAJ Index")

                    st.success("✅ Recette importée avec succès !")
                    
                    # --- RESET ---
                    st.session_state.ingredients_recette = []
                    st.session_state.cat_fixee = ""
                    st.session_state.cat_selectionnee = ""
                    
                    # On nettoie le cache pour forcer un rechargement au prochain affichage
                    if 'index_recettes' in st.session_state: 
                        del st.session_state.index_recettes
                    if 'index_recettes_complet' in st.session_state:
                        del st.session_state.index_recettes_complet
                    
                    st.session_state.form_count += 1
                    
                    time.sleep(1.5)
                    st.rerun()
