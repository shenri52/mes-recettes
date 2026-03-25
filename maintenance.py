import streamlit as st
import requests, json, time
from utils import config_github, charger_index, sauvegarder_index

def afficher():
    # --- LOGIQUE DE NETTOYAGE STRICTE ---
    # Si on charge la page normalement (sans avoir cliqué sur le bouton à l'instant T)
    # On vide la liste des fichiers à réparer.
    if "clic_reparation" not in st.session_state:
        if "a_reparer" in st.session_state:
            del st.session_state["a_reparer"]
    else:
        # On supprime le témoin de clic pour que le prochain changement de page nettoie tout
        del st.session_state["clic_reparation"]

    # --- SECTION : ANALYSE ---
    if st.button("🔍 Réparer l'index des recettes", use_container_width=True):
        # On pose un témoin de clic temporaire
        st.session_state.clic_reparation = True
        
        conf = config_github()
        res = requests.get(f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/git/trees/main?recursive=1", headers=conf['headers'])
        
        if res.status_code == 200:
            tree = res.json().get('tree', [])
            fichiers_physiques = [i['path'] for i in tree if i['path'].startswith('data/recettes/') and i['path'].endswith('.json')]
            index_actuel = charger_index()
            chemins_index = {r['chemin'] for r in index_actuel}
            
            manquantes = [f for f in fichiers_physiques if f not in chemins_index]

            st.write(f"📁 **Fichiers de recettes :** {len(physiques)}")
            st.write(f"🗂️ **Recettes dans l'index :** {len(index_actuel)}")
            
            if manquantes:
                st.warning(f"⚠️ {len(manquantes)} fichiers hors index.")
                with st.expander("📄 Voir la liste des fichiers manquants"):
                    for m in manquantes:
                        st.write(f"- `{m}`")
                st.session_state.a_reparer = manquantes
            else:
                st.success("✅ Index à jour.")
        else:
            st.error("Erreur de connexion GitHub")

    # --- SECTION : ACTION (Le bouton qui doit disparaître) ---
    if "a_reparer" in st.session_state:
        st.divider()
        if st.button("🚀 Lancer la réparation automatique", use_container_width=True):
            # ... (Ta logique de boucle for et sauvegarder_index ici) ...
            # Une fois fini :
            if sauvegarder_index(index_final):
                st.success("✅ Réparé !")
                del st.session_state["a_reparer"]
                time.sleep(1)
                st.rerun()
