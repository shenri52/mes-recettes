import streamlit as st
import requests
import json
import base64
import time
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
    if 'index_recettes' not in st.session_state:
        conf = config_github()
        url = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/data/index_recettes.json"
        res = requests.get(f"{url}?t={int(time.time())}", headers=conf['headers'])
        if res.status_code == 200:
            content_b64 = res.json()['content']
            content_json = base64.b64decode(content_b64).decode('utf-8')
            st.session_state.index_recettes = json.loads(content_json)
        else:
            st.session_state.index_recettes = []
    return st.session_state.index_recettes

def sauvegarder_index_global(index_maj):
    index_trie = sorted(index_maj, key=lambda x: x['nom'].lower())
    if envoyer_vers_github("data/index_recettes.json", json.dumps(index_trie, indent=4, ensure_ascii=False), "MAJ Index"):
        st.session_state.index_recettes = index_trie
        return True
    return False

# --- 4. CALLBACKS DE SUPPRESSION ET AJOUT ---
def supprimer_ingredient(state_key, index_a_supprimer):
    st.session_state[state_key].pop(index_a_supprimer)

def ajouter_ingredient(state_key):
    st.session_state[state_key].append({"Ingrédient": "", "Quantité": ""})

# --- 5. CONSULTATION ET MODIFICATION ---
def afficher():
    index = charger_index()
    st.header("📚 Mes recettes")
    st.write("---")

    # FILTRES
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
    choix = st.selectbox("📖 Sélectionner une recette", ["---"] + noms_filtres, key="select_recette")

    if choix != "---":
        info = resultats[noms_filtres.index(choix)]
        url_full = f"https://raw.githubusercontent.com/{config_github()['owner']}/{config_github()['repo']}/main/{info['chemin']}"
        recette = requests.get(url_full).json()

        m_edit = f"edit_{info['chemin']}"
        if m_edit not in st.session_state: st.session_state[m_edit] = False

        if st.session_state[m_edit]:
            st.subheader("✍️ Modification")
            state_key = f"ings_edit_{info['chemin']}"
            
            if state_key not in st.session_state:
                st.session_state[state_key] = recette.get('ingredients', [])

            # --- SECTION INGRÉDIENTS ---
            st.write("**Ingrédients**")
            
            # On affiche les ingrédients
            for idx in range(len(st.session_state[state_key])):
                # On utilise des colonnes bien alignées
                col_q, col_n, col_del = st.columns([1, 2, 0.5])
                
                # Update direct du session state via le paramètre 'key'
                col_q.text_input("Qté", 
                                key=f"{state_key}_q_{idx}", 
                                value=st.session_state[state_key][idx].get('Quantité', ''),
                                label_visibility="collapsed")
                
                ing_nom = st.session_state[state_key][idx].get('Ingrédient', '')
                opts = sorted(list(set(liste_ingredients_unique + ([ing_nom] if ing_nom else []))))
                
                col_n.selectbox("Nom", 
                               options=opts, 
                               index=opts.index(ing_nom) if ing_nom in opts else 0,
                               key=f"{state_key}_n_{idx}",
                               label_visibility="collapsed")
                
                # Le bouton de suppression appelle le callback
                col_del.button("🗑️", 
                             key=f"del_{info['chemin']}_{idx}", 
                             on_click=supprimer_ingredient, 
                             args=(state_key, idx))

            st.button("➕ Ajouter un ingrédient", on_click=ajouter_ingredient, args=(state_key,))

            # --- FORMULAIRE POUR LE RESTE ---
            with st.form(f"form_meta_{info['chemin']}"):
                e_nom = st.text_input("Nom", value=recette.get('nom', ''))
                e_cat = st.selectbox("Catégorie", options=sorted(cats_existantes), index=sorted(cats_existantes).index(recette.get('categorie', 'Non classé')))
                e_app = st.selectbox("Appareil", ["Aucun", "Cookeo", "Thermomix", "Ninja"], index=["Aucun", "Cookeo", "Thermomix", "Ninja"].index(recette.get('appareil', 'Aucun')))
                e_etapes = st.text_area("Instructions", value=recette.get('etapes', ''), height=150)
                
                st.write("**Photos**")
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
                
                if c_save.form_submit_button("💾 Enregistrer tout", use_container_width=True):
                    # 1. On synchronise les ingrédients depuis les clés dynamiques avant de sauvegarder
                    ings_finalized = []
                    for i in range(len(st.session_state[state_key])):
                        q_val = st.session_state[f"{state_key}_q_{i}"]
                        n_val = st.session_state[f"{state_key}_n_{i}"]
                        if n_val.strip():
                            ings_finalized.append({"Ingrédient": n_val, "Quantité": q_val})

                    # 2. Nettoyage photos
                    for p_path in photos_actuelles:
                        if p_path not in photos_a_garder: supprimer_fichier_github(p_path)
                    
                    # 3. Upload nouvelles photos
                    final_photos = photos_a_garder.copy()
                    for f in nouvelles_photos:
                        nom_img = f"images/{int(time.time())}_{f.name}"
                        img_data = compresser_image(f)
                        if envoyer_vers_github(nom_img, img_data, f"Photo: {e_nom}", est_binaire=True):
                            final_photos.append(nom_img)

                    # 4. Envoi GitHub
                    recette_maj = recette.copy()
                    recette_maj.update({
                        "nom": e_nom, "categorie": e_cat, "appareil": e_app, 
                        "ingredients": ings_finalized, "etapes": e_etapes, "images": final_photos
                    })
                    
                    if envoyer_vers_github(info['chemin'], json.dumps(recette_maj, indent=4, ensure_ascii=False), f"MAJ: {e_nom}"):
                        for item in index:
                            if item['chemin'] == info['chemin']:
                                item.update({"nom": e_nom, "categorie": e_cat, "appareil": e_app, "ingredients": [i['Ingrédient'] for i in ings_finalized]})
                        sauvegarder_index_global(index)
                        
                        # Reset des champs de saisie (Nettoyage session_state)
                        for k in list(st.session_state.keys()):
                            if k.startswith(state_key): del st.session_state[k]
                        st.session_state[m_edit] = False
                        st.rerun()

                if c_cancel.form_submit_button("❌ Annuler", use_container_width=True):
                    for k in list(st.session_state.keys()):
                        if k.startswith(state_key): del st.session_state[k]
                    st.session_state[m_edit] = False
                    st.rerun()
        else:
            # --- MODE AFFICHAGE ---
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
                    if "img_idx" not in st.session_state or st.session_state.get("last_recette") != choix:
                        st.session_state.img_idx = 0
                        st.session_state.last_recette = choix
                    img_url = f"https://raw.githubusercontent.com/{config_github()['owner']}/{config_github()['repo']}/main/{images[st.session_state.img_idx].strip('/')}"
                    st.image(img_url, use_container_width=True)
                    if len(images) > 1:
                        nb_col1, nb_col2, nb_col3 = st.columns([1, 2, 1])
                        if nb_col1.button("⬅️"):
                            st.session_state.img_idx = (st.session_state.img_idx - 1) % len(images)
                            st.rerun()
                        nb_col2.write(f"{st.session_state.img_idx + 1}/{len(images)}")
                        if nb_col3.button("➡️"):
                            st.session_state.img_idx = (st.session_state.img_idx + 1) % len(images)
                            st.rerun()

            st.divider()
            b1, b2 = st.columns(2)
            if b1.button("🗑️ Supprimer la recette", use_container_width=True):
                if supprimer_fichier_github(info['chemin']):
                    for p in recette.get('images', []): supprimer_fichier_github(p)
                    nouvel_index = [r for r in index if r['chemin'] != info['chemin']]
                    sauvegarder_index_global(nouvel_index)
                    st.rerun()
            if b2.button("✍️ Modifier", use_container_width=True):
                st.session_state[m_edit] = True
                st.rerun()

if __name__ == "__main__":
    afficher()
