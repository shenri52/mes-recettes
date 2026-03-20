import streamlit as st
import requests
import json
import time
import base64
from datetime import datetime
from PIL import Image
import io

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

@st.cache_data(ttl=600)  # Expire après 10 min d'inactivité ou après st.cache_data.clear()
def charger_json_github(chemin_fichier):
    """Charge un fichier JSON depuis GitHub avec anti-cache."""
    conf = get_github_config()
    url = f"https://raw.githubusercontent.com/{conf['owner']}/{conf['repo']}/main/{chemin_fichier}?t={int(time.time())}"
    try:
        res = requests.get(url)
        return res.json() if res.status_code == 200 else []
    except:
        return []

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
    
    if res_put.status_code in [200, 201]:
        # On ne vide le cache que si la sauvegarde a réussi
        st.cache_data.clear() 
        return True
    
    return False

# --- FONCTION POUR LA MAINTENANCE ET LES IMAGES ---

def envoyer_donnees_github(chemin, contenu, message, est_image=False):
    """Fonction universelle pour envoyer texte ou images."""
    conf = get_github_config()
    url = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/{chemin}"
    
    # Récupération du SHA
    res_get = requests.get(url, headers=conf['headers'])
    sha = res_get.json().get('sha') if res_get.status_code == 200 else None
    
    # Encodage spécifique selon le type
    contenu_b64 = base64.b64encode(contenu if est_image else contenu.encode('utf-8')).decode('utf-8')
    
    payload = {"message": message, "content": contenu_b64, "branch": "main"}
    if sha: payload["sha"] = sha
    
    res_put = requests.put(url, headers=conf['headers'], json=payload)
    if res_put.status_code in [200, 201]:
        st.cache_data.clear() # On vide le cache car le dépôt a changé
        return True
    return False

def scanner_depot_complet():
    """Scan récursif de tout le dépôt GitHub."""
    conf = get_github_config()
    url = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/git/trees/main?recursive=1"
    res = requests.get(url, headers=conf['headers'])
    return res.json().get('tree', []) if res.status_code == 200 else []

def get_index_options():
    """1. Récupère les ingrédients et catégories uniques pour les menus déroulants."""
    idx = charger_json_github("data/index_recettes.json")
    if idx:
        ing = {i for r in idx for i in r.get('ingredients', []) if i}
        cat = {r.get('categorie') for r in idx if r.get('categorie')}
        return ["---"] + sorted(list(ing)), ["---"] + sorted(list(cat))
    return ["---"], ["---"]

def traiter_et_compresser_image(file):
    """2. Compresse l'image à 75% et limite la taille à 1200px."""
    img = Image.open(file).convert("RGB")
    img.thumbnail((1200, 1200))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=75, optimize=True)
    return buf.getvalue(), "jpg"

def mettre_a_jour_index(nouvelle_recette_index):
    """3. Télécharge l'index, ajoute la ligne et renvoie sur GitHub."""
    idx_data = charger_json_github("data/index_recettes.json") or []
    idx_data.append(nouvelle_recette_index)
    return envoyer_donnees_github("data/index_recettes.json", json.dumps(idx_data, indent=4, ensure_ascii=False), "📈 MAJ Index")
