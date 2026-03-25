import streamlit as st
import requests, json, base64, time

# --- CONFIGURATION GITHUB ---
def config_github():
    return {
      "headers": {"Authorization": f"token {st.secrets['GITHUB_TOKEN']}",
                  "Accept": "application/vnd.github.v3+json"},
      "owner": st.secrets["REPO_OWNER"],
      "repo": st.secrets["REPO_NAME"]
    }

# --- GESTION DE L'INDEX DES RECETTES---
def charger_index():
    conf = config_github()
    url = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/data/index_recettes.json?t={int(time.time())}"
    try:
        res = requests.get(url, headers=conf['headers'])
        if res.status_code == 200:
            content_b64 = res.json()['content']
            content_json = base64.b64decode(content_b64).decode('utf-8')
            st.session_state.index_recettes = json.loads(content_json)
        else:
            st.session_state.index_recettes = []
    except Exception:
        # En cas d'erreur de décodage ou de fichier vide, on initialise à vide
        st.session_state.index_recettes = []
    return st.session_state.index_recettes

