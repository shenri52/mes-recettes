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

    # --- BOUTONS DE RÉSULTATS (POUR FORCER LA LISTE) ---
    if filtre_actif:
        if resultats:
            st.write(f"### 📋 {len(resultats)} suggestion(s)")
            for r in resultats:
                nom_r = r['nom'].upper()
                if st.button(f"📖 {nom_r}", key=f"btn_{r['chemin']}", use_container_width=True):
                    st.session_state["select_recette"] = nom_r
                    st.rerun()
        else:
            st.warning("❌ Aucun résultat.")

    st.divider()

    # --- LA LISTE DÉROULANTE (STABLE ET MASTER) ---
    # On met TOUTES les recettes pour éviter que la fiche se ferme en cours de modif
    options = ["---"] + sorted([r['nom'].upper() for r in index])
    
    valeur_actuelle = st.session_state.get("select_recette", "---")
    idx_depart = options.index(valeur_actuelle) if valeur_actuelle in options else 0
    
    choix = st.selectbox(
        "Sélectionner la recette", 
        options,
        index=idx_depart,
        key="choix_recette_gui",
        on_change=nettoyer_modif
    )
    st.session_state["select_recette"] = choix

    # --- AFFICHAGE / MODIFICATION ---
    if choix != "---":
        info = next((r for r in index if r['nom'].upper() == choix), None)
        
        if info:
            conf = config_github()
            url_api = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/{info['chemin']}?t={int(time.time())}"
            res_rec = requests.get(url_api, headers=conf['headers'])
            
            if res_rec.status_code == 200:
                recette = json.loads(base64.b64decode(res_rec.json()['content']).decode('utf-8'))
                m_edit = f"edit_{info['chemin']}"
                
                if m_edit not in st.session_state: st.session_state[m_edit] = False

                if st.session_state[m_edit]:
                    # --- MODE MODIFICATION ---
                    st.subheader("✍️ Modification")
                    state_key = f"ings_list_{info['chemin']}"
                    init_flag = f"init_done_{info['chemin']}"
                    
                    if init_flag not in st.session_state:
                        st.session_state[state_key] = [
                            {"id": str(uuid.uuid4()), "Ingrédient": i.get("Ingrédient", ""), "Quantité": i.get("Quantité", "")}
                            for i in recette.get('ingredients', [])
                        ]
                        st.session_state[init_flag] = True

                    # Gestion des ingrédients
                    rows_to_delete = []
                    for idx, item in enumerate(st.session_state[state_key]):
                        c_q, c_n, c_d = st.columns([1, 2, 0.5])
                        st.session_state[state_key][idx]["Quantité"] = c_q.text_input("Qté", value=item["Quantité"], key=f"q_{item['id']}", label_visibility="collapsed")
                        opts_i = ["--- Choisir ---", "➕ NOUVEL INGRÉDIENT"] + sorted(list(set(liste_ingredients_unique)))
                        def_idx = opts_i.index(item["Ingrédient"]) if item["Ingrédient"] in opts_i else 0
                        sel = c_n.selectbox("Nom", options=opts_i, index=def_idx, key=f"sel_{item['id']}", label_visibility="collapsed")
                        if sel == "➕ NOUVEL INGRÉDIENT":
                            st.session_state[state_key][idx]["Ingrédient"] = c_n.text_input("Nom", value=item["Ingrédient"] if item["Ingrédient"] not in opts_i else "", key=f"new_{item['id']}")
                        else:
                            st.session_state[state_key][idx]["Ingrédient"] = sel if sel != "--- Choisir ---" else ""
                        if c_d.button("🗑️", key=f"del_{item['id']}"): rows_to_delete.append(idx)

                    if rows_to_delete:
                        for r_idx in reversed(rows_to_delete): st.session_state[state_key].pop(r_idx)
                        st.rerun()

                    if st.button("➕ Ajouter un ingrédient"):
                        st.session_state[state_key].append({"id": str(uuid.uuid4()), "Ingrédient": "", "Quantité": ""})
                        st.rerun()

                    with st.form(f"form_edit_{info['chemin']}"):
                        e_nom = st.text_input("Nom", value=recette.get('nom', ''))
                        e_cat = st.selectbox("Catégorie", options=sorted(cats_existantes), index=sorted(cats_existantes).index(recette.get('categorie', 'Non classé')) if recette.get('categorie') in cats_existantes else 0)
                        e_app = st.selectbox("Appareil", ["Aucun", "Cookeo", "Thermomix", "Ninja"], index=["Aucun", "Cookeo", "Thermomix", "Ninja"].index(recette.get('appareil', 'Aucun')))
                        e_pers = st.number_input("Personnes", min_value=1, value=int(recette.get('nb_personnes', 1)))
                        e_prep = st.text_input("Préparation", value=recette.get('temps_preparation', '0'))
                        e_cuis = st.text_input("Cuisson", value=recette.get('temps_cuisson', '0'))
                        e_etapes = st.text_area("Etapes", value=recette.get('etapes', ''), height=150)
                        
                        # Photos
                        photos_actuelles = recette.get('images', [])
                        photos_a_garder = [p for p in photos_actuelles if st.checkbox(f"Garder {p.split('/')[-1]}", value=True, key=f"kp_{p}")]
                        nouvelles = st.file_uploader("Ajouter des photos", accept_multiple_files=True, type=['jpg', 'jpeg', 'png'])

                        c_s, c_c = st.columns(2)
                        if c_s.form_submit_button("💾 Enregistrer", use_container_width=True):
                            if verifier_doublon(e_nom, index, info['chemin']):
                                st.error("Nom déjà pris ! 🛑")
                                st.stop()
                            
                            # Nettoyage et Upload
                            for p in photos_actuelles:
                                if p not in photos_a_garder: supprimer_fichier_github(p)
                            
                            final_pics = photos_a_garder.copy()
                            for f in nouvelles:
                                n_path = f"data/images/{int(time.time())}_{f.name}"
                                if envoyer_vers_github(n_path, compresser_image(f), f"Photo: {e_nom}", est_binaire=True):
                                    final_pics.append(n_path)

                            # Sauvegarde
                            ings = [{"Ingrédient": i["Ingrédient"], "Quantité": i["Quantité"]} for i in st.session_state[state_key] if i["Ingrédient"]]
                            recette_maj = {**recette, "nom": e_nom, "categorie": e_cat, "appareil": e_app, "nb_personnes": e_pers, "temps_preparation": e_prep, "temps_cuisson": e_cuis, "ingredients": ings, "etapes": e_etapes, "images": final_pics}
                            
                            if envoyer_vers_github(info['chemin'], json.dumps(recette_maj, indent=4, ensure_ascii=False), f"MAJ: {e_nom}"):
                                for item in index:
                                    if item['chemin'] == info['chemin']:
                                        item.update({"nom": e_nom, "categorie": e_cat, "appareil": e_app, "ingredients": [i['Ingrédient'] for i in ings]})
                                sauvegarder_index(index)
                                
                                # --- RESET DES CHAMPS ---
                                del st.session_state[state_key]
                                del st.session_state[init_flag]
                                st.session_state[m_edit] = False
                                st.session_state["select_recette"] = e_nom.upper()
                                st.success("Recette enregistrée ! ✨")
                                time.sleep(1)
                                st.rerun()

                        if c_c.form_submit_button("❌ Annuler", use_container_width=True):
                            del st.session_state[state_key]
                            del st.session_state[init_flag]
                            st.session_state[m_edit] = False
                            st.rerun()
                else:
                    # --- AFFICHAGE CLASSIQUE ---
                    st.subheader(f"🍽️ {recette['nom'].upper()}")
                    col_t, col_i = st.columns([1, 1])
                    with col_t:
                        st.write(f"**Catégorie :** {recette.get('categorie', 'Non classé')}")
                        st.write(f"**Appareil :** {recette.get('appareil', 'Aucun')}")
                        st.write(f"👥 **Personnes :** {recette.get('nb_personnes', 0)}")
                        st.write(f"⏱️ **Préparation :** {recette.get('temps_preparation', '0')} | **Cuisson :** {recette.get('temps_cuisson', '0')}")
                        st.markdown("**Ingrédients :**")
                        for i in recette.get('ingredients', []):
                            st.write(f"- {i.get('Quantité', '')} {i.get('Ingrédient', '')}")
                        st.markdown(f"**Etapes :**\n{recette.get('etapes')}")
                    
                    with col_i:
                        imgs = recette.get('images', [])
                        if imgs:
                            if "img_idx" not in st.session_state or st.session_state.img_idx >= len(imgs): st.session_state.img_idx = 0
                            u = f"https://raw.githubusercontent.com/{conf['owner']}/{conf['repo']}/main/{imgs[st.session_state.img_idx].strip('/')}?t={int(time.time())}"
                            st.image(u, use_container_width=True)
                            if len(imgs) > 1:
                                n1, n2, n3 = st.columns([1, 2, 1])
                                if n1.button("◀️"): st.session_state.img_idx = (st.session_state.img_idx - 1) % len(imgs); st.rerun()
                                n2.write(f"<p style='text-align:center'>{st.session_state.img_idx+1}/{len(imgs)}</p>", unsafe_allow_html=True)
                                if n3.button("▶️"): st.session_state.img_idx = (st.session_state.img_idx + 1) % len(imgs); st.rerun()
                        else: st.info("📷 Pas de photo.")

                    if st.session_state.get("authentifie", False):
                        b1, b2 = st.columns(2)
                        if b1.button("🗑️ Supprimer", use_container_width=True):
                            for p in recette.get('images', []): supprimer_fichier_github(p)
                            if supprimer_fichier_github(info['chemin']):
                                idx_n = [r for r in index if r['chemin'] != info['chemin']]
                                sauvegarder_index(idx_n)
                                st.session_state["select_recette"] = "---"
                                st.rerun()
                        if b2.button("✍️ Modifier", use_container_width=True):
                            st.session_state[m_edit] = True
                            st.rerun()
