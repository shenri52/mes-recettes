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

def supprimer_fichier_github(chemin):
    if not chemin: return
    conf = config_github()
    url = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/{chemin.strip('/')}"
    get_res = requests.get(url, headers=conf['headers'])
    if get_res.status_code == 200:
        sha = get_res.json()['sha']
        requests.delete(url, headers=conf['headers'], json={"message": "Suppression", "sha": sha, "branch": "main"})

def afficher():
    st.header("📚 Mes recettes")

    if st.button("🔄 Actualiser la liste"):
        if 'toutes_recettes' in st.session_state:
            del st.session_state.toutes_recettes
        st.rerun()

    if 'toutes_recettes' not in st.session_state:
        with st.spinner("Chargement depuis GitHub..."):
            fichiers = charger_fichiers("data/recettes")
            data_recettes = []
            for f in fichiers:
                if f['name'].endswith('.json'):
                    # Utilisation du SHA pour éviter le cache GitHub
                    res = requests.get(f"{f['download_url']}?v={f['sha']}")
                    if res.status_code == 200:
                        d = res.json()
                        d['chemin_json'] = f['path']
                        data_recettes.append(d)
            st.session_state.toutes_recettes = data_recettes

    # --- FILTRES ---
    recherche = st.text_input("🔍 Rechercher un plat", "").lower()
    recettes_f = [r for r in st.session_state.toutes_recettes if recherche in r.get('nom', '').lower()]

    for idx, rec in enumerate(recettes_f):
        with st.expander(f"📖 {rec.get('nom', 'Sans nom').upper()}"):
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.subheader("Détails")
                for i in rec.get('ingredients', []):
                    st.write(f"• {i['Quantité']} {i['Ingrédient']}")
                st.write("**Préparation :**")
                st.write(rec.get('etapes', ""))
                
                if st.button(f"🗑️ Supprimer", key=f"del_{idx}"):
                    supprimer_fichier_github(rec['chemin_json'])
                    for m in rec.get('images', []): supprimer_fichier_github(m)
                    if 'toutes_recettes' in st.session_state: del st.session_state.toutes_recettes
                    st.rerun()

            with col2:
                st.subheader("Médias")
                medias = rec.get('images', [])
                if not medias and rec.get('image'): medias = [rec.get('image')]
                
                if medias:
                    # Index de navigation
                    key_idx = f"nav_{idx}"
                    if key_idx not in st.session_state: st.session_state[key_idx] = 0
                    
                    nb = len(medias)
                    curr = st.session_state[key_idx] % nb
                    
                    if nb > 1:
                        c_p, c_c, c_n = st.columns([1, 2, 1])
                        if c_p.button("⬅️", key=f"p_{idx}"): 
                            st.session_state[key_idx] -= 1
                            st.rerun()
                        c_c.write(f"{curr + 1} / {nb}")
                        if c_n.button("➡️", key=f"n_{idx}"): 
                            st.session_state[key_idx] += 1
                            st.rerun()
                    
                    # Chargement API
                    p = medias[curr].strip("/")
                    if not p.startswith("data/"): p = f"data/{p}"
                    
                    conf = config_github()
                    url_api = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/{p}"
                    r_img = requests.get(url_api, headers=conf['headers'])
                    
                    if r_img.status_code == 200:
                        b64 = r_img.json().get('content')
                        data_img = base64.b64decode(b64)
                        if p.lower().endswith('.pdf'):
                            st.download_button("📂 Ouvrir PDF", data_img, file_name=f"recette_{idx}.pdf", key=f"pdf_{idx}")
                        else:
                            st.image(data_img, use_container_width=True)
                else:
                    st.info("Pas de photo.")
