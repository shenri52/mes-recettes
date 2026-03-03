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

    if st.button("🔄 Actualiser la bibliothèque"):
        if 'toutes_recettes' in st.session_state:
            del st.session_state.toutes_recettes
        st.rerun()

    # --- CHARGEMENT ---
    if 'toutes_recettes' not in st.session_state:
        with st.spinner("Lecture de GitHub..."):
            fichiers = charger_fichiers("data/recettes")
            data_recettes = []
            for f in fichiers:
                if f['name'].endswith('.json'):
                    res = requests.get(f['download_url'])
                    if res.status_code == 200:
                        d = res.json()
                        d['chemin_json'] = f['path']
                        data_recettes.append(d)
            st.session_state.toutes_recettes = data_recettes

    # --- FILTRES ---
    col_s, col_a, col_i = st.columns([2, 1, 1])
    recherche = col_s.text_input("🔍 Rechercher un plat", "").lower()
    apps = ["Tous"] + list(set(r.get('appareil', 'Aucun') for r in st.session_state.toutes_recettes))
    filtre_app = col_a.selectbox("Appareil", apps)
    tous_ings = sorted(list(set(i.get('Ingrédient') for r in st.session_state.toutes_recettes for i in r.get('ingredients', []))))
    filtre_ing = col_i.selectbox("Ingrédient", ["Tous"] + tous_ings)

    # Filtrage
    recettes_f = [r for r in st.session_state.toutes_recettes if recherche in r.get('nom', '').lower() 
                  and (filtre_app == "Tous" or r.get('appareil') == filtre_app)
                  and (filtre_ing == "Tous" or any(i.get('Ingrédient') == filtre_ing for i in r.get('ingredients', [])))]

    # --- AFFICHAGE ---
    for idx, rec in enumerate(recettes_f):
        # Utilisation de l'icône appareil dans le titre
        icone = "🍳"
        if rec.get('appareil') == "Cookeo": icone = "🥘"
        elif rec.get('appareil') == "Thermomix": icone = "🥣"
        elif rec.get('appareil') == "Ninja": icone = "🌪️"

        with st.expander(f"{icone} {rec.get('nom', 'Sans nom').upper()}"):
            c1, c2 = st.columns([1, 1])
            
            with c1:
                st.subheader("📝 Détails")
                for i in rec.get('ingredients', []):
                    st.write(f"• {i['Quantité']} {i['Ingrédient']}")
                st.markdown(f"**Préparation :**\n{rec.get('etapes', '...')}")
                
                if st.button(f"🗑️ Supprimer la recette", key=f"del_{idx}"):
                    supprimer_fichier_github(rec['chemin_json'])
                    # On nettoie tous les médias liés
                    m_list = rec.get('images', [])
                    if not m_list and rec.get('image'): m_list = [rec.get('image')]
                    for m in m_list: supprimer_fichier_github(m)
                    
                    if 'toutes_recettes' in st.session_state: del st.session_state.toutes_recettes
                    st.success("Recette supprimée !")
                    st.rerun()

            with c2:
                st.subheader("🖼️ Médias")
                # FORCE LA DÉTECTION DES MÉDIAS (Ancien vs Nouveau format)
                m_bruts = rec.get('images', [])
                if not m_bruts and rec.get('image'):
                    m_bruts = [rec.get('image')]
                
                # Filtrer les valeurs vides ou None
                m_valides = [m for m in m_bruts if m]
                
                if m_valides:
                    nb_m = len(m_valides)
                    # Navigation par index
                    k_idx = f"nav_{idx}"
                    if k_idx not in st.session_state: st.session_state[k_idx] = 0
                    
                    curr = st.session_state[k_idx]
                    
                    if nb_m > 1:
                        col_p, col_c, col_n = st.columns([1, 2, 1])
                        if col_p.button("⬅️", key=f"p_{idx}"):
                            st.session_state[k_idx] = (curr - 1) % nb_m
                            st.rerun()
                        col_c.write(f"Fichier {curr + 1}/{nb_m}")
                        if col_n.button("➡️", key=f"n_{idx}"):
                            st.session_state[k_idx] = (curr + 1) % nb_m
                            st.rerun()
                    
                    # AFFICHAGE DU FICHIER
                    path_to_load = m_valides[curr].strip("/")
                    # Sécurité si "data/" est oublié
                    if not path_to_load.startswith("data"): path_to_load = f"data/{path_to_load}"
                    
                    conf = config_github()
                    url_api = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/{path_to_load}"
                    r_img = requests.get(url_api, headers=conf['headers'])
                    
                    if r_img.status_code == 200:
                        b64 = r_img.json().get('content')
                        if b64:
                            raw_data = base64.b64decode(b64)
                            if path_to_load.lower().endswith('.pdf'):
                                st.download_button("📂 Ouvrir le PDF", raw_data, file_name=f"recette_{idx}.pdf", key=f"btn_pdf_{idx}_{curr}")
                                st.info("Cliquer sur le bouton ci-dessus pour voir le PDF.")
                            else:
                                st.image(raw_data, use_container_width=True)
                        else: st.error("Fichier vide")
                    else:
                        st.error(f"Erreur GitHub {r_img.status_code}")
                        st.caption(f"Chemin testé : {path_to_load}")
                else:
                    st.info("Aucun média trouvé dans cette recette.")
