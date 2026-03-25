import streamlit as st
import requests, json, base64, time, io
from PIL import Image
from utils import config_github, charger_index

def envoyer_vers_github(chemin, contenu, message, est_binaire=False):
    """Version améliorée avec anti-cache sur le SHA et gestion d'erreurs."""
    try:
        conf = config_github()
        url = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/{chemin}"
        
        # 1. Récupération du SHA avec anti-cache pour éviter les conflits
        res_get = requests.get(f"{url}?t={int(time.time())}", headers=conf['headers'])
        sha = res_get.json().get('sha') if res_get.status_code == 200 else None
        
        # 2. Préparation du contenu
        if not est_binaire:
            # Si c'est du texte (ex: JSON), on encode en utf-8
            if isinstance(contenu, (dict, list)):
                contenu_final = json.dumps(contenu, indent=4, ensure_ascii=False).encode('utf-8')
            else:
                contenu_final = contenu.encode('utf-8')
        else:
            contenu_final = contenu

        contenu_b64 = base64.b64encode(contenu_final).decode('utf-8')
        
        # 3. Payload pour GitHub
        data = {
            "message": message,
            "content": contenu_b64,
            "branch": "main"
        }
        if sha: 
            data["sha"] = sha
            
        res = requests.put(url, headers=conf['headers'], json=data)
        return res.status_code in [200, 201]
    except Exception as e:
        st.error(f"Erreur technique API : {str(e)}")

# --- INTERFACE DE MAINTENANCE ---
def afficher():

    if "bouton_analyse_clique" not in st.session_state:
        for key in ["a_reparer", "index_a_sauvegarder"]:
            if key in st.session_state: del st.session_state[key]

    # --- SECTION 1 : SYNCHRONISATION INDEX ---
    if st.button("🔍 Réparer l'index des recettes", use_container_width=True):
        st.session_state.bouton_analyse_clique = True
        conf = config_github()
        res = requests.get(f"https://api.github.com/repos/{st.secrets['REPO_OWNER']}/{st.secrets['REPO_NAME']}/git/trees/main?recursive=1", headers=conf['headers'])
        if res.status_code == 200:
            tree = res.json().get('tree', [])
            exclus = ['data/index_recettes.json', 'data/index_produits_zones.json', 'data/planning.json', 'data/plats_rapides.json']
            physiques = [i['path'] for i in tree if i['path'].startswith('data/') and i['path'].endswith('.json') and i['path'] not in exclus]
            index_actuel = charger_index_local()
            chemins_index = {r['chemin'] for r in index_actuel}
            manquantes = [f for f in physiques if f not in chemins_index]
            st.write(f"📁 **Fichiers /data :** {len(physiques)}")
            st.write(f"🗂️ **Index des recettes :** {len(index_actuel)}")
            if manquantes:
                st.warning(f"⚠️ {len(manquantes)} fichiers hors index.")
                with st.expander("📄 Voir la liste des fichiers manquants"):
                    for m in manquantes:
                        st.write(f"- `{m}`")
                st.session_state.a_reparer = manquantes
            else: st.success("✅ Index à jour.")

    if st.session_state.get("a_reparer"):
        if st.button("🚀 Intégrer les fichiers manquants", use_container_width=True):
            with st.spinner("Analyse..."):
                index_actuel = charger_index_local()
                nouvelles = []
                for chemin in st.session_state.a_reparer:
                    r = requests.get(f"https://raw.githubusercontent.com/{st.secrets['REPO_OWNER']}/{st.secrets['REPO_NAME']}/main/{chemin}")
                    if r.status_code == 200:
                        d = r.json()
                        nouvelles.append({"nom": d.get("nom", "Sans nom"), "categorie": d.get("categorie", "Non classé"), "appareil": d.get("appareil", "Aucun"), "ingredients": [i.get("Ingrédient") for i in d.get("ingredients", [])], "chemin": chemin})
                index_final = sorted(index_actuel + nouvelles, key=lambda x: x['nom'].lower())
                if envoyer_vers_github("data/index_recettes.json", json.dumps(index_final, indent=4, ensure_ascii=False), "🛠️ Réparation"):
                    st.success("✅ Index réparé !")
                    del st.session_state.a_reparer
                    st.rerun()
