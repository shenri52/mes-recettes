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

    # BOUTON DE NETTOYAGE TOTAL
    if st.button("🧨 Réinitialiser et Forcer la mise à jour"):
        st.session_state.clear()
        st.rerun()

    # --- CHARGEMENT ---
    if 'toutes_recettes' not in st.session_state:
        with st.spinner("Lecture forcée de GitHub..."):
            fichiers = charger_fichiers("data/recettes")
            data_recettes = []
            for f in fichiers:
                if f['name'].endswith('.json'):
                    # L'astuce du '?nocache' avec le SHA du fichier force GitHub à donner le vrai contenu
                    res = requests.get(f"{f['download_url']}?nocache={f['sha']}")
                    if res.status_code == 200:
                        d = res.json()
                        d['chemin_json'] = f['path']
                        data_recettes.append(d)
            st.session_state.toutes_recettes = data_recettes

    # --- RECHERCHE ---
    recherche = st.text_input("🔍 Rechercher un plat", "").lower()
    recettes_f = [r for r in st.session_state.toutes_recettes if recherche in r.get('nom', '').lower()]

    for idx, rec in enumerate(recettes_f):
        with st.expander(f"📖 {rec.get('nom', 'Sans nom').upper()}"):
            col_txt, col_img = st.columns([1, 1])
            
            with col_txt:
                st.write("**Ingrédients :**")
                for i in rec.get('ingredients', []):
                    st.write(f"- {i['Quantité']} {i['Ingrédient']}")
                
                # DEBUG : Affiche ce que le code voit réellement dans le JSON
                if st.checkbox("Voir structure JSON (Debug)", key=f"debug_{idx}"):
                    st.json(rec)

            with col_img:
                st.subheader("Médias")
                
                # On essaie de récupérer 'images' (nouveau) ou 'image' (ancien)
                medias = rec.get('images', [])
                if not medias and rec.get('image'):
                    medias = [rec.get('image')]
                
                if medias and isinstance(medias, list):
                    # Système de navigation
                    k_nav = f"nav_{idx}"
                    if k_nav not in st.session_state: st.session_state[k_nav] = 0
                    curr = st.session_state[k_nav] % len(medias)
                    
                    if len(medias) > 1:
                        c_p, c_c, c_n = st.columns([1, 2, 1])
                        if c_p.button("⬅️", key=f"p_{idx}"): st.session_state[k_nav] -= 1; st.rerun()
                        c_c.write(f"{curr + 1}/{len(medias)}")
                        if c_n.button("➡️", key=f"n_{idx}"): st.session_state[k_nav] += 1; st.rerun()
                    
                    # Chargement de l'image via l'API (plus fiable que l'URL directe)
                    path = medias[curr].strip("/")
                    if not path.startswith("data/"): path = f"data/{path}"
                    
                    conf = config_github()
                    api_url = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/{path}"
                    r_api = requests.get(api_url, headers=conf['headers'])
                    
                    if r_api.status_code == 200:
                        img_b64 = r_api.json().get('content')
                        if img_b64:
                            img_bytes = base64.b64decode(img_b64)
                            if path.lower().endswith('.pdf'):
                                st.download_button("📂 Voir le PDF", img_bytes, file_name="doc.pdf", key=f"pdf_{idx}")
                            else:
                                st.image(img_bytes, use_container_width=True)
                    else:
                        st.error(f"GitHub Error {r_api.status_code}")
                else:
                    st.warning("Aucun média détecté dans le JSON.")
