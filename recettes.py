import streamlit as st
import requests
import json
import base64
import time
import uuid
from PIL import Image
import io

# --- 1. CONFIGURATION TECHNIQUE ---
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

def envoyer_vers_github(chemin, contenu, message, est_binaire=False):
    try:
        conf = config_github()
        url = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/{chemin}"
        res_get = requests.get(f"{url}?t={int(time.time())}", headers=conf['headers'])
        sha = res_get.json().get('sha') if res_get.status_code == 200 else None
        contenu_b64 = base64.b64encode(contenu if est_binaire else contenu.encode('utf-8')).decode('utf-8')
        data = {"message": message, "content": contenu_b64, "branch": "main"}
        if sha: data["sha"] = sha
        res = requests.put(url, headers=conf['headers'], json=data)
        return res.status_code in [200, 201]
    except Exception as e:
        st.error(f"Erreur technique : {str(e)}")
        return False

def supprimer_fichier_github(chemin):
    conf = config_github()
    url = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/{chemin.strip('/')}"
    get_res = requests.get(f"{url}?t={int(time.time())}", headers=conf['headers'])
    if get_res.status_code == 200:
        sha = get_res.json()['sha']
        res_del = requests.delete(url, headers=conf['headers'], json={"message": "Suppression", "sha": sha, "branch": "main"})
        return res_del.status_code in [200, 204]
    return False

# --- 2. TRAITEMENT IMAGE ---
def compresser_image(upload_file):
    img = Image.open(upload_file)
    if img.mode in ("RGBA", "P"): img = img.convert("RGB")
    img.thumbnail((1200, 1200))
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=80, optimize=True)
    return buffer.getvalue()

# --- 3. GESTION DE L'INDEX ---
def charger_index():
    conf = config_github()
    url = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/data/index_recettes.json?t={int(time.time())}"
    res = requests.get(url, headers=conf['headers'])
    if res.status_code == 200:
        content_b64 = res.json()['content']
        content_json = base64.b64decode(content_b64).decode('utf-8')
        st.session_state.index_recettes = json.loads(content_json)
    elif 'index_recettes' not in st.session_state:
        st.session_state.index_recettes = []
    return st.session_state.index_recettes

def sauvegarder_index_global(index_maj):
    index_trie = sorted(index_maj, key=lambda x: x['nom'].lower())
    if envoyer_vers_github("data/index_recettes.json", json.dumps(index_trie, indent=4, ensure_ascii=False), "MAJ Index"):
        st.session_state.index_recettes = index_trie
        return True
    return False

# --- 4. LOGIQUE D'AFFICHAGE ET MODIFICATION ---
def afficher():
    def nettoyer_modif():
        """Supprime les données temporaires d'édition quand on change de recette."""
        if "img_idx" in st.session_state:
            st.session_state.img_idx = 0
        for key in list(st.session_state.keys()):
            if any(key.startswith(p) for p in ["edit_", "init_done_", "ings_list_"]):
                del st.session_state[key]
                
    index = charger_index()
    st.header("📚 Mes recettes")
    st.write("---")

    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
    recherche = c1.text_input("🔍 Rechercher", "").lower()
    cats_existantes = sorted(list(set(r.get('categorie', 'Non classé') for r in index)))
    apps = ["Tous"] + sorted(list(set(r.get('appareil', 'Aucun') for r in index)))
    
    tous_ings_bruts = []
    for r in index: 
        if r.get('ingredients'): tous_ings_bruts.extend(r['ingredients'])
    liste_ingredients_unique = sorted(list(set(tous_ings_bruts)))

    f_cat = c2.selectbox("Catégorie", ["Tous"] + cats_existantes)
    f_app = c3.selectbox("Appareil", apps)
    f_ing = c4.selectbox("Ingrédient", ["Tous"] + liste_ingredients_unique)

    resultats = [
        r for r in index 
        if (not recherche or recherche in r['nom'].lower())
        and (f_cat == "Tous" or r['categorie'] == f_cat)
        and (f_app == "Tous" or r['appareil'] == f_app)
        and (f_ing == "Tous" or f_ing in r.get('ingredients', []))
    ]

    noms_filtres = [r['nom'].upper() for r in resultats]

    choix = st.selectbox(
        "📖 Sélectionner une recette", 
        ["---"] + noms_filtres, 
        key="select_recette",
        on_change=nettoyer_modif # <-- C'est cette ligne qui remplace ton ancien bloc IF
    )
    
    if choix != "---":
        info = resultats[noms_filtres.index(choix)]
        url_full = f"https://raw.githubusercontent.com/{config_github()['owner']}/{config_github()['repo']}/main/{info['chemin']}?t={int(time.time())}"
        recette = requests.get(url_full).json()

        m_edit = f"edit_{info['chemin']}"
        if m_edit not in st.session_state: st.session_state[m_edit] = False

        if st.session_state[m_edit]:
            st.subheader("✍️ Modification")
            state_key = f"ings_list_{info['chemin']}"
            init_flag = f"init_done_{info['chemin']}"
            
            if init_flag not in st.session_state or state_key not in st.session_state:
                st.session_state[state_key] = [
                    {"id": str(uuid.uuid4()), "Ingrédient": i.get("Ingrédient", ""), "Quantité": i.get("Quantité", "")}
                    for i in recette.get('ingredients', [])
                ]
                st.session_state[init_flag] = True

            st.write("**Ingrédients**")
            rows_to_delete = []
            if state_key in st.session_state:
                for idx, item in enumerate(st.session_state[state_key]):
                    col_q, col_n, col_del = st.columns([1, 2, 0.5])
                    st.session_state[state_key][idx]["Quantité"] = col_q.text_input("Qté", value=item["Quantité"], key=f"q_{item['id']}", label_visibility="collapsed")
                    
                    base_opts = ["--- Choisir ---", "➕ NOUVEL INGRÉDIENT"]
                    opts = base_opts + sorted(list(set(liste_ingredients_unique)))
                    current_ing = item["Ingrédient"]
                    default_index = opts.index(current_ing) if current_ing in opts else 0
                    
                    choix_sel = col_n.selectbox("Nom", options=opts, index=default_index, key=f"sel_{item['id']}", label_visibility="collapsed")

                    if choix_sel == "➕ NOUVEL INGRÉDIENT":
                        nouveau_nom = col_n.text_input("Nom", value=current_ing if current_ing not in opts else "", key=f"new_{item['id']}", placeholder="Nom...")
                        st.session_state[state_key][idx]["Ingrédient"] = nouveau_nom
                    else:
                        st.session_state[state_key][idx]["Ingrédient"] = choix_sel if choix_sel != "--- Choisir ---" else ""
                    
                    if col_del.button("🗑️", key=f"del_{item['id']}"):
                        rows_to_delete.append(idx)

            if rows_to_delete:
                for r_idx in reversed(rows_to_delete):
                    st.session_state[state_key].pop(r_idx)
                st.rerun()

            if st.button("➕ Ajouter un ingrédient"):
                st.session_state[state_key].append({"id": str(uuid.uuid4()), "Ingrédient": "", "Quantité": ""})
                st.rerun()

            with st.form(f"form_meta_{info['chemin']}"):
                e_nom = st.text_input("Nom", value=recette.get('nom', ''))
                e_cat = st.selectbox("Catégorie", options=sorted(cats_existantes), index=sorted(cats_existantes).index(recette.get('categorie', 'Non classé')))
                e_app = st.selectbox("Appareil", ["Aucun", "Cookeo", "Thermomix", "Ninja"], index=["Aucun", "Cookeo", "Thermomix", "Ninja"].index(recette.get('appareil', 'Aucun')))
                e_etapes = st.text_area("Instructions", value=recette.get('etapes', ''), height=150)
                
                photos_actuelles = recette.get('images', [])
                photos_a_garder = []
                for p_path in photos_actuelles:
                    img_url = f"https://raw.githubusercontent.com/{config_github()['owner']}/{config_github()['repo']}/main/{p_path.strip('/')}"
                    col_img, col_check = st.columns([1, 4])
                    col_img.image(img_url, width=60)
                    if col_check.checkbox(f"Garder {p_path.split('/')[-1]}", value=True, key=f"kp_{p_path}"):
                        photos_a_garder.append(p_path)

                nouvelles_photos = st.file_uploader("Ajouter des photos", accept_multiple_files=True, type=['jpg', 'jpeg', 'png'])

                c_save, c_cancel = st.columns(2)
                if c_save.form_submit_button("💾 Enregistrer", use_container_width=True):
                    for p_path in photos_actuelles:
                        if p_path not in photos_a_garder: supprimer_fichier_github(p_path)
                    
                    final_photos = photos_a_garder.copy()
                    for f in nouvelles_photos:
                        nom_img = f"data/images/{int(time.time())}_{f.name}"
                        img_data = compresser_image(f)
                        if envoyer_vers_github(nom_img, img_data, f"Photo: {e_nom}", est_binaire=True):
                            final_photos.append(nom_img)

                    ings_clean = [{"Ingrédient": i["Ingrédient"], "Quantité": i["Quantité"]} for i in st.session_state[state_key] if i["Ingrédient"]]
                    recette_maj = recette.copy()
                    recette_maj.update({"nom": e_nom, "categorie": e_cat, "appareil": e_app, "ingredients": ings_clean, "etapes": e_etapes, "images": final_photos})
                    
                    if envoyer_vers_github(info['chemin'], json.dumps(recette_maj, indent=4, ensure_ascii=False), f"MAJ: {e_nom}"):
                        for item in index:
                            if item['chemin'] == info['chemin']:
                                item.update({"nom": e_nom, "categorie": e_cat, "appareil": e_app, "ingredients": [i['Ingrédient'] for i in ings_clean]})
                        sauvegarder_index_global(index)
                        if state_key in st.session_state: del st.session_state[state_key]
                        if init_flag in st.session_state: del st.session_state[init_flag]
                        st.session_state[m_edit] = False
                        st.rerun()

                if c_cancel.form_submit_button("❌ Annuler", use_container_width=True):
                    if state_key in st.session_state: del st.session_state[state_key]
                    if init_flag in st.session_state: del st.session_state[init_flag]
                    st.session_state[m_edit] = False
                    st.rerun()
        else:
            # --- AFFICHAGE CLASSIQUE AVEC NAVIGATION PHOTO ---
            st.subheader(recette['nom'].upper())
            col_t, col_i = st.columns([1, 1])
            with col_t:
                st.write(f"**Catégorie :** {recette.get('categorie', 'Non classé')}")
                st.write(f"**Appareil :** {recette.get('appareil', 'Aucun')}")
                st.write("**Ingrédients :**")
                for i in recette.get('ingredients', []):
                    st.write(f"- {i.get('Quantité', '')} {i.get('Ingrédient', '')}")
                st.write(f"**Instructions :**\n{recette.get('etapes')}")
            
            with col_i:
                images = recette.get('images', [])
                if images:
                    # 1. Initialisation de l'index
                    if "img_idx" not in st.session_state:
                        st.session_state.img_idx = 0
                    
                    # Sécurité : on s'assure que l'index ne dépasse pas le nombre d'images
                    if st.session_state.img_idx >= len(images):
                        st.session_state.img_idx = 0
                    
                    # 2. Affichage de la photo actuelle
                    img_url = f"https://raw.githubusercontent.com/{config_github()['owner']}/{config_github()['repo']}/main/{images[st.session_state.img_idx].strip('/')}?t={int(time.time())}"
                    st.image(img_url, use_container_width=True)
                    
                    # 3. NAVIGATION (Uniquement si plus d'une photo existe)
                    if len(images) > 1:
                        nb1, nb2, nb3 = st.columns([1, 2, 1])
                        
                        with nb1:
                            if st.button("◀️", use_container_width=True, key="prev"):
                                st.session_state.img_idx = (st.session_state.img_idx - 1) % len(images)
                                st.rerun()
                        
                        with nb2:
                            st.write(f"<p style='text-align:center'>{st.session_state.img_idx + 1} / {len(images)}</p>", unsafe_allow_html=True)
                        
                        with nb3:
                            if st.button("▶️", use_container_width=True, key="next"):
                                st.session_state.img_idx = (st.session_state.img_idx + 1) % len(images)
                                st.rerun()
                else:
                    st.info("📷 Aucune photo pour cette recette.")

            
        # --- SECTION ACTIONS (MODIFIER / SUPPRIMER) ---
        # On ne montre ces boutons QUE si l'utilisateur est admin (authentifié)
        if st.session_state.get("authentifie", False):
            b1, b2 = st.columns(2)
            st.divider()
            if b1.button("🗑️ Supprimer la recette", use_container_width=True):
                # Ta logique de suppression complète (Fichier + Images + Index)
                if supprimer_fichier_github(info['chemin']):
                    for p in recette.get('images', []): 
                        supprimer_fichier_github(p)
                    nouvel_index = [r for r in index if r['chemin'] != info['chemin']]
                    sauvegarder_index_global(nouvel_index)
                    st.rerun()
            
            if b2.button("✍️ Modifier", use_container_width=True):
                # Ton mode édition
                st.session_state[m_edit] = True
                st.rerun()
        
        st.divider()

if __name__ == "__main__":
    afficher()
