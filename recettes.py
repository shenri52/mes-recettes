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

# --- 2. GESTION DE L'INDEX (LE CATALOGUE RAPIDE) ---
def charger_index():
    if 'index_recettes' not in st.session_state:
        conf = config_github()
        # On tente de lire l'index global
        url = f"https://raw.githubusercontent.com/{conf['owner']}/{conf['repo']}/main/data/index_recettes.json"
        res = requests.get(url)
        
        if res.status_code == 200:
            st.session_state.index_recettes = res.json()
        else:
            # GÉNÉRATION INITIALE : Scan des 200 fichiers si l'index n'existe pas
            with st.spinner("Initialisation du catalogue (scan des 200 fichiers)..."):
                url_api = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/data/recettes"
                res_api = requests.get(url_api, headers=conf['headers'])
                if res_api.status_code == 200:
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
                    envoyer_vers_github("data/index_recettes.json", json.dumps(st.session_state.index_recettes, indent=4, ensure_ascii=False), "Initialisation Index")
                else:
                    st.session_state.index_recettes = []
    return st.session_state.index_recettes

def sauvegarder_index_global(index_maj):
    index_trie = sorted(index_maj, key=lambda x: x['nom'].lower())
    if envoyer_vers_github("data/index_recettes.json", json.dumps(index_trie, indent=4, ensure_ascii=False), "MAJ Index"):
        st.session_state.index_recettes = index_trie
        return True
    return False

# --- 3. FONCTION PRINCIPALE (APPELÉE PAR APP.PY) ---
def afficher():
    st.sidebar.title("🍽️ Menu")
    page = st.sidebar.radio("Navigation", ["Consulter", "Ajouter"])

    if page == "Consulter":
        afficher_consultation()
    else:
        afficher_ajout()

# --- 4. PAGES DE CONTENU ---
def afficher_consultation():
    index = charger_index()
    st.header("📚 Mes recettes")

    # --- BOUTON DE FORÇAGE DE L'ACTUALISATION ---
    if st.button("🔄 Actualiser la liste", use_container_width=True):
        # On vide les caches de session pour forcer un nouvel appel GitHub
        if 'index_recettes' in st.session_state:
            del st.session_state.index_recettes
        if 'toutes_recettes' in st.session_state:
            del st.session_state.toutes_recettes
        st.rerun()
    
    st.write("---") # Petite ligne de séparation visuelle
    
    # La suite de ton code (filtres, affichage des cartes, etc.)

    # FILTRES (Ton affichage habituel)
    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
    recherche = c1.text_input("🔍 Rechercher", "").lower()
    
    cats = ["Tous"] + sorted(list(set(r.get('categorie', 'Non classé') for r in index)))
    apps = ["Tous"] + sorted(list(set(r.get('appareil', 'Aucun') for r in index)))
    
    tous_ings = []
    for r in index: 
        if r.get('ingredients'): tous_ings.extend(r['ingredients'])
    ings = ["Tous"] + sorted(list(set(tous_ings)))

    f_cat = c2.selectbox("Catégorie", cats)
    f_app = c3.selectbox("Appareil", apps)
    f_ing = c4.selectbox("Ingrédient", ings)

    # Filtrage sur l'index (instantané)
    resultats = [
        r for r in index 
        if (not recherche or recherche in r['nom'].lower())
        and (f_cat == "Tous" or r['categorie'] == f_cat)
        and (f_app == "Tous" or r['appareil'] == f_app)
        and (f_ing == "Tous" or f_ing in r.get('ingredients', []))
    ]

    noms_filtres = [r['nom'].upper() for r in resultats]
    id_unique = f"sel_{recherche}_{f_cat}_{f_app}_{f_ing}"
    choix = st.selectbox("📖 Sélectionner une recette", ["---"] + noms_filtres, key=id_unique)

    if choix != "---":
        info = resultats[noms_filtres.index(choix)]
        url_full = f"https://raw.githubusercontent.com/{config_github()['owner']}/{config_github()['repo']}/main/{info['chemin']}"
        recette = requests.get(url_full).json()
        
        st.subheader(recette['nom'].upper())
        st.info(f"📁 {recette.get('categorie')} | 🛠️ {recette.get('appareil')}")
        
        col_t, col_i = st.columns([1, 1])
        with col_t:
            st.write("**Ingrédients :**")
            for i in recette.get('ingredients', []):
                st.write(f"- {i.get('Quantité', '')} {i.get('Ingrédient', '')}")
            st.write(f"**Instructions :**\n{recette.get('etapes')}")
        with col_i:
            if recette.get('images'):
                img_url = f"https://raw.githubusercontent.com/{config_github()['owner']}/{config_github()['repo']}/main/{recette['images'][0].strip('/')}"
                st.image(img_url, use_container_width=True)

        st.divider()
        if st.button("🗑️ Supprimer cette recette", use_container_width=True):
            if supprimer_fichier_github(info['chemin']):
                nouvel_index = [r for r in index if r['chemin'] != info['chemin']]
                sauvegarder_index_global(nouvel_index)
                st.success("Supprimé !")
                time.sleep(1)
                st.rerun()

def afficher_ajout():
    st.header("🆕 Ajouter une recette")
    
    # Reset des champs via session_state
    cles = ["s_nom", "s_cat", "s_app", "s_ings", "s_steps"]
    for k in cles:
        if k not in st.session_state: st.session_state[k] = ""

    with st.form("form_saisie", clear_on_submit=False):
        nom = st.text_input("Nom", value=st.session_state.s_nom)
        cat = st.text_input("Catégorie", value=st.session_state.s_cat)
        app = st.selectbox("Appareil", ["Aucun", "Cookeo", "Thermomix", "Ninja"])
        ings_brut = st.text_area("Ingrédients (Qté | Nom)", value=st.session_state.s_ings)
        steps = st.text_area("Préparation", value=st.session_state.s_steps)
        
        if st.form_submit_button("🚀 Enregistrer"):
            if nom:
                chemin = f"data/recettes/{nom.replace(' ', '_').lower()}.json"
                liste_ings = [{"Ingrédient": l.split("|")[1].strip(), "Quantité": l.split("|")[0].strip()} if "|" in l else {"Ingrédient": l.strip(), "Quantité": ""} for l in ings_brut.strip().split('\n') if l.strip()]
                
                data_full = {"nom": nom, "categorie": cat, "appareil": app, "ingredients": liste_ings, "etapes": steps, "images": []}
                
                if envoyer_vers_github(chemin, json.dumps(data_full, indent=4, ensure_ascii=False), f"Ajout: {nom}"):
                    index = charger_index()
                    index.append({
                        "nom": nom, "categorie": cat, "appareil": app,
                        "ingredients": [i['Ingrédient'] for i in liste_ings],
                        "chemin": chemin
                    })
                    sauvegarder_index_global(index)
                    # Reset pour la prochaine saisie
                    for k in cles: st.session_state[k] = ""
                    st.success("Ajouté et Indexé !")
                    time.sleep(1)
                    st.rerun()
