import streamlit as st
import requests
import json
import time
# On importe les fonctions nécessaires depuis app.py
from app import config_github, envoyer_vers_github, charger_index

def afficher():
    st.header("🛠️ Diagnostic et Réparation")
    st.write("Ce module vérifie la cohérence entre vos fichiers GitHub et l'index des recettes.")

    # Étape 1 : Analyse
    if st.button("🔍 Analyser l'index"):
        conf = config_github()
        # Récupérer l'arborescence réelle du dépôt
        url_tree = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/git/trees/main?recursive=1"
        res = requests.get(url_tree, headers=conf['headers'])
        
        if res.status_code == 200:
            tree = res.json().get('tree', [])
            # Liste des fichiers JSON dans data/ (exclure l'index)
            fichiers_physiques = [item['path'] for item in tree if item['path'].startswith('data/') 
                                 and item['path'].endswith('.json') 
                                 and item['path'] != 'data/index_recettes.json']
            
            # Charger l'index actuel
            index_actuel = charger_index()
            chemins_index = [r['chemin'] for r in index_actuel]
            
            # Identifier les recettes présentes sur le disque mais pas dans l'index
            manquantes = [f for f in fichiers_physiques if f not in chemins_index]
            
            if manquantes:
                st.warning(f"⚠️ {len(manquantes)} recette(s) trouvée(s) sur GitHub mais absente(s) de l'index.")
                st.write("Voici les fichiers à ajouter :")
                for m in manquantes:
                    st.code(m)
                
                # On stocke la liste dans la session pour l'étape suivante
                st.session_state.recettes_a_reparer = manquantes
            else:
                st.success("✅ Tout est en ordre. L'index correspond parfaitement aux fichiers.")
                if "recettes_a_reparer" in st.session_state:
                    del st.session_state.recettes_a_reparer
        else:
            st.error("Impossible de joindre l'API GitHub pour l'analyse.")

    # Étape 2 : Application (Uniquement si des manquantes ont été trouvées)
    if "recettes_a_reparer" in st.session_state and st.session_state.recettes_a_reparer:
        st.divider()
        st.subheader("Action corrective")
        if st.button("🚀 Appliquer la réparation (Ajouter à l'index)"):
            with st.spinner("Récupération des données et mise à jour..."):
                manquantes = st.session_state.recettes_a_reparer
                index_actuel = charger_index()
                nouvelles_entrees = []
                
                for chemin in manquantes:
                    url_raw = f"https://raw.githubusercontent.com/{config_github()['owner']}/{config_github()['repo']}/main/{chemin}"
                    res_rec = requests.get(url_raw)
                    if res_rec.status_code == 200:
                        data = res_rec.json()
                        nouvelles_entrees.append({
                            "nom": data.get("nom", "Sans nom"),
                            "categorie": data.get("categorie", "Non classé"),
                            "appareil": data.get("appareil", "Aucun"),
                            "ingredients": [i.get("Ingrédient") for i in data.get("ingredients", [])],
                            "chemin": chemin
                        })

                # Fusion et tri
                index_maj = index_actuel + nouvelles_entrees
                index_maj = sorted(index_maj, key=lambda x: x['nom'].lower())
                
                if envoyer_vers_github("data/index_recettes.json", 
                                       json.dumps(index_maj, indent=4, ensure_ascii=False), 
                                       "Réparation manuelle de l'index"):
                    st.session_state.index_recettes = index_maj
                    st.success(f"✅ Index réparé ! {len(nouvelles_entrees)} recettes ajoutées.")
                    del st.session_state.recettes_a_reparer
                    st.rerun()
                else:
                    st.error("Échec de l'envoi de l'index mis à jour.")
