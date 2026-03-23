import streamlit as st
import requests
import base64
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

def config_github_maintenance():
    conf = config_github()
    conf['base_url'] = f"https://api.github.com/repos/{st.secrets['REPO_OWNER']}/{st.secrets['REPO_NAME']}/contents/"
    return conf

def envoyer_vers_github(chemin, contenu, message, binaire=False):
    try:
        conf = config_github()
        url = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/{chemin}"
        res_get = requests.get(f"{url}?t={int(time.time())}", headers=conf['headers'])
        sha = res_get.json().get('sha') if res_get.status_code == 200 else None
        contenu_b64 = base64.b64encode(contenu if binaire else contenu.encode('utf-8')).decode('utf-8')
        data = {"message": message, "content": contenu_b64, "branch": "main"}
        if sha:
            data["sha"] = sha
        res = requests.put(url, headers=conf['headers'], json=data)
        return res.status_code in [200, 201]
    except Exception as e:
        st.error(f"Erreur technique : {str(e)}")
        return False

def recuperer_donnees_index():
    conf = config_github()
    url = f"https://raw.githubusercontent.com/{conf['owner']}/{conf['repo']}/main/data/index_recettes.json?t={int(time.time())}"
    try:
        res = requests.get(url)
        if res.status_code == 200:
            idx = res.json()
            st.session_state.index_recettes = idx
            ing = {i for r in idx for i in r.get('ingredients', []) if i}
            cat = {r.get('categorie') for r in idx if r.get('categorie')}
            return idx, ["---"] + sorted(list(ing)), ["---"] + sorted(list(cat))
    except Exception as e:
        st.warning(f"Impossible de récupérer l'index : {e}")

    st.session_state.index_recettes = []
    return [], ["---"], ["---"]

def refresh_index_session():
    index_complet, _, _ = recuperer_donnees_index()
    st.session_state.index_recettes = index_complet
    st.session_state['liste_recettes_filtrees'] = ["---"] + [r['nom'].upper() for r in index_complet]
