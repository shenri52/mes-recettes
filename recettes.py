import streamlit as st
import json
import time
import uuid
import requests
from utils import get_github_config, charger_json_github, envoyer_donnees_github, supprimer_fichier_github, traiter_et_compresser_image, charger_recette_specifique

# --- 4. LOGIQUE D'AFFICHAGE ET MODIFICATION ---
def afficher():
    def nettoyer_modif():
        """Supprime les données temporaires d'édition quand on change de recette."""
        if "img_idx" in st.session_state:
            st.session_state.img_idx = 0
        for key in list(st.session_state.keys()):
            if any(key.startswith(p) for p in ["edit_", "init_done_", "ings_list_"]):
                del st.session_state[key]
                
    index = charger_json_github("data/index_recettes.json")

    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
    recherche = c1.text_input("🔍 Rechercher", "").lower()
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
        if (not recherche or recherche in r['nom'].lower())
        and (f_cat == "Tous" or r['categorie'] == f_cat)
        and (f_app == "Tous" or r['appareil'] == f_app)
        and (f_ing == "Tous" or f_ing in r.get('ingredients', []))
    ]

    noms_filtres = [r['nom'].upper() for r in resultats]

    if "menu_key" not in st.session_state:
        st.session_state.menu_key = 0
        
    choix = st.selectbox(
        "📖 Sélectionner une recette", 
        ["---"] + noms_filtres, 
        key=f"menu_sel_{st.session_state.menu_key}", # Clé qui change pour reset
        on_change=nettoyer_modif 
    )
    
    if choix != "---":
        info = resultats[noms_filtres.index(choix)]
        conf = get_github_config()
        url_full = f"https://raw.githubusercontent.com/{conf['owner']}/{conf['repo']}/main/{info['chemin']}?t={int(time.time())}"
        recette = charger_recette_specifique(url_full)

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
            if state_key in st.session_state:
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
                e_cat = st.selectbox("Catégorie", options=sorted(cats_existantes), index=sorted(cats_existantes).index(recette.get('categorie', 'Non classé')))
                e_app = st.selectbox("Appareil", ["Aucun", "Cookeo", "Thermomix", "Ninja"], index=["Aucun", "Cookeo", "Thermomix", "Ninja"].index(recette.get('appareil', 'Aucun')))
                e_etapes = st.text_area("Instructions", value=recette.get('etapes', ''), height=150)
                
                photos_actuelles = recette.get('images', [])
                photos_a_garder = []
                for p_path in photos_actuelles:
                    img_url = f"https://raw.githubusercontent.com/{conf['owner']}/{conf['repo']}/main/{p_path.strip('/')}"
                    col_img, col_check = st.columns([1, 4])
                    col_img.image(img_url, width=60)
                    if col_check.checkbox(f"Garder {p_path.split('/')[-1]}", value=True, key=f"kp_{p_path}"):
                        photos_a_garder.append(p_path)

                nouvelles_photos = st.file_uploader("Ajouter des photos", accept_multiple_files=True, type=['jpg', 'jpeg', 'png'])

                c_save, c_cancel = st.columns(2)
                if c_save.form_submit_button("💾 Enregistrer", use_container_width=True):
                    for p_path in photos_actuelles:
                        if p_path not in photos_a_garder: supprimer_fichier_github(p_path)
                    
                    final_photos = photos_a_garder.copy()
                    for f in nouvelles_photos:
                        nom_img = f"data/images/{int(time.time())}_{f.name}"
                        img_data, _ = traiter_et_compresser_image(f)
                        if envoyer_donnees_github(nom_img, img_data, f"Photo: {e_nom}", est_image=True):
                            final_photos.append(nom_img)

                    ings_clean = [{"Ingrédient": i["Ingrédient"], "Quantité": i["Quantité"]} for i in st.session_state[state_key] if i["Ingrédient"]]
                    recette_maj = recette.copy()
                    recette_maj.update({"nom": e_nom, "categorie": e_cat, "appareil": e_app, "ingredients": ings_clean, "etapes": e_etapes, "images": final_photos})
                    
                    if envoyer_donnees_github(info['chemin'], json.dumps(recette_maj, indent=4, ensure_ascii=False), f"MAJ: {e_nom}"):
                        for item in index:
                            if item['chemin'] == info['chemin']:
                                item.update({"nom": e_nom, "categorie": e_cat, "appareil": e_app, "ingredients": [i['Ingrédient'] for i in ings_clean]})
                        envoyer_donnees_github("data/index_recettes.json", json.dumps(index, indent=4, ensure_ascii=False), "MAJ Index")
                        
                        if state_key in st.session_state: del st.session_state[state_key]
                        if init_flag in st.session_state: del st.session_state[init_flag]
                        st.session_state[m_edit] = False
                        st.rerun()

                if c_cancel.form_submit_button("❌ Annuler", use_container_width=True):
                    if state_key in st.session_state: del st.session_state[state_key]
                    if init_flag in st.session_state: del st.session_state[init_flag]
                    st.session_state[m_edit] = False
                    st.rerun()
        else:
            # --- AFFICHAGE CLASSIQUE AVEC NAVIGATION PHOTO ---
            st.subheader(recette['nom'].upper())
            col_t, col_i = st.columns([1, 1])
            with col_t:
                st.write(f"**Catégorie :** {recette.get('categorie', 'Non classé')}")
                st.write(f"**Appareil :** {recette.get('appareil', 'Aucun')}")
                st.write("**Ingrédients :**")
                for i in recette.get('ingredients', []):
                    st.write(f"- {i.get('Quantité', '')} {i.get('Ingrédient', '')}")
                st.write(f"**Instructions :**\n{recette.get('etapes')}")
            
            with col_i:
                images = recette.get('images', [])
                if images:
                    # 1. Initialisation de l'index
                    if "img_idx" not in st.session_state:
                        st.session_state.img_idx = 0
                    
                    # Sécurité : on s'assure que l'index ne dépasse pas le nombre d'images
                    if st.session_state.img_idx >= len(images):
                        st.session_state.img_idx = 0
                    
                    # 2. Affichage de la photo actuelle
                    conf = get_github_config()
                    img_url = f"https://raw.githubusercontent.com/{conf['owner']}/{conf['repo']}/main/{images[st.session_state.img_idx].strip('/')}?t={int(time.time())}"
                    st.image(img_url, use_container_width=True)
                    
                    # 3. NAVIGATION (Uniquement si plus d'une photo existe)
                    if len(images) > 1:
                        nb1, nb2, nb3 = st.columns([1, 2, 1])
                        
                        with nb1:
                            if st.button("◀️", use_container_width=True, key="prev"):
                                st.session_state.img_idx = (st.session_state.img_idx - 1) % len(images)
                                st.rerun()
                        
                        with nb2:
                            st.write(f"<p style='text-align:center'>{st.session_state.img_idx + 1} / {len(images)}</p>", unsafe_allow_html=True)
                        
                        with nb3:
                            if st.button("▶️", use_container_width=True, key="next"):
                                st.session_state.img_idx = (st.session_state.img_idx + 1) % len(images)
                                st.rerun()
                else:
                    st.info("📷 Aucune photo pour cette recette.")
           
        # --- BOUTONS ADMIN (À l'intérieur du bloc 'if choix != "---"') ---
            if st.session_state.get("authentifie", False):
                st.divider()
                b1, b2 = st.columns(2)
                
                # BOUTON SUPPRIMER
                if b1.button("🗑️ Supprimer la recette", use_container_width=True):
                    with st.spinner("Suppression complète..."):
                        if supprimer_fichier_github(info['chemin']):
                            for p in recette.get('images', []): 
                                supprimer_fichier_github(p)
                
                            st.cache_data.clear() 
                            
                            # --- MODIFICATION ICI : ON LIT L'INDEX VIA L'API POUR ÊTRE INSTANTANÉ ---
                            conf = get_github_config()
                            url_api_idx = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/data/index_recettes.json"
                            res_idx = requests.get(url_api_idx, headers=conf['headers'])
                            
                            if res_idx.status_code == 200:
                                import base64
                                content_b64 = res_idx.json().get('content', '')
                                content_str = base64.b64decode(content_b64).decode('utf-8')
                                index_frais = json.loads(content_str)
                            else:
                                index_frais = []

                            nouvel_index = [r for r in index_frais if r['chemin'] != info['chemin']]
                
                            # Sauvegarde du nouvel index propre
                            if envoyer_donnees_github("data/index_recettes.json", json.dumps(nouvel_index, indent=4, ensure_ascii=False), f"Suppr: {info['nom']}"):
                                st.cache_data.clear() 
                                st.session_state.menu_key += 1 
                                st.success(f"✅ '{info['nom']}' a été définitivement supprimée.")
                                time.sleep(1)
                                st.rerun()
    
                # BOUTON MODIFIER
                if b2.button("✍️ Modifier la recette", use_container_width=True):
                    st.session_state[m_edit] = True
                    st.rerun()

if __name__ == "__main__":
    afficher()
