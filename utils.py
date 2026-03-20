import streamlit as st
import requests
import json
import time
import base64
from datetime import datetime

def get_github_config():
    """Récupère les identifiants GitHub depuis les secrets Streamlit."""
    return {
        "token": st.secrets["GITHUB_TOKEN"],
        "owner": st.secrets["REPO_OWNER"],
        "repo": st.secrets["REPO_NAME"],
        "headers": {
            "Authorization": f"token {st.secrets['GITHUB_TOKEN']}",
            "Accept": "application/vnd.github.v3+json"
        }
    }

def charger_json_github(chemin_fichier):
    """Charge un fichier JSON depuis GitHub avec anti-cache."""
    conf = get_github_config()
    url = f"https://raw.githubusercontent.com/{conf['owner']}/{conf['repo']}/main/{chemin_fichier}?t={int(time.time())}"
    res = requests.get(url)
    return res.json() if res.status_code == 200 else []

def sauvegarder_json_github(chemin_fichier, donnees, message_commit="Mise à jour"):
    """Gère la sauvegarde vers GitHub avec gestion du SHA."""
    conf = get_github_config()
    url = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/{chemin_fichier}"
    
    res_get = requests.get(url, headers=conf['headers'])
    sha = res_get.json().get('sha') if res_get.status_code == 200 else None

    contenu_json = json.dumps(donnees, indent=4, ensure_ascii=False)
    contenu_base64 = base64.b64encode(contenu_json.encode('utf-8')).decode('utf-8')

    payload = {"message": message_commit, "content": contenu_base64}
    if sha: 
        payload["sha"] = sha

    res_put = requests.put(url, json=payload, headers=conf['headers'])
    return res_put.status_code in [200, 201]
