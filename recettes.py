import streamlit as st
import requests
import json
import base64

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

def charger_fichiers(dossier):
    conf = config_github()
    url = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/{dossier}"
    res = requests.get(url, headers=conf['headers'])
    return res.json() if res.status_code == 200 else []

def afficher():
    st.header("📚 Mes recettes")

    # BOUTON RADICAL POUR VIDER LE CACHE
    if st.button("🗑️ Vider le cache et actualiser"):
        st.session_state.clear()
        st.rerun()

    if 'toutes_recettes' not in st.session_state:
        with st.spinner("Chargement..."):
            fichiers = charger_fichiers("data/recettes")
            data_recettes = []
            for f in fichiers:
                if f['name'].endswith('.json'):
                    # On force le téléchargement du contenu frais
                    res = requests.get(f"{f['download_url']}?v={f['sha']}")
                    if res.status_code == 200:
                        d = res.json()
                        d['chemin_json'] = f['path']
                        data_recettes.append(d)
            st.session_state.toutes_recettes = data_recettes

    for idx, rec in enumerate(st.session_state.toutes_recettes):
        with st.expander(f"📖 {rec.get('nom', 'Sans nom')}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Données JSON lues :**")
                # Ceci va nous montrer si 'images' est bien présent dans la mémoire de Streamlit
                st.json(rec) 
            
            with col2:
                st.subheader("Médias")
                
                # Test de présence des clés
                if "images" in rec:
                    st.write(f"✅ Clé 'images' trouvée : {len(rec['images'])} fichier(s)")
                    medias = rec['images']
                elif "image" in rec:
                    st.write("✅ Clé 'image' (ancien format) trouvée")
                    medias = [rec['image']]
                else:
                    st.error("❌ Aucune clé 'image' ou 'images' dans ce JSON")
                    medias = []

                for i, path in enumerate(medias):
                    if not path: continue
                    
                    # Nettoyage et appel API
                    clean_path = path.strip("/")
                    if not clean_path.startswith("data/"): clean_path = f"data/{clean_path}"
                    
                    conf = config_github()
                    api_url = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/{clean_path}"
                    res_m = requests.get(api_url, headers=conf['headers'])
                    
                    if res_m.status_code == 200:
                        img_data = res_m.json().get('content')
                        if img_data:
                            st.image(base64.b64decode(img_data), caption=f"Fichier : {clean_path}")
                        else:
                            st.warning("Contenu GitHub vide")
                    else:
                        st.error(f"Erreur GitHub {res_m.status_code} sur {clean_path}")
