import streamlit as st
import requests, json, base64, time, io
from PIL import Image

# --- CONFIGURATION GITHUB ---
def config_github():
    return {
      "headers": {"Authorization": f"token {st.secrets['GITHUB_TOKEN']}",
                  "Accept": "application/vnd.github.v3+json"},
      "owner": st.secrets["REPO_OWNER"],
      "repo": st.secrets["REPO_NAME"]
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

def sauvegarder_index(index_maj):
    index_trie = sorted(index_maj, key=lambda x: x['nom'].lower())
    if envoyer_vers_github("data/index_recettes.json", json.dumps(index_trie, indent=4, ensure_ascii=False), "MAJ Index"):
        st.session_state.index_recettes = index_trie
        return True
    return False

def recuperer_donnees_index():
    idx = charger_index()
    if idx:
        ing = {i for r in idx for i in r.get('ingredients', []) if i}
        cat = {r.get('categorie') for r in idx if r.get('categorie')}
        return ["---"] + sorted(list(ing)), ["---"] + sorted(list(cat))
    return ["---"], ["---"]
    
# --- Fonction de vérification des doublons ---
def verifier_doublon(nom_test, index, chemin_actuel=None):
    """
    Retourne True si le nom existe déjà dans l'index (hors la recette en cours d'édition).
    """
    for r in index:
        # On compare en minuscules et sans espaces inutiles
        if r['nom'].strip().lower() == nom_test.strip().lower():
            # Si on est en mode édition, on ignore le doublon si c'est la même recette (même chemin)
            if chemin_actuel and r['chemin'] == chemin_actuel:
                continue
            return True
    return False

# --- Fonction de compression des images ---
def compresser_image(upload_file, qualite=80, taille_max=(1000, 1000)):
    """Compresse l'image pour GitHub (centralisé)."""
    img = Image.open(upload_file)
    if img.mode in ("RGBA", "P"): 
        img = img.convert("RGB")
    img.thumbnail(taille_max)
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=qualite, optimize=True)
    return buffer.getvalue()

# --- Fonction de sauvegarde du projet---
def telecharger_projet_complet():
    """Récupère le ZIP du dépôt complet depuis GitHub."""
    conf = config_github()
    # URL de l'API pour obtenir le ZIP de la branche principale
    url = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/zipball/main"
    
    response = requests.get(url, headers=conf['headers'])
    
    if response.status_code == 200:
        return response.content
    return None

# --- Fonction de suppression d'une recette ---
def supprimer_fichier_github(chemin):
    conf = config_github()
    url = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/{chemin.strip('/')}"
    get_res = requests.get(f"{url}?t={int(time.time())}", headers=conf['headers'])
    if get_res.status_code == 200:
        sha = get_res.json()['sha']
        res_del = requests.delete(url, headers=conf['headers'], json={"message": "Suppression", "sha": sha, "branch": "main"})
        return res_del.status_code in [200, 204]
    return False
