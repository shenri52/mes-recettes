import streamlit as st
import requests, json, time
from utils import config_github, charger_index, sauvegarder_index

def afficher():
    # --- 1. LOGIQUE DE NETTOYAGE (ANTI-FANTÔME) ---
    # On nettoie si on arrive sur la page, sauf si on vient de cliquer sur "Réparer"
    if "clic_reparation" not in st.session_state:
        if "a_reparer" in st.session_state:
            del st.session_state["a_reparer"]
    else:
        # On consomme le témoin pour que le prochain rafraîchissement (changement de page) nettoie tout
        del st.session_state["clic_reparation"]

    # --- 2. SECTION : ANALYSE ---
    if st.button("🔍 Réparer l'index des recettes", use_container_width=True):
        st.session_state.clic_reparation = True
        conf = config_github()
        
        # Récupération de l'arborescence complète via l'API Tree de GitHub
        url_tree = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/git/trees/main?recursive=1"
        res = requests.get(url_tree, headers=conf['headers'])
        
        if res.status_code == 200:
            tree = res.json().get('tree', [])
            
            # Liste des fichiers JSON réellement présents dans le dossier recettes
            fichiers_physiques = [
                i['path'] for i in tree 
                if i['path'].startswith('data/recettes/') and i['path'].endswith('.json')
            ]
            
            # Chargement de l'index actuel pour comparaison
            index_actuel = charger_index()
            chemins_dans_index = {r['chemin'] for r in index_actuel}
            
            # Identification des fichiers manquants dans l'index
            manquantes = [f for f in fichiers_physiques if f not in chemins_dans_index]

            # --- AFFICHAGE DES STATISTIQUES (BIEN PRÉSENTES) ---
            st.write(f"📁 **Fichiers de recettes trouvés sur GitHub :** {len(fichiers_physiques)}")
            st.write(f"🗂️ **Recettes listées dans l'index :** {len(index_actuel)}")
            
            if manquantes:
                st.warning(f"⚠️ {len(manquantes)} fichier(s) ne sont pas listés dans l'index.")
                # --- EXPANDER (BIEN PRÉSENT) ---
                with st.expander("📄 Voir la liste des fichiers à intégrer"):
                    for m in manquantes:
                        st.write(f"- `{m}`")
                
                # Sauvegarde dans la session pour l'étape suivante
                st.session_state.a_reparer = manquantes
            else:
                st.success("✅ L'index est parfaitement à jour.")
        else:
            st.error("Impossible d'accéder à l'API GitHub pour l'analyse.")

    # --- 3. SECTION : ACTION DE RÉPARATION ---
    if "a_reparer" in st.session_state:
        st.divider()
        if st.button("🚀 Lancer la réparation automatique", use_container_width=True):
            with st.spinner("Récupération des données et fusion de l'index..."):
                idx_actuel = charger_index() # On recharge l'index frais
                nouvelles_entrees = []
                conf = config_github()

                # On boucle sur chaque fichier manquant pour construire son entrée d'index
                for chemin in st.session_state.a_reparer:
                    url_raw = f"https://raw.githubusercontent.com/{conf['owner']}/{conf['repo']}/main/{chemin}"
                    r = requests.get(url_raw)
                    
                    if r.status_code == 200:
                        try:
                            d = r.json()
                            # Extraction des données pour l'index (On ne perd rien !)
                            nouvelles_entrees.append({
                                "nom": d.get("nom", "Sans nom"),
                                "categorie": d.get("categorie", "Non classé"),
                                "appareil": d.get("appareil", "Aucun"),
                                "ingredients": [i.get("Ingrédient") for i in d.get("ingredients", [])],
                                "chemin": chemin
                            })
                        except Exception as e:
                            st.error(f"Erreur de lecture sur {chemin}: {e}")
                
                # FUSION ET SAUVEGARDE (Variables index_final bien définies)
                index_final = idx_actuel + nouvelles_entrees
                
                if sauvegarder_index(index_final):
                    st.success(f"✅ Réparation terminée : {len(nouvelles_entrees)} recettes ajoutées !")
                    # Nettoyage final pour faire disparaître le bouton après succès
                    if "a_reparer" in st.session_state:
                        del st.session_state["a_reparer"]
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("Erreur lors de la sauvegarde de l'index mis à jour.")
