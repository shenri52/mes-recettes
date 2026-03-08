import streamlit as st
import requests
import json
import base64
import time

# --- CONFIGURATION ---
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

# --- FONCTIONS SYNC GITHUB ---
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
    conf = config_github()
    url = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/{chemin.strip('/')}"
    get_res = requests.get(f"{url}?t={int(time.time())}", headers=conf['headers'])
    if get_res.status_code == 200:
        sha = get_res.json()['sha']
        requests.delete(url, headers=conf['headers'], json={"message": "Suppression", "sha": sha, "branch": "main"})
        return True
    return False

# --- PAGE CONSULTATION & MODIFICATION ---
def afficher():
    st.header("📚 Mes recettes")
    conf = config_github()
    
    # ÉCONOMIE DE QUOTA : On liste les fichiers une seule fois
    url_dossier = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/data/recettes?t={int(time.time())}"
    res_dossier = requests.get(url_dossier, headers=conf['headers'])
    
    if res_dossier.status_code == 200:
        jsons_gh = [f for f in res_dossier.json() if f['name'].endswith('.json')]
        
        # On ne télécharge QUE si la mémoire est vide ou si le nombre de fichiers a changé
        if 'toutes_recettes' not in st.session_state or len(st.session_state.toutes_recettes) != len(jsons_gh):
            with st.spinner("Synchronisation des 200 recettes..."):
                data_recettes = []
                for f in jsons_gh:
                    # Utilisation de download_url pour économiser l'API
                    res = requests.get(f['download_url'])
                    if res.status_code == 200:
                        d = res.json()
                        d['chemin_json'] = f['path']
                        data_recettes.append(d)
                st.session_state.toutes_recettes = sorted(data_recettes, key=lambda x: x.get('nom', '').lower())

    if 'toutes_recettes' in st.session_state:
        # FILTRES
        col_search, col_app, col_ing = st.columns([2, 1, 1])
        recherche = col_search.text_input("🔍 Rechercher", "").lower()
        
        apps = ["Tous"] + sorted(list(set(r.get('appareil', 'Aucun') for r in st.session_state.toutes_recettes)))
        filtre_app = col_app.selectbox("Appareil", apps)
        
        tous_ings = []
        for r in st.session_state.toutes_recettes:
            for i in r.get('ingredients', []):
                if i.get('Ingrédient'): tous_ings.append(i.get('Ingrédient'))
        ings = ["Tous"] + sorted(list(set(tous_ings)))
        filtre_ing = col_ing.selectbox("Ingrédient", ings)

        # LISTE FILTRÉE
        recettes_f = [
            r for r in st.session_state.toutes_recettes 
            if (not recherche or recherche in r.get('nom', '').lower()) 
            and (filtre_app == "Tous" or r.get('appareil') == filtre_app)
            and (filtre_ing == "Tous" or any(i.get('Ingrédient') == filtre_ing for i in r.get('ingredients', [])))
        ]

        st.divider()

        # SELECTBOX (Key dynamique pour forcer le refresh si on efface la recherche)
        noms_liste = [r.get('nom', 'SANS NOM').upper() for r in recettes_f]
        id_select = f"sel_{recherche}_{filtre_app}_{filtre_ing}"
        choix = st.selectbox("📖 Sélectionner une recette", ["---"] + noms_liste, key=id_select)

        if choix != "---":
            idx_sel = noms_liste.index(choix)
            rec = recettes_f[idx_sel]
            m_edit = f"edit_{rec['chemin_json']}"
            
            if m_edit not in st.session_state: st.session_state[m_edit] = False

            if st.session_state[m_edit]:
                # --- MODE MODIFICATION ---
                with st.form(key=f"form_{rec['chemin_json']}"):
                    e_nom = st.text_input("Nom", value=rec.get('nom', ''))
                    e_cat = st.text_input("Catégorie", value=rec.get('categorie', ''))
                    c1, c2, c3 = st.columns(3)
                    with c1: e_app = st.selectbox("Appareil", ["Aucun", "Cookeo", "Thermomix", "Ninja"], index=["Aucun", "Cookeo", "Thermomix", "Ninja"].index(rec.get('appareil', 'Aucun')))
                    with c2: e_prep = st.text_input("Prépa", value=rec.get('temps_preparation', ''))
                    with c3: e_cuis = st.text_input("Cuisson", value=rec.get('temps_cuisson', ''))
                    
                    txt_ing = "\n".join([f"{i.get('Quantité', '')} | {i.get('Ingrédient', '')}" for i in rec.get('ingredients', [])])
                    e_ings = st.text_area("Ingrédients (Qté | Nom)", value=txt_ing)
                    e_steps = st.text_area("Préparation", value=rec.get('etapes', ''), height=150)
                    
                    if st.form_submit_button("✅ Enregistrer"):
                        new_ings = [{"Ingrédient": l.split("|")[1].strip(), "Quantité": l.split("|")[0].strip()} if "|" in l else {"Ingrédient": l.strip(), "Quantité": ""} for l in e_ings.strip().split('\n') if l.strip()]
                        data_mod = {
                            "nom": e_nom, "categorie": e_cat, "appareil": e_app, 
                            "temps_preparation": e_prep, "temps_cuisson": e_cuis, 
                            "ingredients": new_ings, "etapes": e_steps, "images": rec.get('images', [])
                        }
                        if envoyer_vers_github(rec['chemin_json'], json.dumps(data_mod, indent=4, ensure_ascii=False), f"Modif: {e_nom}"):
                            # MAJ INSTANTANÉE DU CACHE (Économise le quota)
                            for i, r in enumerate(st.session_state.toutes_recettes):
                                if r['chemin_json'] == rec['chemin_json']:
                                    st.session_state.toutes_recettes[i] = {**data_mod, "chemin_json": rec['chemin_json']}
                            st.session_state[m_edit] = False
                            st.rerun()
            else:
                # --- MODE CONSULTATION ---
                st.subheader(rec.get('nom', '').upper())
                st.info(f"📁 Catégorie : {rec.get('categorie', 'Non classé')}")
                c_txt, c_img = st.columns([1, 1])
                with c_txt:
                    st.write(f"**Appareil :** {rec.get('appareil')}")
                    st.write("**Ingrédients :**")
                    for i in rec.get('ingredients', []): st.write(f"- {i.get('Quantité', '')} {i.get('Ingrédient', '')}")
                    st.write(f"**Instructions :**\n{rec.get('etapes')}")
                with c_img:
                    if rec.get('images'):
                        url_img = f"https://raw.githubusercontent.com/{conf['owner']}/{conf['repo']}/main/{rec['images'][0].strip('/')}?t={int(time.time())}"
                        st.image(url_img, use_container_width=True)
                
                b1, b2 = st.columns(2)
                if b1.button("🗑️ Supprimer"):
                    if supprimer_fichier_github(rec['chemin_json']):
                        st.session_state.toutes_recettes = [r for r in st.session_state.toutes_recettes if r['chemin_json'] != rec['chemin_json']]
                        st.rerun()
                if b2.button("✍️ Modifier"):
                    st.session_state[m_edit] = True
                    st.rerun()

# --- PAGE AJOUT AVEC RESET AUTOMATIQUE ---
def ajouter():
    st.header("🆕 Nouvelle Recette")
    
    # Initialisation session_state pour le reset
    for k in ["n_nom", "n_cat", "n_prep", "n_cuis", "n_ings", "n_steps"]:
        if k not in st.session_state: st.session_state[k] = ""

    with st.form("form_ajout", clear_on_submit=False):
        nom = st.text_input("Nom", value=st.session_state.n_nom)
        cat = st.text_input("Catégorie", value=st.session_state.n_cat)
        app = st.selectbox("Appareil", ["Aucun", "Cookeo", "Thermomix", "Ninja"])
        c1, c2 = st.columns(2)
        prep = c1.text_input("Préparation", value=st.session_state.n_prep)
        cuis = c2.text_input("Cuisson", value=st.session_state.n_cuis)
        ings = st.text_area("Ingrédients (Qté | Nom)", value=st.session_state.n_ings)
        steps = st.text_area("Étapes", value=st.session_state.n_steps)

        if st.form_submit_button("🚀 Enregistrer"):
            if nom:
                new_data = {
                    "nom": nom, "categorie": cat, "appareil": app, 
                    "temps_preparation": prep, "temps_cuisson": cuis, 
                    "ingredients": [{"Ingrédient": l.split("|")[1].strip(), "Quantité": l.split("|")[0].strip()} if "|" in l else {"Ingrédient": l.strip(), "Quantité": ""} for l in ings.strip().split('\n') if l.strip()],
                    "etapes": steps, "images": []
                }
                path = f"data/recettes/{nom.replace(' ', '_').lower()}.json"
                if envoyer_vers_github(path, json.dumps(new_data, indent=4, ensure_ascii=False), f"Ajout: {nom}"):
                    # RESET DES CHAMPS
                    for k in ["n_nom", "n_cat", "n_prep", "n_cuis", "n_ings", "n_steps"]: st.session_state[k] = ""
                    if 'toutes_recettes' in st.session_state: del st.session_state.toutes_recettes
                    st.success("Recette ajoutée !")
                    time.sleep(1)
                    st.rerun()

# --- ROUTAGE ---
if "page" not in st.session_state: st.session_state.page = "consultation"
if st.session_state.page == "consultation": afficher()
else: ajouter()
