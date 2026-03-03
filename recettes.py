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

    # --- CHARGEMENT DES DONNÉES ---
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
    recherche = col_s.text_input("🔍 Rechercher", "").lower()
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
        with st.expander(f"🍴 {rec.get('appareil', 'Cookeo')} - {rec.get('nom', 'Sans nom').upper()}"):
            c1, c2 = st.columns([1, 1])
            
            with c1:
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

            with c2:
                st.subheader("Médias")
                medias = rec.get('images', [])
                if not medias and rec.get('image'): medias = [rec.get('image')]
                
                if medias:
                    # Gestion de l'index de navigation pour chaque recette
                    key_index = f"idx_img_{idx}"
                    if key_index not in st.session_state:
                        st.session_state[key_index] = 0
                    
                    nb_photos = len(medias)
                    current_idx = st.session_state[key_index]
                    
                    # Sélecteurs de déplacement si plusieurs photos
                    if nb_photos > 1:
                        col_prev, col_count, col_next = st.columns([1, 2, 1])
                        if col_prev.button("⬅️", key=f"prev_{idx}"):
                            st.session_state[key_index] = (current_idx - 1) % nb_photos
                            st.rerun()
                        col_count.write(f"Photo {current_idx + 1} / {nb_photos}")
                        if col_next.button("➡️", key=f"next_{idx}"):
                            st.session_state[key_index] = (current_idx + 1) % nb_photos
                            st.rerun()
                    
                    # Affichage du média actuel
                    m_path = medias[current_idx]
                    conf = config_github()
                    api_url = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/{m_path.strip('/')}"
                    res_img = requests.get(api_url, headers=conf['headers'])
                    
                    if res_img.status_code == 200:
                        img_b64 = res_img.json().get('content')
                        if img_b64:
                            data = base64.b64decode(img_b64)
                            if m_path.lower().endswith('.pdf'):
                                st.download_button("📂 Ouvrir le PDF", data, file_name=f"doc_{idx}.pdf", key=f"pdf_btn_{idx}")
                            else:
                                st.image(data, use_container_width=True)
                        else:
                            st.error("Fichier vide")
                    else:
                        st.error(f"Erreur GitHub {res_img.status_code}")
                else:
                    st.info("Aucun média.")
