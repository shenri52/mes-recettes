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

def sauvegarder_index(index_maj):
    index_trie = sorted(index_maj, key=lambda x: x['nom'].lower())
    if envoyer_vers_github("data/index_recettes.json", json.dumps(index_trie, indent=4, ensure_ascii=False), "MAJ Index"):
        st.session_state.index_recettes = index_trie
        return True
    return False

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
