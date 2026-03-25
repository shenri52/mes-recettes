import streamlit as st
import requests, json, time
from utils import config_github, charger_index, sauvegarder_index

def afficher():
    # --- LOGIQUE DE NETTOYAGE ---
    if not st.session_state.get("bouton_analyse_clique"):
        if "a_reparer" in st.session_state:
            del st.session_state["a_reparer"]
    
    st.session_state.bouton_analyse_clique = False

    # --- SECTION : RÉPARATION DE L'INDEX ---
    if st.button("🔍 Réparer l'index des recettes", use_container_width=True):
        st.session_state.bouton_analyse_clique = True
        st.session_state.bouton_analyse_clique = True
        conf = config_github()
        
        # Récupération de l'arborescence GitHub
        url_tree = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/git/trees/main?recursive=1"
        res = requests.get(url_tree, headers=conf['headers'])
        
        if res.status_code == 200:
            tree = res.json().get('tree', [])
            
            # On cherche uniquement les JSON dans le dossier des recettes
            fichiers_physiques = [
                i['path'] for i in tree 
                if i['path'].startswith('data/recettes/') and i['path'].endswith('.json')
            ]
            
            # On charge l'index actuel
            index_actuel = charger_index()
            chemins_dans_index = {r['chemin'] for r in index_actuel}
            
            # Comparaison
            manquantes = [f for f in fichiers_physiques if f not in chemins_dans_index]
            
            st.write(f"📁 **Fichiers trouvés sur GitHub :** {len(fichiers_physiques)}")
            st.write(f"🗂️ **Recettes dans l'index :** {len(index_actuel)}")
            
            if manquantes:
                st.warning(f"⚠️ {len(manquantes)} fichier(s) ne sont pas listés dans l'index.")
                with st.expander("📄 Liste des fichiers à intégrer"):
                    for m in manquantes:
                        st.write(f"- `{m}`")
                st.session_state.a_reparer = manquantes
            else:
                st.success("✅ L'index est parfaitement à jour.")
        else:
            st.error("Impossible d'accéder à GitHub.")

    # --- ACTION DE RÉPARATION ---
    if st.session_state.get("a_reparer"):
        if st.button("🚀 Lancer la réparation automatique", use_container_width=True):
            with st.spinner("Intégration des recettes..."):
                index_actuel = charger_index()
                nouvelles_entrees = []
                conf = config_github()

                for chemin in st.session_state.a_reparer:
                    # On télécharge le contenu de la recette manquante
                    url_raw = f"https://raw.githubusercontent.com/{conf['owner']}/{conf['repo']}/main/{chemin}"
                    r = requests.get(url_raw)
                    
                    if r.status_code == 200:
                        d = r.json()
                        nouvelles_entrees.append({
                            "nom": d.get("nom", "Sans nom"),
                            "categorie": d.get("categorie", "Non classé"),
                            "appareil": d.get("appareil", "Aucun"),
                            "ingredients": [i.get("Ingrédient") for i in d.get("ingredients", [])],
                            "chemin": chemin
                        })
                
                # Fusion et sauvegarde via la fonction centralisée dans utils.py
                index_final = index_actuel + nouvelles_entrees
                
                if sauvegarder_index(index_final):
                    st.success(f"✅ Réparation terminée : {len(nouvelles_entrees)} recettes ajoutées !")
                    del st.session_state.a_reparer
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("Erreur lors de la sauvegarde de l'index.")
