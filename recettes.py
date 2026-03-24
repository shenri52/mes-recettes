import streamlit as st
import time, uuid
from utils import config_github, envoyer_vers_github, charger_donnees, supprimer_fichier_github, compresser_image, verifier_doublon

# --- 3. GESTION DE L'INDEX ---
def charger_index():
    try:
        data = charger_donnees("data/index_recettes.json")
        st.session_state.index_recettes = data if data else []
    except Exception:
        st.session_state.index_recettes = []
    return st.session_state.index_recettes

def sauvegarder_index_global(chemin_recette, data_recette_maj=None, index_complet=None):
    """Met à jour l'index sur GitHub de manière sécurisée."""
    import requests, base64, json
    conf = config_github()
    url_idx = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/data/index_recettes.json"
    
    try:
        if index_complet is not None:
            index_final = index_complet
        else:
            res = requests.get(url_idx, headers=conf['headers'])
            index_actuel = json.loads(base64.b64decode(res.json()['content']).decode('utf-8')) if res.status_code == 200 else []
            
            index_final = []
            trouve = False
            for item in index_actuel:
                if item['chemin'] == chemin_recette:
                    index_final.append({
                        "nom": data_recette_maj['nom'],
                        "categorie": data_recette_maj['categorie'],
                        "appareil": data_recette_maj['appareil'],
                        "ingredients": [i['Ingrédient'] for i in data_recette_maj['ingredients']],
                        "chemin": chemin_recette
                    })
                    trouve = True
                else:
                    index_final.append(item)
            
            if not trouve:
                index_final.append({
                    "nom": data_recette_maj['nom'],
                    "categorie": data_recette_maj['categorie'],
                    "appareil": data_recette_maj['appareil'],
                    "ingredients": [i['Ingrédient'] for i in data_recette_maj['ingredients']],
                    "chemin": chemin_recette
                })

        index_trie = sorted(index_final, key=lambda x: x['nom'].lower())
        
        if envoyer_vers_github("data/index_recettes.json", index_trie, "🔄 MAJ Index"):
            st.session_state.index_recettes = index_trie
            return True
    except Exception as e:
        st.error(f"Erreur synchro index : {e}")
    return False

# --- 4. LOGIQUE D'AFFICHAGE ET MODIFICATION ---
def afficher():
    def nettoyer_modif():
        if "img_idx" in st.session_state:
            st.session_state.img_idx = 0
        for key in list(st.session_state.keys()):
            if any(key.startswith(p) for p in ["edit_", "init_done_", "ings_list_"]):
                del st.session_state[key]
                
    index = charger_index()
    st.header("📚 Mes recettes")
    st.write("---")

    c2, c3, c4 = st.columns([1, 1, 1])
    cats_existantes = sorted(list(set(r.get('categorie', 'Non classé') for r in index)))
    apps = ["Tous"] + sorted(list(set(r.get('appareil', 'Aucun') for r in index)))
    
    tous_ings_bruts = []
    for r in index: 
        if r.get('ingredients'): tous_ings_bruts.extend(r['ingredients'])
    liste_ingredients_unique = sorted(list(set(tous_ings_bruts)))

    f_cat = c2.selectbox("Catégorie", ["Tous"] + cats_existantes)
    f_app = c3.selectbox("Appareil", apps)
    f_ing = c4.selectbox("Ingrédient", ["Tous"] + liste_ingredients_unique)

    resultats = [
        r for r in index 
        if (f_cat == "Tous" or r['categorie'] == f_cat)
        and (f_app == "Tous" or r['appareil'] == f_app)
        and (f_ing == "Tous" or f_ing in r.get('ingredients', []))
    ]

    noms_filtres = [r['nom'].upper() for r in resultats]

    choix = st.selectbox(
        "📖 Sélectionner une recette", 
        ["---"] + noms_filtres, 
        key="select_recette",
        on_change=nettoyer_modif
    )
    
    if choix != "---":
        info = resultats[noms_filtres.index(choix)]
        conf = config_github()
        recette = charger_donnees(info['chemin'])
        if not recette:
            st.error("Impossible de charger les détails de la recette. 📋")
            st.stop()

        m_edit = f"edit_{info['chemin']}"
        if m_edit not in st.session_state: st.session_state[m_edit] = False

        if st.session_state[m_edit]:
            st.subheader("✍️ Modification")
            state_key = f"ings_list_{info['chemin']}"
            init_flag = f"init_done_{info['chemin']}"
            
            if init_flag not in st.session_state or state_key not in st.session_state:
                st.session_state[state_key] = [
                    {"id": str(uuid.uuid4()), "Ingrédient": i.get("Ingrédient", ""), "Quantité": i.get("Quantité", "")}
                    for i in recette.get('ingredients', [])
                ]
                st.session_state[init_flag] = True

            st.write("**Ingrédients**")
            rows_to_delete = []
            for idx, item in enumerate(st.session_state[state_key]):
                col_q, col_n, col_del = st.columns([1, 2, 0.5])
                st.session_state[state_key][idx]["Quantité"] = col_q.text_input("Qté", value=item["Quantité"], key=f"q_{item['id']}", label_visibility="collapsed")
                
                base_opts = ["--- Choisir ---", "➕ NOUVEL INGRÉDIENT"]
                opts = base_opts + sorted(list(set(liste_ingredients_unique)))
                current_ing = item["Ingrédient"]
                default_index = opts.index(current_ing) if current_ing in opts else 0
                choix_sel = col_n.selectbox("Nom", options=opts, index=default_index, key=f"sel_{item['id']}", label_visibility="collapsed")

                if choix_sel == "➕ NOUVEL INGRÉDIENT":
                    nouveau_nom = col_n.text_input("Nom", value=current_ing if current_ing not in opts else "", key=f"new_{item['id']}", placeholder="Nom...")
                    st.session_state[state_key][idx]["Ingrédient"] = nouveau_nom
                else:
                    st.session_state[state_key][idx]["Ingrédient"] = choix_sel if choix_sel != "--- Choisir ---" else ""
                
                if col_del.button("🗑️", key=f"del_{item['id']}"):
                    rows_to_delete.append(idx)

            if rows_to_delete:
                for r_idx in reversed(rows_to_delete):
                    st.session_state[state_key].pop(r_idx)
                st.rerun()

            if st.button("➕ Ajouter un ingrédient"):
                st.session_state[state_key].append({"id": str(uuid.uuid4()), "Ingrédient": "", "Quantité": ""})
                st.rerun()

            with st.form(f"form_meta_{info['chemin']}"):
                e_nom = st.text_input("Nom", value=recette.get('nom', ''))
                cats_triees = sorted(cats_existantes)
                cat_actuelle = recette.get('categorie', 'Non classé')
                idx_cat = cats_triees.index(cat_actuelle) if cat_actuelle in cats_triees else 0
                
                e_cat = st.selectbox("Catégorie", options=cats_triees, index=idx_cat)
                e_app = st.selectbox("Appareil", ["Aucun", "Cookeo", "Thermomix", "Ninja"], index=["Aucun", "Cookeo", "Thermomix", "Ninja"].index(recette.get('appareil', 'Aucun')))
                e_etapes = st.text_area("Etapes", value=recette.get('etapes', ''), height=150)
                
                photos_actuelles = recette.get('images', [])
                photos_a_garder = []
                for p_path in photos_actuelles:
                    img_url = f"https://raw.githubusercontent.com/{conf['owner']}/{conf['repo']}/main/{p_path.strip('/')}?t={int(time.time())}"
                    col_img, col_check = st.columns([1, 4])
                    col_img.image(img_url, width=60)
                    if col_check.checkbox(f"Garder {p_path.split('/')[-1]}", value=True, key=f"kp_{p_path}"):
                        photos_a_garder.append(p_path)

                nouvelles_photos = st.file_uploader("Ajouter des photos", accept_multiple_files=True, type=['jpg', 'jpeg', 'png'])

                c_save, c_cancel = st.columns(2)
                if c_save.form_submit_button("💾 Enregistrer", use_container_width=True):
                    if verifier_doublon(e_nom, index, info['chemin']):
                        st.error(f"⚠️ Une recette nommée '{e_nom}' existe déjà.")
                        st.stop()

                    for p_path in photos_actuelles:
                        if p_path not in photos_a_garder: supprimer_fichier_github(p_path)
                    
                    final_photos = photos_a_garder.copy()
                    for f in nouvelles_photos:
                        nom_img = f"data/images/{int(time.time())}_{f.name}"
                        img_data = compresser_image(f)
                        if envoyer_vers_github(nom_img, img_data, f"Photo: {e_nom}", est_binaire=True):
                            final_photos.append(nom_img)

                    ings_clean = [{"Ingrédient": i["Ingrédient"], "Quantité": i["Quantité"]} for i in st.session_state[state_key] if i["Ingrédient"]]
                    recette_maj = {"nom": e_nom, "categorie": e_cat, "appareil": e_app, "ingredients": ings_clean, "etapes": e_etapes, "images": final_photos}
                    
                    if envoyer_vers_github(info['chemin'], recette_maj, f"MAJ: {e_nom}"):
                        if sauvegarder_index_global(info['chemin'], recette_maj):
                            st.success("✅ Mis à jour !")
                            for k in [state_key, init_flag, m_edit, "img_idx"]:
                                if k in st.session_state: del st.session_state[k]
                            time.sleep(1)
                            st.rerun()
                    
                if c_cancel.form_submit_button("❌ Annuler", use_container_width=True):
                    for k in [state_key, init_flag]:
                        if k in st.session_state: del st.session_state[k]
                    st.session_state[m_edit] = False
                    st.rerun()
        else:
            st.subheader(recette['nom'].upper())
            col_t, col_i = st.columns([1, 1])
            with col_t:
                st.write(f"**Catégorie :** {recette.get('categorie', 'Non classé')}")
                st.write(f"**Appareil :** {recette.get('appareil', 'Aucun')}")
                st.write("**Ingrédients :**")
                for i in recette.get('ingredients', []):
                    st.write(f"- {i.get('Quantité', '')} {i.get('Ingrédient', '')}")
                st.write(f"**Etapes :**\n{recette.get('etapes')}")
            
            with col_i:
                images = recette.get('images', [])
                if images:
                    if "img_idx" not in st.session_state: st.session_state.img_idx = 0
                    if st.session_state.img_idx >= len(images): st.session_state.img_idx = 0
                    
                    img_url = f"https://raw.githubusercontent.com/{conf['owner']}/{conf['repo']}/main/{images[st.session_state.img_idx].strip('/')}?t={int(time.time())}"
                    st.image(img_url, use_container_width=True)
                    
                    if len(images) > 1:
                        nb1, nb2, nb3 = st.columns([1, 2, 1])
                        if nb1.button("◀️", key="prev"):
                            st.session_state.img_idx = (st.session_state.img_idx - 1) % len(images)
                            st.rerun()
                        nb2.write(f"<p style='text-align:center'>{st.session_state.img_idx + 1}/{len(images)}</p>", unsafe_allow_html=True)
                        if nb3.button("▶️", key="next"):
                            st.session_state.img_idx = (st.session_state.img_idx + 1) % len(images)
                            st.rerun()
                else:
                    st.info("📷 Aucune photo.")

        if st.session_state.get("authentifie", False):
            st.divider()
            b1, b2 = st.columns(2)
            if b1.button("✍️ Modifier", use_container_width=True):
                st.session_state[m_edit] = True
                st.rerun()
            if b2.button("🗑️ Supprimer", use_container_width=True):
                nouvel_index = [r for r in index if r['chemin'] != info['chemin']]
                if supprimer_fichier_github(info['chemin']):
                    for p in recette.get('images', []): supprimer_fichier_github(p)
                    if sauvegarder_index_global(info['chemin'], index_complet=nouvel_index):
                        st.success("Supprimé ! ✨")
                        time.sleep(1)
                        st.rerun()

if __name__ == "__main__":
    afficher()
