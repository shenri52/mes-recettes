import streamlit as st
import requests
import json
import time
from app import config_github, envoyer_vers_github, charger_index

def afficher():
    st.header("🛠️ Réparation de l'index")
    st.write("Ce script compare les fichiers réels sur GitHub avec votre index actuel.")

    if st.button("Lancer la synchronisation"):
        conf = config_github()
        # 1. Récupérer la liste de TOUS les fichiers du dépôt
        url_tree = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/git/trees/main?recursive=1"
        res = requests.get(url_tree, headers=conf['headers'])
        
        if res.status_code == 200:
            tree = res.json().get('tree', [])
            # Filtrer pour n'avoir que les JSON de recettes (exclure l'index lui-même)
            fichiers_gh = [item['path'] for item in tree if item['path'].startswith('data/') 
                          and item['path'].endswith('.json') 
                          and item['path'] != 'data/index_recettes.json']
            
            # 2. Charger l'index actuel
            index_actuel = charger_index()
            chemins_index = [r['chemin'] for r in index_actuel]
            
            # 3. Trouver les manquants
            manquants = [f for f in fichiers_gh if f not in chemins_index]
            
            if not manquants:
                st.success("L'index est déjà à jour. Aucune recette manquante détectée.")
                return

            st.write(f"🔎 {len(manquants)} recette(s) manquante(s) trouvée(s). Ajout en cours...")
            
            nouvelles_entrees = []
            for chemin in manquants:
                # Lire le contenu du fichier manquant
                url_raw = f"https://raw.githubusercontent.com/{conf['owner']}/{conf['repo']}/main/{chemin}"
                res_recette = requests.get(url_raw)
                
                if res_recette.status_code == 200:
                    data = res_recette.json()
                    # Créer l'entrée pour l'index
                    nouvelles_entrees.append({
                        "nom": data.get("nom", "Sans nom"),
                        "categorie": data.get("categorie", "Non classé"),
                        "appareil": data.get("appareil", "Aucun"),
                        "ingredients": [i.get("Ingrédient") for i in data.get("ingredients", [])],
                        "chemin": chemin
                    })
            
            # 4. Fusionner et sauvegarder
            index_final = index_actuel + nouvelles_entrees
            index_final = sorted(index_final, key=lambda x: x['nom'].lower())
            
            if envoyer_vers_github("data/index_recettes.json", 
                                   json.dumps(index_final, indent=4, ensure_ascii=False), 
                                   "Synchronisation automatique de l'index"):
                st.session_state.index_recettes = index_final
                st.success(f"✅ Terminé ! {len(nouvelles_entrees)} recettes ont été ajoutées à l'index.")
                st.rerun()
            else:
                st.error("Erreur lors de la sauvegarde de l'index sur GitHub.")
        else:
            st.error("Impossible de lire la liste des fichiers sur GitHub.")
