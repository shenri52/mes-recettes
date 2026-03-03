import streamlit as st
import requests
import json
import base64
import time

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

def envoyer_vers_github(chemin, contenu, message):
    conf = config_github()
    url = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/{chemin}"
    res_get = requests.get(f"{url}?t={int(time.time())}", headers=conf['headers'])
    sha = res_get.json().get('sha') if res_get.status_code == 200 else None
    
    contenu_b64 = base64.b64encode(contenu.encode('utf-8')).decode('utf-8')
    data = {"message": message, "content": contenu_b64, "branch": "main"}
    if sha: data["sha"] = sha
    
    res = requests.put(url, headers=conf['headers'], json=data)
    return res.status_code in [200, 201]

def supprimer_fichier_github(chemin):
    if not chemin: return
    conf = config_github()
    url = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/{chemin.strip('/')}"
    get_res = requests.get(f"{url}?t={int(time.time())}", headers=conf['headers'])
    if get_res.status_code == 200:
        sha = get_res.json()['sha']
        requests.delete(url, headers=conf['headers'], json={"message": "Suppression", "sha": sha, "branch": "main"})
        return True
    return False

def afficher():
    st.header("📚 Mes recettes")

    # --- CHARGEMENT DYNAMIQUE ---
    conf = config_github()
    url_dossier = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/data/recettes?t={int(time.time())}"
    res_dossier = requests.get(url_dossier, headers=conf['headers'])
    
    if res_dossier.status_code == 200:
        fichiers_github = res_dossier.json()
        nb_fichiers_distants = len([f for f in fichiers_github if f['name'].endswith('.json')])
        
        if 'toutes_recettes' not in st.session_state or len(st.session_state.toutes_recettes) != nb_fichiers_distants:
            with st.spinner("🔄 Synchronisation avec GitHub..."):
                data_recettes = []
                for f in fichiers_github:
                    if f['name'].endswith('.json'):
                        res = requests.get(f"{f['download_url']}?v={f['sha']}")
                        if res.status_code == 200:
                            d = res.json()
                            d['chemin_json'] = f['path']
                            data_recettes.append(d)
                st.session_state.toutes_recettes = sorted(data_recettes, key=lambda x: x.get('nom', '').lower())

    # --- RECHERCHE ET FILTRES ---
    if 'toutes_recettes' in st.session_state:
        col_search, col_app, col_ing = st.columns([2, 1, 1])
        recherche = col_search.text_input("🔍 Rechercher un plat", "").lower()
        apps = ["Tous"] + sorted(list(set(r.get('appareil', 'Aucun') for r in st.session_state.toutes_recettes)))
        filtre_app = col_app.selectbox("Appareil", apps)
        
        tous_ingredients = []
        for r in st.session_state.toutes_recettes:
            for i in r.get('ingredients', []):
                if i.get('Ingrédient'): tous_ingredients.append(i.get('Ingrédient'))
        ings = ["Tous"] + sorted(list(set(tous_ingredients)))
        filtre_ing = col_ing.selectbox("Ingrédient", ings)

        # --- BOUTON ACTUALISER (COMME DANS SAISIR) ---
        if st.button("🔄 Actualiser la liste des recettes", use_container_width=True):
            if 'toutes_recettes' in st.session_state: del st.session_state.toutes_recettes
            if 'liste_choix' in st.session_state: del st.session_state.liste_choix
            st.rerun()

        st.divider()

        recettes_f = [
            r for r in st.session_state.toutes_recettes 
            if recherche in r.get('nom', '').lower() 
            and (filtre_app == "Tous" or r.get('appareil') == filtre_app)
            and (filtre_ing == "Tous" or any(i.get('Ingrédient') == filtre_ing for i in r.get('ingredients', [])))
        ]

        # --- AFFICHAGE ---
        for idx, rec in enumerate(recettes_f):
            mode_edit_key = f"mode_edit_{idx}"
            if mode_edit_key not in st.session_state:
                st.session_state[mode_edit_key] = False

            with st.expander(f"📖 {rec.get('nom', 'Sans nom').upper()}"):
                if st.session_state[mode_edit_key]:
                    # --- FORMULAIRE DE MODIFICATION ---
                    with st.form(key=f"form_edit_{idx}"):
                        edit_nom = st.text_input("Nom", value=rec.get('nom', ''))
                        edit_app = st.selectbox("Appareil", ["Aucun", "Cookeo", "Thermomix", "Ninja"], 
                                              index=["Aucun", "Cookeo", "Thermomix", "Ninja"].index(rec.get('appareil', 'Aucun')))
                        
                        ing_text = "\n".join([f"{i.get('Quantité', '')} | {i.get('Ingrédient', '')}" for i in rec.get('ingredients', [])])
                        edit_ings_raw = st.text_area("Ingrédients (Qté | Nom)", value=ing_text)
                        edit_etapes = st.text_area("Préparation", value=rec.get('etapes', ''), height=150)
                        
                        c_save, c_cancel = st.columns(2)
                        if c_save.form_submit_button("✅ Enregistrer"):
                            nouveaux_ings = []
                            for ligne in edit_ings_raw.strip().split('\n'):
                                if "|" in ligne:
                                    q, n = ligne.split("|")
                                    nouveaux_ings.append({"Ingrédient": n.strip(), "Quantité": q.strip()})
                                elif ligne.strip():
                                    nouveaux_ings.append({"Ingrédient": ligne.strip(), "Quantité": ""})
                            
                            rec_modifiee = {
                                "nom": edit_nom, "appareil": edit_app, "ingredients": nouveaux_ings,
                                "etapes": edit_etapes, "images": rec.get('images', [])
                            }
                            
                            if envoyer_vers_github(rec['chemin_json'], json.dumps(rec_modifiee, indent=4, ensure_ascii=False), f"Update {edit_nom}"):
                                st.session_state[mode_edit_key] = False
                                if 'toutes_recettes' in st.session_state: del st.session_state.toutes_recettes
                                if 'liste_choix' in st.session_state: del st.session_state.liste_choix
                                time.sleep(1)
                                st.rerun()
                        
                        if c_cancel.form_submit_button("❌ Annuler"):
                            st.session_state[mode_edit_key] = False
                            st.rerun()
                else:
                    # --- AFFICHAGE CONSULTATION ---
                    col_txt, col_img = st.columns([1, 1])
                    with col_txt:
                        st.subheader("🍴 Préparation")
                        st.write(f"**Appareil :** {rec.get('appareil', 'Non précisé')}")
                        st.write("**Ingrédients :**")
                        for i in rec.get('ingredients', []):
                            st.write(f"- {i.get('Quantité', '')} {i.get('Ingrédient', '')}")
                        st.write("**Préparation :**")
                        st.write(rec.get('etapes', 'Aucune étape rédigée.'))
                        
                        st.divider()
                        c1, c2 = st.columns(2)
                        if c1.button(f"🗑️ Supprimer", key=f"del_{idx}"):
                            with st.spinner("Suppression..."):
                                supprimer_fichier_github(rec['chemin_json'])
                                for m in rec.get('images', []): supprimer_fichier_github(m)
                                if 'toutes_recettes' in st.session_state: del st.session_state.toutes_recettes
                                st.rerun()
                        if c2.button(f"✍️ Modifier", key=f"edit_btn_{idx}"):
                            st.session_state[mode_edit_key] = True
                            st.rerun()

                    with col_img:
                        st.subheader("🖼️ Galerie")
                        medias = rec.get('images', [])
                        if medias:
                            k_nav = f"nav_{idx}"
                            if k_nav not in st.session_state: st.session_state[k_nav] = 0
                            curr = st.session_state[k_nav] % len(medias)
                            if len(medias) > 1:
                                cp, cc, cn = st.columns([1, 2, 1])
                                if cp.button("⬅️", key=f"p_{idx}"): st.session_state[k_nav] -= 1; st.rerun()
                                cc.write(f"{curr + 1}/{len(medias)}")
                                if cn.button("➡️", key=f"n_{idx}"): st.session_state[k_nav] += 1; st.rerun()
                            
                            path = medias[curr].strip("/")
                            url_img = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/{path if path.startswith('data/') else 'data/'+path}?t={int(time.time())}"
                            r_api = requests.get(url_img, headers=conf['headers'])
                            if r_api.status_code == 200:
                                img_b64 = r_api.json().get('content')
                                if img_b64:
                                    img_bytes = base64.b64decode(img_b64)
                                    if path.lower().endswith('.pdf'): st.download_button("📂 PDF", img_bytes, file_name=f"recette.pdf", key=f"pdf_{idx}")
                                    else: st.image(img_bytes, use_container_width=True)
                        else:
                            st.info("Aucun média.")
