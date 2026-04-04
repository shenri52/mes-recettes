import streamlit as st
import requests, json, base64, time, uuid
from utils import config_github, charger_index, sauvegarder_index, verifier_doublon, envoyer_vers_github, compresser_image, supprimer_fichier_github

# --- 3. LOGIQUE D'AFFICHAGE ET MODIFICATION ---
def afficher():        
    def nettoyer_modif():
        """Supprime les données temporaires d'édition quand on change de recette."""
        if "img_idx" in st.session_state:
            st.session_state.img_idx = 0
        for key in list(st.session_state.keys()):
            if any(key.startswith(p) for p in ["edit_", "init_done_", "ings_list_"]):
                if key in st.session_state:
                    del st.session_state[key]
                
    index = charger_index()

    # --- FILTRAGE ---
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

    filtre_actif = (f_cat != "Tous" or f_app != "Tous" or f_ing != "Tous")

    resultats = [
        r for r in index 
        if (f_cat == "Tous" or r.get('categorie') == f_cat)
        and (f_app == "Tous" or r.get('appareil') == f_app)
        and (f_ing == "Tous" or f_ing in r.get('ingredients', []))
    ]

    # --- AFFICHAGE DES BOUTONS RÉSULTATS ---
    if filtre_actif:
        if resultats:
            st.write(f"### 📋 {len(resultats)} recette(s) trouvée(s)")
            # On affiche les boutons en colonnes pour gagner de la place
            for r in resultats:
                if st.button(f"📖 {r['nom'].upper()}", key=f"btn_{r['chemin']}", use_container_width=True):
                    st.session_state["select_recette"] = r['nom'].upper()
                    st.rerun()
        else:
            st.warning("❌ Aucune recette ne correspond.")

    st.divider()

    # --- LISTE DÉROULANTE (MASTER) ---
    # On garde TOUJOURS toutes les recettes ici pour que Streamlit ne "perde" pas la recette pendant l'édition
    options = ["---"] + sorted([r['nom'].upper() for r in index])
    
    valeur_actuelle = st.session_state.get("select_recette", "---")
    idx_depart = options.index(valeur_actuelle) if valeur_actuelle in options else 0
    
    choix = st.selectbox(
        "Rechercher ou sélectionner une recette", 
        options,
        index=idx_depart,
        key="choix_recette_gui",
        on_change=nettoyer_modif
    )
    st.session_state["select_recette"] = choix

    # --- AFFICHAGE DE LA FICHE ---
    if choix != "---":
        info = next((r for r in index if r['nom'].upper() == choix), None)
        
        if info:
            conf = config_github()
            url_api = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/{info['chemin']}?t={int(time.time())}"
            res_rec = requests.get(url_api, headers=conf['headers'])
            
            if res_rec.status_code == 200:
                contenu_b64 = res_rec.json()['content']
                recette = json.loads(base64.b64decode(contenu_b64).decode('utf-8'))
                
                m_edit = f"edit_{info['chemin']}"
                if m_edit not in st.session_state: st.session_state[m_edit] = False

                # --- MODE ÉDITION ---
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

                    # (Le reste du code de modification est identique à ton original)
                    st.write("**Ingrédients**")
                    rows_to_delete = []
                    for idx, item in enumerate(st.session_state[state_key]):
                        col_q, col_n, col_del = st.columns([1, 2, 0.5])
                        st.session_state[state_key][idx]["Quantité"] = col_q.text_input("Qté", value=item["Quantité"], key=f"q_{item['id']}", label_visibility="collapsed")
                        opts_ing = ["--- Choisir ---", "➕ NOUVEL INGRÉDIENT"] + sorted(list(set(liste_ingredients_unique)))
                        def_idx = opts_ing.index(item["Ingrédient"]) if item["Ingrédient"] in opts_ing else 0
                        choix_sel = col_n.selectbox("Nom", options=opts_ing, index=def_idx, key=f"sel_{item['id']}", label_visibility="collapsed")
                        if choix_sel == "➕ NOUVEL INGRÉDIENT":
                            nouveau = col_n.text_input("Nom", value=item["Ingrédient"] if item["Ingrédient"] not in opts_ing else "", key=f"new_{item['id']}")
                            st.session_state[state_key][idx]["Ingrédient"] = nouveau
                        else:
                            st.session_state[state_key][idx]["Ingrédient"] = choix_sel if choix_sel != "--- Choisir ---" else ""
                        if col_del.button("🗑️", key=f"del_{item['id']}"): rows_to_delete.append(idx)

                    if rows_to_delete:
                        for r_idx in reversed(rows_to_delete): st.session_state[state_key].pop(r_idx)
                        st.rerun()

                    if st.button("➕ Ajouter un ingrédient"):
                        st.session_state[state_key].append({"id": str(uuid.uuid4()), "Ingrédient": "", "Quantité": ""})
                        st.rerun()

                    with st.form(f"form_meta_{info['chemin']}"):
                        e_nom = st.text_input("Nom", value=recette.get('nom', ''))
                        e_cat = st.selectbox("Catégorie", options=sorted(cats_existantes), index=sorted(cats_existantes).index(recette.get('categorie', 'Non classé')) if recette.get('categorie') in cats_existantes else 0)
                        e_app = st.selectbox("Appareil", ["Aucun", "Cookeo", "Thermomix", "Ninja"], index=["Aucun", "Cookeo", "Thermomix", "Ninja"].index(recette.get('appareil', 'Aucun')))
                        e_pers = st.number_input("Nombre de personnes", min_value=1, value=int(recette.get('nb_personnes', 1)))
                        e_prep = st.text_input("Préparation", value=recette.get('temps_preparation', '0'))
                        e_cuis = st.text_input("Cuisson", value=recette.get('temps_cuisson', '0'))
                        e_etapes = st.text_area("Etapes", value=recette.get('etapes', ''), height=150)
                        
                        # Photos
                        photos_actuelles = recette.get('images', [])
                        photos_a_garder = []
                        for p_path in photos_actuelles:
                            img_url = f"https://raw.githubusercontent.com/{conf['owner']}/{conf['repo']}/main/{p_path.strip('/')}?t={int(time.time())}"
                            c_img, c_chk = st.columns([1, 4])
                            c_img.image(img_url, width=60)
                            if c_chk.checkbox(f"Garder {p_path.split('/')[-1]}", value=True, key=f"kp_{p_path}"):
                                photos_a_garder.append(p_path)

                        nouvelles_photos = st.file_uploader("Ajouter des photos", accept_multiple_files=True, type=['jpg', 'jpeg', 'png'])

                        c_save, c_cancel = st.columns(2)
                        if c_save.form_submit_button("💾 Enregistrer", use_container_width=True):
                            if verifier_doublon(e_nom, index, info['chemin']):
                                st.error("Nom déjà utilisé.")
                                st.stop()
                            for p_path in photos_actuelles:
                                if p_path not in photos_a_garder: supprimer_fichier_github(p_path)
                            final_photos = photos_a_garder.copy()
                            for f in nouvelles_photos:
                                nom_img = f"data/images/{int(time.time())}_{f.name}"
                                if envoyer_vers_github(nom_img, compresser_image(f), f"Photo: {e_nom}", est_binaire=True):
                                    final_photos.append(nom_img)
                            ings_clean = [{"Ingrédient": i["Ingrédient"], "Quantité": i["Quantité"]} for i in st.session_state[state_key] if i["Ingrédient"]]
                            recette_maj = {**recette, "nom": e_nom, "categorie": e_cat, "appareil": e_app, "nb_personnes": e_pers, "temps_preparation": e_prep, "temps_cuisson": e_cuis, "ingredients": ings_clean, "etapes": e_etapes, "images": final_photos}
                            if envoyer_vers_github(info['chemin'], json.dumps(recette_maj, indent=4, ensure_ascii=False), f"MAJ: {e_nom}"):
                                for item in index:
                                    if item['chemin'] == info['chemin']:
                                        item.update({"nom": e_nom, "categorie": e_cat, "appareil": e_app, "ingredients": [i['Ingrédient'] for i in ings_clean]})
                                sauvegarder_index(index)
                                # RESET
                                if state_key in st.session_state: del st.session_state[state_key]
                                if init_flag in st.session_state: del st.session_state[init_flag]
                                st.session_state[m_edit] = False
                                st.session_state["select_recette"] = e_nom.upper()
                                st.rerun()

                        if c_cancel.form_submit_button("❌ Annuler", use_container_width=True):
                            if state_key in st.session_state: del st.session_state[state_key]
                            if init_flag in st.session_state: del st.session_state[init_flag]
                            st.session_state[m_edit] = False
                            st.rerun()
                else:
                    # --- AFFICHAGE CLASSIQUE ---
                    st.subheader(recette['nom'].upper())
                    col_t, col_i = st.columns([1, 1])
                    with col_t:
                        st.write(f"**Catégorie :** {recette.get('categorie', 'Non classé')}")
                        st.write(f"**Appareil :** {recette.get('appareil', 'Aucun')}")
                        st.write(f"👥**Personnes :** {recette.get('nb_personnes', 0)}")
                        st.write(f"**Préparation :** {recette.get('temps_preparation', '0')} | **Cuisson :** {recette.get('temps_cuisson', '0')} ⏱️")
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
                                nb2.write(f"<p style='text-align:center'>{st.session_state.img_idx + 1} / {len(images)}</p>", unsafe_allow_html=True)
                                if nb3.button("▶️", key="next"):
                                    st.session_state.img_idx = (st.session_state.img_idx + 1) % len(images)
                                    st.rerun()
                        else: st.info("📷 Aucune photo.")

                    if st.session_state.get("authentifie", False):
                        b1, b2 = st.columns(2)
                        if b1.button("🗑️ Supprimer", use_container_width=True):
                            for p in recette.get('images', []): supprimer_fichier_github(p)
                            if supprimer_fichier_github(info['chemin']):
                                index = [r for r in index if r['chemin'] != info['chemin']]
                                sauvegarder_index(index)
                                del st.session_state["select_recette"]
                                st.rerun()
                        if b2.button("✍️ Modifier", use_container_width=True):
                            st.session_state[m_edit] = True
                            st.rerun()
                    else:
                        import urllib.parse
                        msg = urllib.parse.quote(f"Regarde cette recette : {info['nom'].upper()} 🍽️\n🔗 https://mon-catalogue-de-recettes.streamlit.app/?recette={urllib.parse.quote(info['nom'].upper())}")
                        st.markdown(f'<a href="sms:?&body={msg}" style="text-decoration:none;"><div style="background-color:#4CAF50;color:white;padding:10px;text-align:center;border-radius:8px;font-weight:bold;">📲 Partager par SMS</div></a>', unsafe_allow_html=True)
