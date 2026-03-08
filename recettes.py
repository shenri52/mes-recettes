import streamlit as st
import requests
import json
import base64
import time

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

def envoyer_vers_github(chemin, contenu, message):
    conf = config_github()
    url = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/{chemin}"
    res_get = requests.get(f"{url}?t={int(time.time())}", headers=conf['headers'])
    sha = res_get.json().get('sha') if res_get.status_code == 200 else None
    contenu_b64 = base64.b64encode(contenu.encode('utf-8')).decode('utf-8')
    data = {"message": message, "content": contenu_b64, "branch": "main"}
    if sha: data["sha"] = sha
    res = requests.put(url, headers=conf['headers'], json=data)
    return res.status_code in [200, 201]

def supprimer_fichier_github(chemin):
    conf = config_github()
    url = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/{chemin.strip('/')}"
    get_res = requests.get(f"{url}?t={int(time.time())}", headers=conf['headers'])
    if get_res.status_code == 200:
        sha = get_res.json()['sha']
        requests.delete(url, headers=conf['headers'], json={"message": "Suppression", "sha": sha, "branch": "main"})
        return True
    return False

# --- 2. GESTION DE L'INDEX ---
def charger_index():
    if 'index_recettes' not in st.session_state:
        conf = config_github()
        url = f"https://raw.githubusercontent.com/{conf['owner']}/{conf['repo']}/main/data/index_recettes.json"
        res = requests.get(url)
        if res.status_code == 200:
            st.session_state.index_recettes = res.json()
        else:
            st.session_state.index_recettes = []
    return st.session_state.index_recettes

def sauvegarder_index_global(index_maj):
    index_trie = sorted(index_maj, key=lambda x: x['nom'].lower())
    if envoyer_vers_github("data/index_recettes.json", json.dumps(index_trie, indent=4, ensure_ascii=False), "MAJ Index"):
        st.session_state.index_recettes = index_trie
        return True
    return False

# --- 4. CONSULTATION ---
def afficher_consultation():
    index = charger_index()
    st.header("📚 Mes recettes")
    st.write("---")

    # FILTRES (Version d'origine 4 colonnes)
    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
    recherche = c1.text_input("🔍 Rechercher", "").lower()
    
    cats = ["Tous"] + sorted(list(set(r.get('categorie', 'Non classé') for r in index)))
    apps = ["Tous"] + sorted(list(set(r.get('appareil', 'Aucun') for r in index)))
    
    tous_ings = []
    for r in index: 
        if r.get('ingredients'): tous_ings.extend(r['ingredients'])
    ings = ["Tous"] + sorted(list(set(tous_ings)))

    f_cat = c2.selectbox("Catégorie", cats)
    f_app = c3.selectbox("Appareil", apps)
    f_ing = c4.selectbox("Ingrédient", ings)

    # Filtrage
    resultats = [
        r for r in index 
        if (not recherche or recherche in r['nom'].lower())
        and (f_cat == "Tous" or r['categorie'] == f_cat)
        and (f_app == "Tous" or r['appareil'] == f_app)
        and (f_ing == "Tous" or f_ing in r.get('ingredients', []))
    ]

    noms_filtres = [r['nom'].upper() for r in resultats]
    id_unique = f"sel_{recherche}_{f_cat}_{f_app}_{f_ing}"
    
    # --- ZONE SÉLECTEUR + ICÔNE ACTUALISER ---
    st.write("📖 Sélectionner une recette")
    col_liste, col_btn = st.columns([0.9, 0.1])

    with col_liste:
        choix = st.selectbox("📖 Sélectionner une recette", ["---"] + noms_filtres, key=id_unique, label_visibility="collapsed")

    with col_btn:
        if st.button("🔄", help="Actualiser"):
            if 'index_recettes' in st.session_state:
                del st.session_state.index_recettes
            st.rerun()

    st.write("---")

    if choix != "---":
        info = resultats[noms_filtres.index(choix)]
        url_full = f"https://raw.githubusercontent.com/{config_github()['owner']}/{config_github()['repo']}/main/{info['chemin']}"
        recette = requests.get(url_full).json()
        
        st.subheader(recette['nom'].upper())
        st.write(f"**Catégorie :** {recette.get('categorie', 'Non classé')}")
        st.write(f"**Appareil :** {recette.get('appareil', 'Aucun')}")
        
        col_t, col_i = st.columns([1, 1])
        with col_t:
            st.write("**Ingrédients :**")
            for i in recette.get('ingredients', []):
                st.write(f"- {i.get('Quantité', '')} {i.get('Ingrédient', '')}")
            st.write(f"**Instructions :**\n{recette.get('etapes')}")
        with col_i:
            images = recette.get('images', [])
            if images:
                # --- AJOUT NAVIGATION ---
                if "img_idx" not in st.session_state or st.session_state.get("last_recette") != choix:
                    st.session_state.img_idx = 0
                    st.session_state.last_recette = choix

                img_url = f"https://raw.githubusercontent.com/{config_github()['owner']}/{config_github()['repo']}/main/{images[st.session_state.img_idx].strip('/')}"
                st.image(img_url, use_container_width=True)
                
                if len(images) > 1:
                    nb_col1, nb_col2, nb_col3 = st.columns([1, 2, 1])
                    if nb_col1.button("⬅️", key="prev_img"):
                        st.session_state.img_idx = (st.session_state.img_idx - 1) % len(images)
                        st.rerun()
                    nb_col2.write(f"{st.session_state.img_idx + 1} / {len(images)}")
                    if nb_col3.button("➡️", key="next_img"):
                        st.session_state.img_idx = (st.session_state.img_idx + 1) % len(images)
                        st.rerun()
                # --- FIN NAVIGATION ---

        st.divider()
        b1, b2 = st.columns(2)
        if b1.button("🗑️ Supprimer", use_container_width=True):
            if supprimer_fichier_github(info['chemin']):
                nouvel_index = [r for r in index if r['chemin'] != info['chemin']]
                sauvegarder_index_global(nouvel_index)
                st.rerun()
        if b2.button("✍️ Modifier", use_container_width=True):
            st.info("Modification bientôt disponible.")
