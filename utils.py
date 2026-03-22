import streamlit as st
import requests
import json
import time
import base64
import pytz
import io
import re
import unicodedata

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
    # Utilise le timestamp actuel pour forcer GitHub à ne pas servir une vieille version
    url = f"https://raw.githubusercontent.com/{conf['owner']}/{conf['repo']}/main/{chemin}?t={int(time.time())}"    
    try:
        res = requests.get(url)
        if res.status_code == 200:
            return res.json()
        # Retourne une liste vide pour l'index ou les plats, un dict vide sinon
        return [] if "plats_rapides" in chemin_fichier or "index" in chemin_fichier else {}
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
    """3. Télécharge l'index VIA L'API (Zéro délai), ajoute la ligne et renvoie sur GitHub."""
    conf = get_github_config()
    # On tape directement dans l'API ultra-rapide au lieu du lien raw
    url = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/data/index_recettes.json"
    
    res_get = requests.get(url, headers=conf['headers'])
    idx_data = []
    
    if res_get.status_code == 200:
        try:
            # L'API GitHub renvoie le fichier crypté en base64, on le décrypte :
            contenu_b64 = res_get.json().get('content', '')
            contenu_str = base64.b64decode(contenu_b64).decode('utf-8')
            idx_data = json.loads(contenu_str)
        except Exception as e:
            idx_data = []
    else:
        # Sécurité au cas où le fichier est introuvable
        idx_data = charger_json_github("data/index_recettes.json") or []

    # On ajoute la nouvelle recette à la VRAIE liste à jour
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
    st.cache_data.clear()
    # On récupère la page d'où l'on vient
    page_actuelle = st.session_state.get('page')

    # NETTOYAGE CIBLÉ
    if page_actuelle in ['importer', 'ajouter', 'import_odt', 'import_pdf']:
        # 1. On vide les listes
        st.session_state["ingredients_img"] = []      # Page Importer
        st.session_state["ingredients_recette"] = []  # Page Saisir
        st.session_state["cat_fixee"] = ""
        st.session_state.liste_odt = []               # Page ODT
        st.session_state.import_idx = 0               # Page ODT
        
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
    if not ligne: return None
    
    # 1. Normalisation des espaces (pour l'ODT)
    ligne = ligne.replace('\xa0', ' ').strip()
    if not ligne or ":" in ligne: return None 

    # 2. Séparation brute par le premier espace
    parts = ligne.split(' ', 1)
    qte = parts[0].strip() if len(parts) > 1 else ""
    ing = parts[1].strip() if len(parts) > 1 else ligne

    # 3. NETTOYAGE UNIQUE DE LA QUANTITÉ
    # On cible l'espace + "de" ou juste le "de" si l'espace a déjà été splitté
    if qte.lower().endswith(" de"):
        qte = qte[:-3].strip()
    elif qte.lower() == "de": # Si le 'de' s'est retrouvé seul dans sa colonne
        qte = ""

    # 4. RE-VÉRIFICATION SI LE "DE" EST RESTÉ DANS QUANTITÉ
    if " de" in qte.lower():
        qte = qte.lower().replace(" de", "").strip()

    return {
        "Ingrédient": ing.capitalize(),
        "Quantité": qte
    }

def nettoyer_nom_github(nom):
    """Transforme 'Gâteau à la crême' en 'gateau_a_la_creme' pour éviter les bugs GitHub."""
    # 1. Normalise (sépare la lettre de l'accent) et garde uniquement la lettre
    nom = "".join(c for c in unicodedata.normalize('NFD', nom) if unicodedata.category(c) != 'Mn')
    # 2. Remplace tout ce qui n'est pas lettre ou chiffre par un underscore
    nom = re.sub(r'[^a-zA-Z0-9]', '_', nom)
    # 3. Nettoie les doubles underscores et met en minuscule
    return re.sub(r'_+', '_', nom).lower().strip('_')
    
def sauvegarder_recette_complete(nom, categorie, ingredients, etapes, photos_files=None, appareil="Aucun", t_prep="", t_cuis="", **kwargs):
    """
    Fonction TOUT-EN-UN mise à jour pour accepter les fichiers photos bruts.
    """
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    nom_propre = nettoyer_nom_github(nom) 
    ch_r = f"data/recettes/{ts}_{nom_propre}.json"
    
    liste_medias = []
    # --- GESTION DES PHOTOS (Correction : on gère plusieurs photos si besoin) ---
    if photos_files:
        # On s'assure que c'est une liste pour boucler dessus
        fichiers = photos_files if isinstance(photos_files, list) else [photos_files]
        for idx, fichier in enumerate(fichiers):
            try:
                img_bits, ext = traiter_et_compresser_image(fichier)
                # On ajoute l'index (idx) au nom pour ne pas écraser les photos
                ch_m = f"data/images/{ts}_{nom_propre}_{idx}.jpg"
                if envoyer_donnees_github(ch_m, img_bits, f"📸 Photo: {nom}", True):
                    liste_medias.append(ch_m)
            except Exception as e:
                st.error(f"Erreur image: {e}")

    # --- PRÉPARATION DU JSON ---
    rec_data = {
        "nom": nom, "categorie": categorie, "appareil": appareil,
        "temps_preparation": t_prep, "temps_cuisson": t_cuis,
        "ingredients": ingredients, "etapes": etapes, "images": liste_medias
    }
    
    # --- ENVOI GITHUB ---
    if envoyer_donnees_github(ch_r, json.dumps(rec_data, indent=4, ensure_ascii=False), f"📝 Import: {nom}"):
        
        # --- ÉTAPE CRUCIALE : ON VIDE LE CACHE AVANT L'INDEX ---
        st.cache_data.clear() 

        # Construction de la liste pour l'index
        liste_index = []
        source_ings = ingredients.to_dict('records') if hasattr(ingredients, 'to_dict') else ingredients
        
        for i in source_ings:
            nom_i = i.get('Ingrédient') or i.get('Détecté') or i.get('nom')
            if nom_i:
                liste_index.append(nom_i.strip().capitalize())

        # Mise à jour de l'index réel
        mettre_a_jour_index({
            "nom": nom, "categorie": categorie, "appareil": appareil,
            "ingredients": list(set(liste_index)),
            "chemin": ch_r
        })
        
        return True, nom

    return False, nom

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
