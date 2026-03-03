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

    # --- LOGIQUE DE FORÇAGE ---
    if 'force_refresh' not in st.session_state:
        st.session_state.force_refresh = False

    conf = config_github()
    
    # On déclenche le chargement si la liste est vide OU si on a cliqué sur actualiser
    if 'toutes_recettes' not in st.session_state or st.session_state.force_refresh:
        with st.spinner("⚡ Synchronisation forcée..."):
            url_dossier = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/data/recettes?t={int(time.time())}"
            res_dossier = requests.get(url_dossier, headers=conf['headers'])
            
            if res_dossier.status_code == 200:
                fichiers_github = res_dossier.json()
                data_recettes = []
                for f in fichiers_github:
                    if f['name'].endswith('.json'):
                        # Utilisation du RAW + SHA pour bypasser tout cache possible
                        raw_url = f"https://raw.githubusercontent.com/{conf['owner']}/{conf['repo']}/main/{f['path']}?v={f['sha']}"
                        res = requests.get(raw_url)
                        if res.status_code == 200:
                            try:
                                d = res.json()
                                d['chemin_json'] = f['path']
                                data_recettes.append(d)
                            except: continue
                st.session_state.toutes_recettes = sorted(data_recettes, key=lambda x: x.get('nom', '').lower())
                st.session_state.force_refresh = False # Reset du flag après succès

    # --- FILTRES ---
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

        # LE BOUTON ACTUALISER (VERSION RÉPARÉE)
        if st.button("🔄 Actualiser la liste des recettes", use_container_width=True):
            st.session_state.force_refresh = True
            # On vide aussi les autres caches pour être sûr
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
            m_edit = f"edit_{idx}"
            if m_edit not in st.session_state: st.session_state[m_edit] = False

            with st.expander(f"📖 {rec.get('nom', 'Sans nom').upper()}"):
                if st.session_state[m_edit]:
                    # --- MODE FORMULAIRE ---
                    with st.form(key=f"f_edit_{idx}"):
                        e_nom = st.text_input("Nom", value=rec.get('nom', ''))
                        e_app = st.selectbox("Appareil", ["Aucun", "Cookeo", "Thermomix", "Ninja"], 
                                           index=["Aucun", "Cookeo", "Thermomix", "Ninja"].index(rec.get('appareil', 'Aucun')))
                        ing_txt = "\n".join([f"{i.get('Quantité', '')} | {i.get('Ingrédient', '')}" for i in rec.get('ingredients', [])])
                        e_ings = st.text_area("Ingrédients (Qté | Nom)", value=ing_txt)
                        e_etapes = st.text_area("Préparation", value=rec.get('etapes', ''), height=150)
                        
                        cs, cc = st.columns(2)
                        if cs.form_submit_button("✅ Enregistrer"):
                            new_ings = []
                            for l in e_ings.strip().split('\n'):
                                if "|" in l:
                                    q, n = l.split("|")
                                    new_ings.append({"Ingrédient": n.strip(), "Quantité": q.strip()})
                                elif l.strip():
                                    new_ings.append({"Ingrédient": l.strip(), "Quantité": ""})
                            
                            data_mod = {"nom": e_nom, "appareil": e_app, "ingredients": new_ings, "etapes": e_etapes, "images": rec.get('images', [])}
                            
                            if envoyer_vers_github(rec['chemin_json'], json.dumps(data_mod, indent=4, ensure_ascii=False), f"Modif: {e_nom}"):
                                st.session_state[m_edit] = False
                                st.session_state.force_refresh = True # On force le prochain chargement
                                st.rerun()
                        
                        if cc.form_submit_button("❌ Annuler"):
                            st.session_state[m_edit] = False
                            st.rerun()
                else:
                    # --- MODE LECTURE ---
                    c_txt, c_img = st.columns([1, 1])
                    with c_txt:
                        st.subheader("🍴 Préparation")
                        st.write(f"**Appareil :** {rec.get('appareil', 'Aucun')}")
                        for i in rec.get('ingredients', []):
                            st.write(f"- {i.get('Quantité', '')} {i.get('Ingrédient', '')}")
                        st.write(f"**Étapes :**\n{rec.get('etapes', '')}")
                        st.divider()
                        b1, b2 = st.columns(2)
                        if b1.button(f"🗑️ Supprimer", key=f"d_{idx}"):
                            if supprimer_fichier_github(rec['chemin_json']):
                                for m in rec.get('images', []): supprimer_fichier_github(m)
                                st.session_state.force_refresh = True
                                st.rerun()
                        if b2.button(f"✍️ Modifier", key=f"e_{idx}"):
                            st.session_state[m_edit] = True
                            st.rerun()
                    
                    with c_img:
                        st.subheader("🖼️ Galerie")
                        medias = rec.get('images', [])
                        if medias:
                            kn = f"n_{idx}"
                            if kn not in st.session_state: st.session_state[kn] = 0
                            cur = st.session_state[kn] % len(medias)
                            if len(medias) > 1:
                                cp, cc, cn = st.columns([1, 1, 1])
                                if cp.button("⬅️", key=f"prev_{idx}"): st.session_state[kn] -= 1; st.rerun()
                                cc.write(f"{cur+1}/{len(medias)}")
                                if cn.button("➡️", key=f"next_{idx}"): st.session_state[kn] += 1; st.rerun()
                            
                            img_path = medias[cur].strip("/")
                            st.image(f"https://raw.githubusercontent.com/{conf['owner']}/{conf['repo']}/main/{img_path if img_path.startswith('data/') else 'data/'+img_path}?t={int(time.time())}", use_container_width=True)
                        else: st.info("Pas d'image.")
