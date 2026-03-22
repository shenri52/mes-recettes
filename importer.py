import streamlit as st
import json, time

from datetime import datetime
from utils import (envoyer_donnees_github,
                   charger_json_github,
                   get_index_options,
                   traiter_et_compresser_image,
                   mettre_a_jour_index,
                   verifier_doublon_recette
                  )

def afficher():
    st.divider()
    
    # Initialisation session_state
    for k, v in {'form_count_img': 0, 'ingredients_img': [], 'liste_choix_img': ["---"], 'liste_categories_img': ["---"], 'cat_fixee': ""}.items():
        if k not in st.session_state: st.session_state[k] = v

    if len(st.session_state.liste_choix_img) <= 1:
        with st.spinner("📦 Synchronisation..."):
            st.session_state.liste_choix_img, st.session_state.liste_categories_img = get_index_options()
        
    f_id = st.session_state.form_count_img
    nom_plat = st.text_input("Nom de la recette", key=f"ni_{f_id}")
    if verifier_doublon_recette(nom_plat):
        st.warning("⚠️ Ce nom existe déjà. À l'enregistrement, la date du jour sera ajoutée pour éviter d'écraser l'ancienne.")
    
    c_app, c_prep, c_cuis = st.columns(3)
    type_appareil = c_app.selectbox("Appareil", options=sorted(["Aucun", "Cookeo", "Thermomix", "Ninja"]), key=f"ai_{f_id}")
    tps_prep = c_prep.text_input("Temps préparation", key=f"pri_{f_id}", placeholder="ex: 10 min")
    tps_cuis = c_cuis.text_input("Temps cuisson", key=f"cui_{f_id}", placeholder="ex: 5 min")

    # --- LOGIQUE CALLBACKS ---
    def ajouter_cat_img_nettoyer():
        nom_nouveau = st.session_state.get(f"ncat_{f_id}", "").strip()
        if nom_nouveau:
            if nom_nouveau not in st.session_state.liste_categories_img:
                st.session_state.liste_categories_img.append(nom_nouveau)
            st.session_state[f"scat_{f_id}"] = "---"
            st.session_state[f"ncat_{f_id}"] = ""

    def ajouter_ing_img_nettoyer():
        nom_nouveau = st.session_state.get(f"new_ing_{f_id}", "").strip()
        choix_actuel = st.session_state[f"sel_{f_id}"]
        ing_final = nom_nouveau if choix_actuel == "➕ Ajouter un nouveau..." else choix_actuel
        qte_val = st.session_state[f"qte_{f_id}"]
        if ing_final and ing_final != "---":
            st.session_state.ingredients_img.append({"Ingrédient": ing_final, "Quantité": qte_val})
            if ing_final not in st.session_state.liste_choix_img:
                st.session_state.liste_choix_img.append(ing_final)
            st.session_state[f"qte_{f_id}"] = ""
            st.session_state[f"new_ing_{f_id}"] = ""
            st.session_state[f"sel_{f_id}"] = "---"

    # --- CATÉGORIE ---
    col_cat, col_btn_cat = st.columns([2, 0.5])
    with col_cat:
        cat_sans_tiret = [c for c in st.session_state.liste_categories_img if c != "---"]
        opts_cat = ["---", "➕ Ajouter une nouvelle..."] + sorted(cat_sans_tiret)
        choix_cat = st.selectbox("Catégorie", options=opts_cat, key=f"scat_{f_id}")
        if choix_cat == "➕ Ajouter une nouvelle...":
            st.text_input("Nom de la catégorie", key=f"ncat_{f_id}")
            st.session_state.cat_fixee = ""
        elif choix_cat == "---":
            st.session_state.cat_fixee = ""
        else:
            st.session_state.cat_fixee = choix_cat

    with col_btn_cat:
        st.write(" "); st.write(" ")
        if choix_cat == "➕ Ajouter une nouvelle...":
            st.button("➕", key=f"bcat_{f_id}", on_click=ajouter_cat_img_nettoyer)

    # --- INGRÉDIENTS ---
    col_ing, col_qte, col_btn_add = st.columns([2, 1, 0.6])
    with col_ing:
        liste_sans_tiret = [i for i in st.session_state.liste_choix_img if i != "---"]    
        opts_ing = ["---", "➕ Ajouter un nouveau..."] + sorted(liste_sans_tiret)
        choix_i = st.selectbox("Ingrédient", options=opts_ing, key=f"sel_{f_id}")
        if choix_i == "➕ Ajouter un nouveau...":
            st.text_input("Nom de l'ingrédient", key=f"new_ing_{f_id}")
        
    with col_qte:
        st.text_input("Quantité", key=f"qte_{f_id}")
            
    with col_btn_add:
        st.write(" "); st.write(" ") 
        if choix_i != "---":
            st.button("➕", key=f"btn_add_{f_id}", on_click=ajouter_ing_img_nettoyer)

    for i in st.session_state.ingredients_img:
            st.write(f"✅ {i['Quantité']} {i['Ingrédient']}")

    # --- SECTION MÉDIAS  ---
    photos_fb = st.file_uploader("📷 Photos de la recette", type=["jpg", "png", "jpeg"], key=f"fi_{f_id}", accept_multiple_files=True)

    # --- BLOC BOUTON ENREGISTRER ---
    if st.button("💾 Enregistrer", use_container_width=True):
        f_cat = st.session_state.cat_fixee
        if not nom_plat or not f_cat or f_cat == "---":
            st.error("⚠️ Nom et Catégorie obligatoires.")
        else:
            with st.spinner("Enregistrement..."):
                # 1. On prépare l'image si elle existe
                img_data = None
                if photos_fb:
                    img_data, _ = traiter_et_compresser_image(photos_fb[0])

                # 2. ON APPELLE LA FONCTION CENTRALE (Comme dans la page Saisir)
                succes, nom_final = sauvegarder_recette_complete(
                    nom=nom_plat, 
                    categorie=f_cat, 
                    ingredients=st.session_state.ingredients_img, 
                    etapes="Voir image jointe", 
                    photos_files=img_data, # On passe l'image ici
                    appareil=type_appareil, 
                    t_prep=tps_prep, 
                    t_cuis=tps_cuis
                )
                
                if succes:
                    st.success(f"✅ '{nom_final}' enregistrée !")
                    st.session_state.ingredients_img = []
                    st.session_state.cat_fixee = ""
                    st.session_state.form_count_img += 1 
                    time.sleep(1)
                    st.rerun()
