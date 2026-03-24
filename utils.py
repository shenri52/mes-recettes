import streamlit as st
import requests, json, base64, time, io
from PIL import Image

# --- CONFIGURATION GITHUB ---
def config_github():
    """Retourne les paramètres de connexion à l'API GitHub."""
    return {
        "headers": {
            "Authorization": f"token {st.secrets['GITHUB_TOKEN']}",
            "Accept": "application/vnd.github.v3+json"
        },
        "owner": st.secrets["REPO_OWNER"],
        "repo": st.secrets["REPO_NAME"]
    }

# --- ENVOYER DES DONNÉES SUR GITHUB ---
def envoyer_vers_github(chemin, contenu, message, est_binaire=False):
    """Envoie ou met à jour un fichier sur GitHub avec gestion du SHA et du cache."""
    try:
        conf = config_github()
        url = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/{chemin}"
        
        # Récupération du SHA (anti-cache)
        res_get = requests.get(f"{url}?t={int(time.time())}", headers=conf['headers'])
        sha = res_get.json().get('sha') if res_get.status_code == 200 else None
        
        # Préparation du contenu
        if not est_binaire:
            if isinstance(contenu, (dict, list)):
                contenu_final = json.dumps(contenu, indent=4, ensure_ascii=False).encode('utf-8')
            else:
                contenu_final = contenu.encode('utf-8')
        else:
            contenu_final = contenu

        contenu_b64 = base64.b64encode(contenu_final).decode('utf-8')
        
        # Payload
        data = {"message": message, "content": contenu_b64, "branch": "main"}
        if sha: 
            data["sha"] = sha
            
        res = requests.put(url, headers=conf['headers'], json=data)
        return res.status_code in [200, 201]
    except Exception as e:
        st.error(f"Erreur technique API : {str(e)}")
        return False

# --- CHARGER DES DONNÉES DEPUIS GITHUB ---
def charger_donnees(chemin):
    """Télécharge un fichier (JSON) depuis raw.githubusercontent en ignorant le cache."""
    conf = config_github()
    url = f"https://raw.githubusercontent.com/{conf['owner']}/{conf['repo']}/main/{chemin}?t={int(time.time())}"
    try:
        res = requests.get(url)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    # Retourne une liste vide par défaut, sauf si c'est un dictionnaire attendu
    return [] if "planning" not in chemin else {}

# --- SUPPRIMER UN FICHIER SUR GITHUB ---
def supprimer_fichier_github(chemin):
    """Supprime un fichier spécifique sur le dépôt GitHub."""
    conf = config_github()
    url = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/{chemin.strip('/')}"
    get_res = requests.get(f"{url}?t={int(time.time())}", headers=conf['headers'])
    if get_res.status_code == 200:
        sha = get_res.json()['sha']
        res_del = requests.delete(url, headers=conf['headers'], json={"message": "Suppression", "sha": sha, "branch": "main"})
        return res_del.status_code in [200, 204]
    return False

# --- COMPRESSER UNE IMAGE ---
def compresser_image(upload_file):
    """Redimensionne et compresse une image (JPEG, max 1200x1200px) pour l'optimisation."""
    img = Image.open(upload_file)
    if img.mode in ("RGBA", "P"): 
        img = img.convert("RGB")
    img.thumbnail((1200, 1200))
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=80, optimize=True)
    return buffer.getvalue()

# --- VÉRIFIER LES DOUBLONS ---
def verifier_doublon(nom_test, index_actuel, chemin_actuel=None):
    """Retourne True si le nom de recette existe déjà dans l'index."""
    for r in index_actuel:
        if r.get('nom', '').strip().lower() == nom_test.strip().lower():
            if chemin_actuel and r.get('chemin') == chemin_actuel:
                continue
            return True
    return False
