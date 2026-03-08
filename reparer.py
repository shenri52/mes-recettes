import streamlit as st
import requests
import json
import base64
import time

# --- FONCTIONS TECHNIQUES AUTONOMES ---
# Ces fonctions permettent au script de fonctionner sans importer app.py
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

def envoyer_vers_github(chemin, contenu, message):
    conf = config_github()
    url = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/{chemin}"
    # Anti-cache pour être sûr de l'état du fichier sur GitHub
    res_get = requests.get(f"{url}?t={int(time.time())}", headers=conf['headers'])
    sha = res_get.json().get('sha') if res_get.status_code == 200 else None
    
    contenu_b64 = base64.b64encode(contenu.encode('utf-8')).decode('utf-8')
    data = {"message": message, "content": contenu_b64, "branch": "main"}
    if sha: 
        data["sha"] = sha
        
    res = requests.put(url, headers=conf['headers'], json=data)
    return res.status_code in [200, 201]

def charger_index_local():
    conf = config_github()
    # On force la récupération du JSON frais pour la comparaison
    url = f"https://raw.githubusercontent.com/{conf['owner']}/{conf['repo']}/main/data/index_recettes.json?t={int(time.time())}"
    res = requests.get(url)
    if res.status_code == 200:
        return res.json()
    return []

# --- INTERFACE DE RÉPARATION ---
def afficher():
    st.header("🛠️ Diagnostic et Réparation")
    st.write("Ce module scanne votre dossier `data/` sur GitHub pour trouver les recettes oubliées.")

    # BOUTON 1 : ANALYSE
    if st.button("🔍 Réparer l'index : analyser les fichiers manquants"):
        conf = config_github()
        # On récupère l'arborescence complète du dépôt
        url_tree = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/git/trees/main?recursive=1"
        res = requests.get(url_tree, headers=conf['headers'])
        
        if res.status_code == 200:
            tree = res.json().get('tree', [])
            # On liste tous les fichiers JSON dans data/ sauf l'index
            fichiers_physiques = [
                item['path'] for item in tree 
                if item['path'].startswith('data/') 
                and item['path'].endswith('.json') 
                and item['path'] != 'data/index_recettes.json'
            ]
            
            index_actuel = charger_index_local()
            chemins_index = [r['chemin'] for r in index_actuel]
            
            # Comparaison
            manquantes = [f for f in fichiers_physiques if f not in chemins_index]
            
            if manquantes:
                st.warning(f"⚠️ {len(manquantes)} fichier(s) trouvé(s) hors index :")
                for m in manquantes:
                    st.code(m)
                # Sauvegarde temporaire dans la session pour l'étape suivante
                st.session_state.a_reparer = manquantes
            else:
                st.success("✅ Félicitations ! Votre index est parfaitement synchronisé.")
                if "a_reparer" in st.session_state:
                    del st.session_state.a_reparer
        else:
            st.error("Impossible d'accéder à la liste des fichiers sur GitHub.")

    # BOUTON 2 : RÉPARATION (Visible uniquement si manquants détectés)
    if "a_reparer" in st.session_state and st.session_state.a_reparer:
        st.divider()
        st.info("Voulez-vous intégrer ces fichiers à l'index ?")
        
        if st.button("🚀 Appliquer la réparation"):
            with st.spinner("Récupération des données..."):
                manquantes = st.session_state.a_reparer
                index_actuel = charger_index_local()
                nouvelles_recettes = []
                
                for chemin in manquantes:
                    # On va lire chaque fichier pour récupérer Nom, Catégorie, etc.
                    url_raw = f"https://raw.githubusercontent.com/{config_github()['owner']}/{config_github()['repo']}/main/{chemin}"
                    res_rec = requests.get(url_raw)
                    if res_rec.status_code == 200:
                        data = res_rec.json()
                        nouvelles_recettes.append({
                            "nom": data.get("nom", "Sans nom"),
                            "categorie": data.get("categorie", "Non classé"),
                            "appareil": data.get("appareil", "Aucun"),
                            "ingredients": [i.get("Ingrédient") for i in data.get("ingredients", [])],
                            "chemin": chemin
                        })

                # Fusion et tri alphabétique final
                index_final = sorted(index_actuel + nouvelles_recettes, key=lambda x: x['nom'].lower())
                
                # Envoi du nouvel index
                if envoyer_vers_github("data/index_recettes.json", 
                                       json.dumps(index_final, indent=4, ensure_ascii=False), 
                                       "🛠️ Réparation automatique de l'index"):
                    st.success(f"✅ Terminé ! {len(nouvelles_recettes)} recettes ajoutées.")
                    # Mise à jour de la session globale pour les autres pages
                    st.session_state.index_recettes = index_final
                    del st.session_state.a_reparer
                    st.rerun()
                else:
                    st.error("Erreur lors de la sauvegarde sur GitHub.")
