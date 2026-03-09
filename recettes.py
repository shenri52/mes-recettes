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
    try:
        conf = config_github()
        url = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/{chemin}"
        res_get = requests.get(f"{url}?t={int(time.time())}", headers=conf['headers'])
        sha = res_get.json().get('sha') if res_get.status_code == 200 else None
        contenu_b64 = base64.b64encode(contenu.encode('utf-8')).decode('utf-8')
        data = {"message": message, "content": contenu_b64, "branch": "main"}
        if sha: data["sha"] = sha
        res = requests.put(url, headers=conf['headers'], json=data)
        if res.status_code not in [200, 201]:
            st.error(f"Erreur GitHub ({res.status_code}): {res.text}")
            return False
        return True
    except Exception as e:
        st.error(f"Erreur technique : {str(e)}")
        return False

def supprimer_fichier_github(chemin):
    conf = config_github()
    url = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/{chemin.strip('/')}"
    get_res = requests.get(f"{url}?t={int(time.time())}", headers=conf['headers'])
    if get_res.status_code == 200:
        sha = get_res.json()['sha']
        res_del = requests.delete(url, headers=conf['headers'], json={"message": "Suppression", "sha": sha, "branch": "main"})
        return res_del.status_code in [200, 204]
    return False

# --- 2. GESTION DE L'INDEX ---
def charger_index():
    if 'index_recettes' not in st.session_state:
        conf = config_github()
        url = f"https://raw.githubusercontent.com/{conf['owner']}/{conf['repo']}/main/data/index_recettes.json"
        res = requests.get(url)
        if res.status_code == 200:
            st.session_state.index_recettes = res.json()
        else:
            st.session_state.index_recettes = []
    return st.session_state.index_recettes

def sauvegarder_index_global(index_maj):
    index_trie = sorted(index_maj, key=lambda x: x['nom'].lower())
    if envoyer_vers_github("data/index_recettes.json", json.dumps(index_trie, indent=4, ensure_ascii=False), "MAJ Index"):
        st.session_state.index_recettes = index_trie
        return True
    return False

# --- 4. CONSULTATION ---
def afficher():
    index = charger_index()
    st.header("📚 Mes recettes")
    st.write("---")

    # FILTRES (4 colonnes d'origine)
    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
    recherche = c1.text_input("🔍 Rechercher", "").lower()
    
    cats_existantes = sorted(list(set(r.get('categorie', 'Non classé') for r in index)))
    cats = ["Tous"] + cats_existantes
    apps = ["Tous"] + sorted(list(set(r.get('appareil', 'Aucun') for r in index)))
    
    tous_ings = []
    for r in index: 
        if r.get('ingredients'): tous_ings.extend(r['ingredients'])
    ings = ["Tous"] + sorted(list(set(tous_ings)))

    f_cat = c2.selectbox("Catégorie", cats)
    f_app = c3.selectbox("🤖 Appareil", apps) # Icône Robot
    f_ing = c4.selectbox("Ingrédient", ings)

    # Filtrage
    resultats = [
        r for r in index 
        if (not recherche or recherche in r['nom'].lower())
        and (f_cat == "Tous" or r['categorie'] == f_cat)
        and (f_app == "Tous" or r['appareil'] == f_app)
        and (f_ing == "Tous" or f_ing in r.get('ingredients', []))
    ]

    noms_filtres = [r['nom'].upper() for r in resultats]
    id_unique = f"sel_{recherche}_{f_cat}_{f_app}_{f_ing}"
    
    st.write("📖 Sélectionner une recette")
    col_liste, col_btn = st.columns([0.9, 0.1])

    with col_liste:
        choix = st.selectbox("📖 Sélectionner une recette", ["---"] + noms_filtres, key=id_unique, label_visibility="collapsed")

    with col_btn:
        if st.button("🔄", help="Actualiser"):
            if 'index_recettes' in st.session_state:
                del st.session_state.index_recettes
            st.rerun()

    st.write("---")

    if choix != "---":
        info = resultats[noms_filtres.index(choix)]
        url_full = f"https://raw.githubusercontent.com/{config_github()['owner']}/{config_github()['repo']}/main/{info['chemin']}"
        recette = requests.get(url_full).json()

        # --- LOGIQUE DE MODIFICATION INTERNE ---
        m_edit = f"edit_{info['chemin']}"
        if m_edit not in st.session_state: st.session_state[m_edit] = False

        if st.session_state[m_edit]:
            with st.form(key=f"f_edit_{info['chemin']}"):
                st.subheader("✍️ Modification")
                e_nom = st.text_input("Nom", value=recette.get('nom', ''))
                
                # Catégorie en liste déroulante
                cat_actuelle = recette.get('categorie', 'Non classé')
                if cat_actuelle not in cats_existantes: cats_existantes.append(cat_actuelle)
                e_cat = st.selectbox("Catégorie", options=sorted(cats_existantes), index=sorted(cats_existantes).index(cat_actuelle))
                
                e_app = st.selectbox("🤖 Appareil", ["Aucun", "Cookeo", "Thermomix", "Ninja"], 
                                   index=["Aucun", "Cookeo", "Thermomix", "Ninja"].index(recette.get('appareil', 'Aucun')))
                
                # --- NOUVELLE GESTION DES INGRÉDIENTS (Style Saisir) ---
                st.write("**Ingrédients**")
                state_key = f"ings_edit_{info['chemin']}"
                if state_key not in st.session_state:
                    st.session_state[state_key] = recette.get('ingredients', [{"Ingrédient": "", "Quantité": ""}])

                new_ingredients = []
                for idx, ing in enumerate(st.session_state[state_key]):
                    col_q, col_n = st.columns([1, 2])
                    q = col_q.text_input(f"Qté", value=ing.get('Quantité', ''), key=f"q_{idx}_{info['chemin']}", label_visibility="collapsed")
                    n = col_n.text_input(f"Nom", value=ing.get('Ingrédient', ''), key=f"n_{idx}_{info['chemin']}", label_visibility="collapsed")
                    new_ingredients.append({"Ingrédient": n, "Quantité": q})

                if st.form_submit_button("➕ Ajouter un ingrédient"):
                    st.session_state[state_key].append({"Ingrédient": "", "Quantité": ""})
                    st.rerun()

                e_etapes = st.text_area("Instructions", value=recette.get('etapes', ''), height=150)
                
                c_save, c_cancel = st.columns(2)
                if c_save.form_submit_button("✅ Enregistrer", use_container_width=True):
                    # Filtrer les ingrédients vides
                    ings_final = [i for i in new_ingredients if i['Ingrédient'].strip()]
                    
                    recette_maj = recette.copy()
                    recette_maj.update({"nom": e_nom, "categorie": e_cat, "appareil": e_app, "ingredients": ings_final, "etapes": e_etapes})
                    
                    if envoyer_vers_github(info['chemin'], json.dumps(recette_maj, indent=4, ensure_ascii=False), f"MAJ: {e_nom}"):
                        for item in index:
                            if item['chemin'] == info['chemin']:
                                item.update({"nom": e_nom, "categorie": e_cat, "appareil": e_app, "ingredients": [i['Ingrédient'] for i in ings_final]})
                        if sauvegarder_index_global(index):
                            if state_key in st.session_state: del st.session_state[state_key]
                            st.session_state[m_edit] = False
                            st.rerun()
                
                if c_cancel.form_submit_button("❌ Annuler", use_container_width=True):
                    if state_key in st.session_state: del st.session_state[state_key]
                    st.session_state[m_edit] = False
                    st.rerun()
        else:
            # --- AFFICHAGE LECTURE ---
            st.subheader(recette['nom'].upper())
            col_t, col_i = st.columns([1, 1])
            with col_t:
                st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
                st.write(f"**Catégorie :** {recette.get('categorie', 'Non classé')}")
                st.write(f"**🤖 Appareil :** {recette.get('appareil', 'Aucun')}")
                st.write("**Ingrédients :**")
                for i in recette.get('ingredients', []):
                    st.write(f"- {i.get('Quantité', '')} {i.get('Ingrédient', '')}")
                st.write(f"**Instructions :**\n{recette.get('etapes')}")
            
            with col_i:
                images = recette.get('images', [])
                if images:
                    if "img_idx" not in st.session_state or st.session_state.get("last_recette") != choix:
                        st.session_state.img_idx = 0
                        st.session_state.last_recette = choix
                    img_url = f"https://raw.githubusercontent.com/{config_github()['owner']}/{config_github()['repo']}/main/{images[st.session_state.img_idx].strip('/')}"
                    st.image(img_url, use_container_width=True)
                    if len(images) > 1:
                        nb_col1, nb_col2, nb_col3 = st.columns([1, 2, 1])
                        if nb_col1.button("⬅️", key="prev_img"):
                            st.session_state.img_idx = (st.session_state.img_idx - 1) % len(images)
                            st.rerun()
                        nb_col2.write(f"{st.session_state.img_idx + 1} / {len(images)}")
                        if nb_col3.button("➡️", key="next_img"):
                            st.session_state.img_idx = (st.session_state.img_idx + 1) % len(images)
                            st.rerun()

            st.divider()
            b1, b2 = st.columns(2)
            if b1.button("🗑️ Supprimer", use_container_width=True):
                if supprimer_fichier_github(info['chemin']):
                    nouvel_index = [r for r in index if r['chemin'] != info['chemin']]
                    if sauvegarder_index_global(nouvel_index):
                        st.rerun()
            
            if b2.button("✍️ Modifier", use_container_width=True):
                st.session_state[m_edit] = True
                st.rerun()
