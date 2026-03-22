import streamlit as st
import requests
import json
import time
import base64
import pytz
import io
import re

from datetime import datetime
from PIL import Image

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
        return [] if "plats_rapides" in chemin_fichier or "index" in chemin_fichier else {}

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

def supprimer_fichier_github(chemin_fichier, message_commit="Suppression"):
    """Supprime un fichier sur GitHub (nécessaire pour les photos et recettes)."""
    conf = get_github_config()
    url = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/{chemin_fichier.strip('/')}"
    res_get = requests.get(url, headers=conf['headers'])
    if res_get.status_code == 200:
        sha = res_get.json()['sha']
        payload = {"message": message_commit, "sha": sha, "branch": "main"}
        res_del = requests.delete(url, headers=conf['headers'], json=payload)
        if res_del.status_code in [200, 204]:
            st.cache_data.clear()
            return True
    return False

def charger_recette_specifique(url_raw):
    """Charge le contenu JSON d'une recette précise via son URL raw."""
    try:
        res = requests.get(url_raw)
        return res.json() if res.status_code == 200 else {}
    except:
        return {}

def initialiser_session():
    """Initialise les variables globales de l'application."""
    if "plats_rapides" not in st.session_state:
        st.session_state.plats_rapides = charger_json_github("data/plats_rapides.json") or []
    if "offset_semaine" not in st.session_state:
        st.session_state.offset_semaine = 0
    if "authentifie" not in st.session_state:
        st.session_state["authentifie"] = False
    if "mode_public" not in st.session_state:
        st.session_state["mode_public"] = False
    if 'page' not in st.session_state:
        st.session_state.page = 'accueil'

def naviguer_vers(nom_page):
    """Change la page active et force le rafraîchissement."""
    st.session_state.page = nom_page
    st.rerun()

def deconnexion():
    """Réinitialise l'accès et nettoie uniquement si on quitte la saisie."""
    # On récupère la page d'où l'on vient
    page_actuelle = st.session_state.get('page')

    # NETTOYAGE CIBLÉ
    if page_actuelle in ['importer', 'ajouter']:
        # 1. On vide les listes
        st.session_state["ingredients_img"] = []      # Page Importer
        st.session_state["ingredients_recette"] = []  # Page Saisir
        st.session_state["cat_fixee"] = ""
        
        # Incrémenter les compteurs pour vider les champs texte (Nom, Temps, etc.)
        if 'form_count_img' in st.session_state:
            st.session_state.form_count_img += 1
        if 'form_count' in st.session_state:
            st.session_state.form_count += 1
            
    st.session_state.page = 'accueil'
    st.session_state["mode_public"] = False

def actualiser_toutes_les_stats():
    """Lance la mise à jour des recettes ET du stockage en une seule fois."""
    from collections import Counter
    from datetime import datetime
    import pytz
    
    success_recettes = False
    success_stockage = False
    
    tz_paris = pytz.timezone('Europe/Paris')
    now = datetime.now(tz_paris).strftime("%d/%m/%Y à %H:%M")

    # --- PARTIE 1 : RECETTES ---
    index = charger_json_github("data/index_recettes.json")
    if index:
        resume_r = {
            "derniere_maj": now,
            "total_recettes": len(index),
            "categories": dict(sorted(Counter(r.get('categorie', 'Non classé') for r in index).items())),
            "appareils": dict(sorted(Counter(r.get('appareil', 'Aucun') for r in index).items()))
        }
        success_recettes = sauvegarder_json_github("data/stats_recettes.json", resume_r, "📊 MAJ Stats Recettes")

    # --- PARTIE 2 : STOCKAGE ---
    tree = scanner_depot_complet()
    if tree:
        stats_c = {"Recettes (JSON)": {"nb": 0, "poids": 0}, "Photos (Images)": {"nb": 0, "poids": 0}, "Fichiers Système & Apps": {"nb": 0, "poids": 0}}
        for item in [i for i in tree if i.get('type') == 'blob']:
            path, size = item['path'].lower(), item.get('size', 0)
            key = "Recettes (JSON)" if "recettes/" in path else "Photos (Images)" if "images/" in path else "Fichiers Système & Apps"
            stats_c[key]["nb"] += 1
            stats_c[key]["poids"] += size
        
        poids_total = sum(d["poids"] for d in stats_c.values())
        resume_s = {
            "derniere_maj": now,
            "poids_total_mo": round(poids_total / (1024 * 1024), 2),
            "details": [{"Type": k, "Nombre": v["nb"], "Mo": round(v["poids"] / (1024 * 1024), 2)} for k, v in stats_c.items()]
        }
        success_stockage = sauvegarder_json_github("data/data_stockage.json", resume_s, "📊 MAJ Stats Stockage")

    return success_recettes and success_stockage

def parser_ligne_ingredient(ligne):
    """Transforme '180g de farine' en {'Ingrédient': 'Farine', 'Quantité': '180g'}"""
    ligne = ligne.strip()
    if not ligne or ":" in ligne: return None # Évite de prendre les titres comme 'Ingrédients :'
    match = re.match(r"(\d+\s*\w*)\s*(?:de|d')?\s*(.*)", ligne, re.I)
    if match:
        return {"Ingrédient": match.group(2).strip().capitalize(), "Quantité": match.group(1).strip()}
    return {"Ingrédient": ligne.capitalize(), "Quantité": ""}

def sauvegarder_recette_complete(nom, categorie, ingredients, etapes, image_data=None, appareil="Aucun"):
    """Centralise la sauvegarde pour les nouveaux modules d'import."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    nom_fic = nom.lower().replace(" ", "_").replace("'", "_")
    liste_medias = []

    # 1. Image (image_data doit être un BytesIO déjà compressé)
    if image_data:
        ch_m = f"data/images/{ts}_{nom_fic}.jpg"
        if envoyer_donnees_github(ch_m, image_data, f"📸 Photo: {nom}", True):
            liste_medias.append(ch_m)

    # 2. JSON
    ch_r = f"data/recettes/{ts}_{nom_fic}.json"
    rec_data = {
        "nom": nom, "categorie": categorie, "appareil": appareil,
        "temps_preparation": "", "temps_cuisson": "",
        "ingredients": ingredients, "etapes": etapes, "images": liste_medias
    }
    
    # 3. GitHub & Index
    if envoyer_donnees_github(ch_r, json.dumps(rec_data, indent=4, ensure_ascii=False), f"📝 Import: {nom}"):
        mettre_a_jour_index({
            "nom": nom, "categorie": categorie, "appareil": appareil,
            "ingredients": [i['Ingrédient'] for i in ingredients if i.get('Ingrédient')],
            "chemin": ch_r
        })
        return True
    return False

def verifier_doublon_recette(nom_saisi):
    """
    Vérifie si le nom de la recette existe déjà dans l'index.
    L'appel à charger_json_github est protégé par le cache Streamlit, 
    donc pas de surcharge de l'API !
    """
    if not nom_saisi: 
        return False
    
    # On charge l'index (c'est instantané grâce au @st.cache_data)
    idx_data = charger_json_github("data/index_recettes.json") or []
    
    # On extrait les noms des recettes
    noms_existants = [r.get('nom', '').strip().lower() for r in idx_data if r.get('nom')]
    
    # On compare
    return nom_saisi.strip().lower() in noms_existants
