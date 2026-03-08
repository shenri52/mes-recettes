import streamlit as st
import requests
import json
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

def charger_index_local():
    conf = config_github()
    url = f"https://raw.githubusercontent.com/{conf['owner']}/{conf['repo']}/main/data/index_recettes.json?t={int(time.time())}"
    res = requests.get(url)
    return res.json() if res.status_code == 200 else []

def afficher():
    st.header("🩺 Diagnostic Approfondi")
    
    if st.button("🔍 Lancer l'analyse complète"):
        conf = config_github()
        # 1. Récupération de l'arbre réel sur GitHub
        url_tree = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/git/trees/main?recursive=1&t={int(time.time())}"
        res = requests.get(url_tree, headers=conf['headers'])
        
        if res.status_code == 200:
            tree = res.json().get('tree', [])
            # Tous les fichiers .json dans /data (sauf l'index lui-même)
            fichiers_sur_github = [
                item['path'] for item in tree 
                if item['path'].startswith('data/') 
                and item['path'].endswith('.json') 
                and item['path'] != 'data/index_recettes.json'
            ]
            
            # 2. Récupération de l'index
            index_actuel = charger_index_local()
            chemins_dans_index = [r['chemin'] for r in index_actuel]
            
            # --- CALCULS ---
            hors_index = [f for f in fichiers_sur_github if f not in chemins_dans_index]
            fantomes = [c for c in chemins_dans_index if c not in fichiers_sur_github]

            # --- AFFICHAGE DES RÉSULTATS ---
            col1, col2, col3 = st.columns(3)
            col1.metric("Fichiers physiques", len(fichiers_sur_github))
            col2.metric("Entrées dans l'index", len(index_actuel))
            col3.metric("Hors index", len(hors_index))

            if hors_index:
                st.warning(f"⚠️ {len(hors_index)} fichiers ne sont pas répertoriés :")
                for f in hors_index:
                    st.code(f)
                st.session_state.a_reparer = hors_index
            else:
                st.success("✅ Aucun fichier n'est oublié par l'index.")

            if fantomes:
                st.error(f"🚫 {len(fantomes)} entrées de l'index pointent vers des fichiers inexistants (Fantômes) :")
                for f in fantomes:
                    st.text(f)

            # --- LA LISTE BRUTE (Pour trouver l'intrus) ---
            with st.expander("📂 Voir la liste complète des 40 fichiers"):
                for i, f in enumerate(sorted(fichiers_sur_github), 1):
                    st.write(f"{i}. `{f}`")
        else:
            st.error("Erreur de connexion à GitHub.")

    # Logique de réparation (Bouton 2) identique à la précédente...
    if "a_reparer" in st.session_state and st.session_state.a_reparer:
        # (Garder ton code d'envoi vers GitHub ici)
        pass
