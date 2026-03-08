import streamlit as st
import requests
import json
import base64
import time

# --- 1. CONFIGURATION TECHNIQUE ---
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
    conf = config_github()
    url = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/{chemin.strip('/')}"
    get_res = requests.get(f"{url}?t={int(time.time())}", headers=conf['headers'])
    if get_res.status_code == 200:
        sha = get_res.json()['sha']
        requests.delete(url, headers=conf['headers'], json={"message": "Suppression", "sha": sha, "branch": "main"})
        return True
    return False

# --- 2. GESTION DE L'INDEX (LE CATALOGUE) ---
def charger_index():
    if 'index_recettes' not in st.session_state:
        conf = config_github()
        url = f"https://raw.githubusercontent.com/{conf['owner']}/{conf['repo']}/main/data/index_recettes.json"
        res = requests.get(url)
        
        if res.status_code == 200:
            st.session_state.index_recettes = res.json()
        else:
            # GÉNÉRATION INITIALE : Si le fichier n'existe pas, on scanne tout une fois
            with st.spinner("Création de l'index (scan des 200 fichiers)..."):
                url_api = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/data/recettes"
                res_api = requests.get(url_api, headers=conf['headers'])
                fichiers = [f for f in res_api.json() if f['name'].endswith('.json')]
                index_neuf = []
                for f in fichiers:
                    r = requests.get(f['download_url']).json()
                    index_neuf.append({
                        "nom": r.get('nom', 'Sans nom'),
                        "categorie": r.get('categorie', 'Non classé'),
                        "appareil": r.get('appareil', 'Aucun'),
                        "ingredients": [i.get('Ingrédient') for i in r.get('ingredients', []) if i.get('Ingrédient')],
                        "chemin": f['path']
                    })
                st.session_state.index_recettes = sorted(index_neuf, key=lambda x: x['nom'].lower())
                # On crée le fichier sur GitHub pour les prochaines fois
                envoyer_vers_github("data/index_recettes.json", json.dumps(st.session_state.index_recettes, indent=4, ensure_ascii=False), "Initialisation Index")
    return st.session_state.index_recettes

def sauvegarder_index_global(index_maj):
    index_trie = sorted(index_maj, key=lambda x: x['nom'].lower())
    if envoyer_vers_github("data/index_recettes.json", json.dumps(index_trie, indent=4, ensure_ascii=False), "Mise à jour Index"):
        st.session_state.index_recettes = index_trie
        return True
    return False

# --- 3. PAGE CONSULTATION & SUPPRESSION ---
def page_consultation():
    index = charger_index()
    st.header("📚 Bibliothèque Rapide")

    # FILTRES (Directement sur l'index)
    c1, c2, c3 = st.columns([2, 1, 1])
    recherche = c1.text_input("🔍 Nom", "").lower()
    f_cat = c2.selectbox("Catégorie", ["Tous"] + sorted(list(set(r['categorie'] for r in index))))
    f_app = c3.selectbox("Appareil", ["Tous"] + sorted(list(set(r['appareil'] for r in index))))

    resultats = [r for r in index if (not recherche or recherche in r['nom'].lower()) 
                 and (f_cat == "Tous" or r['categorie'] == f_cat)
                 and (f_app == "Tous" or r['appareil'] == f_app)]

    noms = [r['nom'].upper() for r in resultats]
    choix = st.selectbox("📖 Sélectionner", ["---"] + noms, key=f"sel_{recherche}_{f_cat}_{f_app}")

    if choix != "---":
        info = resultats[noms.index(choix)]
        # On ne charge le détail que de LA recette sélectionnée
        url_full = f"https://raw.githubusercontent.com/{config_github()['owner']}/{config_github()['repo']}/main/{info['chemin']}"
        recette = requests.get(url_full).json()
        
        st.subheader(recette['nom'].upper())
        st.info(f"📁 {recette.get('categorie')} | 🛠️ {recette.get('appareil')}")
        
        col_l, col_r = st.columns(2)
        with col_l:
            st.write("**Ingrédients :**")
            for i in recette.get('ingredients', []):
                st.write(f"- {i.get('Quantité', '')} {i.get('Ingrédient', '')}")
        with col_r:
            st.write(f"**Instructions :**\n{recette.get('etapes')}")

        st.divider()
        # LA SUPPRESSION EST ICI
        if st.button("🗑️ Supprimer la recette et l'index", use_container_width=True):
            if supprimer_fichier_github(info['chemin']):
                # On nettoie l'index en mémoire et sur GitHub
                nouvel_index = [r for r in index if r['chemin'] != info['chemin']]
                sauvegarder_index_global(nouvel_index)
                st.success("Recette supprimée avec succès !")
                time.sleep(1)
                st.rerun()

# --- 4. PAGE SAISIE / IMPORT (AVEC RESET) ---
def page_saisie():
    st.header("🆕 Ajouter une recette")
    
    # Reset des champs automatique
    keys = ["s_nom", "s_cat", "s_app", "s_ings", "s_steps"]
    for k in keys:
        if k not in st.session_state: st.session_state[k] = ""

    with st.form("form_saisie", clear_on_submit=False):
        nom = st.text_input("Nom", value=st.session_state.s_nom)
        cat = st.text_input("Catégorie", value=st.session_state.s_cat)
        app = st.selectbox("Appareil", ["Aucun", "Cookeo", "Thermomix", "Ninja"])
        ings = st.text_area("Ingrédients (Qté | Nom)", value=st.session_state.s_ings)
        steps = st.text_area("Préparation", value=st.session_state.s_steps)
        
        if st.form_submit_button("🚀 Enregistrer"):
            if nom:
                chemin = f"data/recettes/{nom.replace(' ', '_').lower()}.json"
                liste_ings = [{"Ingrédient": l.split("|")[1].strip(), "Quantité": l.split("|")[0].strip()} if "|" in l else {"Ingrédient": l.strip(), "Quantité": ""} for l in ings.strip().split('\n') if l.strip()]
                
                data_full = {"nom": nom, "categorie": cat, "appareil": app, "ingredients": liste_ings, "etapes": steps, "images": []}
                
                if envoyer_vers_github(chemin, json.dumps(data_full, indent=4, ensure_ascii=False), f"Ajout: {nom}"):
                    # MISE À JOUR DE L'INDEX
                    index = charger_index()
                    index.append({
                        "nom": nom, "categorie": cat, "appareil": app,
                        "ingredients": [i['Ingrédient'] for i in liste_ings],
                        "chemin": chemin
                    })
                    sauvegarder_index_global(index)
                    
                    # RESET DES CHAMPS
                    for k in keys: st.session_state[k] = ""
                    st.success("Recette ajoutée et indexée !")
                    time.sleep(1)
                    st.rerun()

# --- ROUTAGE ---
menu = st.sidebar.radio("Navigation", ["Consulter", "Ajouter"])
if menu == "Consulter": page_consultation()
else: page_saisie()
