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
    st.header("✍️ Ajouter une recette")

    for k, v in {'form_count': 0, 'ingredients_recette': [], 'liste_choix': [""], 'liste_categories': [""], 'cat_fixee': ""}.items():
        if k not in st.session_state: st.session_state[k] = v

    if len(st.session_state.liste_choix) <= 1:
        with st.spinner("📦 Synchronisation..."):
            st.session_state.liste_choix, st.session_state.liste_categories = get_index_options()

    f_id = st.session_state.form_count
    with st.container():
        nom_plat = st.text_input("Nom de la recette", key=f"nom_{f_id}")
        if verifier_doublon_recette(nom_plat):
            st.warning("⚠️ Ce nom existe déjà. À l'enregistrement, la date du jour sera ajoutée pour éviter d'écraser l'ancienne.")
        
        c_app, c_prep, c_cuis = st.columns(3)
        type_appareil = c_app.selectbox("Appareil utilisé", options=sorted(["Aucun", "Cookeo", "Thermomix", "Ninja"]), key=f"app_{f_id}")
        tps_prep = c_prep.text_input("Temps préparation", key=f"prep_{f_id}", placeholder="ex: 15 min")
        tps_cuis = c_cuis.text_input("Temps cuisson", key=f"cuis_{f_id}", placeholder="ex: 20 min")
        
        # --- CATÉGORIE ---
        def ajouter_cat_et_nettoyer():
            # 1. On récupère le texte saisi
            nom_nouveau = st.session_state.get(f"ncat_{f_id}", "").strip()
            if nom_nouveau:
                # 2. On l'ajoute à la liste de choix si besoin
                if nom_nouveau not in st.session_state.liste_categories:
                    st.session_state.liste_categories.append(nom_nouveau)
                
                st.session_state.cat_fixee = nom_nouveau
                
                # 3. LE RESET : On force le menu à revenir sur "---"
                st.session_state[f"scat_{f_id}"] = "---"
                
                # 4. On vide le champ de saisie
                st.session_state[f"ncat_{f_id}"] = ""

        col_cat, col_btn_cat = st.columns([2, 0.5])
        with col_cat:
            cats_existantes = sorted([c for c in st.session_state.liste_categories if c and c != "---"])
            opts_cat = ["---"] + cats_existantes + ["➕ Ajouter une nouvelle..."]
            
            # Un seul selectbox avec la clé dynamique
            choix_cat = st.selectbox("Catégorie", options=opts_cat, key=f"scat_{f_id}")
            
            if choix_cat == "➕ Ajouter une nouvelle...":
                st.text_input("Nom de la catégorie", key=f"ncat_{f_id}")
            elif choix_cat == "---":
                st.session_state.cat_fixee = "" # Sécurité : bloque l'enregistrement
            else:
                st.session_state.cat_fixee = choix_cat # Mémorise le choix existant

        with col_btn_cat:
            st.write(" "); st.write(" ")
            if choix_cat == "➕ Ajouter une nouvelle...":
                st.button("➕", key=f"bcat_valider_{f_id}", on_click=ajouter_cat_et_nettoyer)
                
        # ---  INGRÉDIENTS  ---
        def ajouter_ing_et_nettoyer():
            # 1. Récupération des saisies
            nom_nouveau = st.session_state.get(f"new_ing_{f_id}", "")
            choix_actuel = st.session_state[f"sel_{f_id}"]
            
            # Déterminer le nom final de l'ingrédient
            ing_final = nom_nouveau if choix_actuel == "➕ Ajouter un nouveau..." else choix_actuel
            qte_val = st.session_state[f"qte_{f_id}"]

            if ing_final and ing_final != "---":
                # Ajoute l'ingrédient à la rectte
                st.session_state.ingredients_recette.append({
                    "Ingrédient": ing_final, 
                    "Quantité": qte_val
                })
                
                # Ajoute l'ingrédient à la liste
                if ing_final not in st.session_state.liste_choix:
                    st.session_state.liste_choix.append(ing_final)
                
                # NETTOYAGE DES CHAMPS
                if f"new_ing_{f_id}" in st.session_state: 
                    st.session_state[f"new_ing_{f_id}"] = ""
                st.session_state[f"qte_{f_id}"] = ""
                
                # ON REVIENT SUR LE TIRET (Index 0)
                st.session_state[f"sel_{f_id}"] = "---"

        col_ing, col_qte, col_btn_add = st.columns([2, 1, 0.6])
        with col_ing:
            opts_ing = st.session_state.liste_choix[:1] + ["➕ Ajouter un nouveau..."] + st.session_state.liste_choix[1:]
            choix_i = st.selectbox("Ingrédient", options=opts_ing, key=f"sel_{f_id}")
            if choix_i == "➕ Ajouter un nouveau...":
                st.text_input("Nom de l'ingrédient", key=f"new_ing_{f_id}")
        
        with col_qte:
            st.text_input("Quantité", key=f"qte_{f_id}")
        
        with col_btn_add:
            st.write(" "); st.write(" ")
            # Le bouton n'apparaît QUE si on n'est pas sur le tiret "---"
            if choix_i != "---":
                st.button("➕", key=f"btn_add_ing_{f_id}", on_click=ajouter_ing_et_nettoyer)

        # Affichage visuel de ce qui est déjà dans la recette
        for i in st.session_state.ingredients_recette:
            st.write(f"✅ {i['Quantité']} {i['Ingrédient']}")

    # --- SECTION ÉTAPES ---
    etapes_saisies = st.text_area("📝 Étapes de la recette", key=f"etp_{f_id}", height=150, placeholder="1. Préchauffer le four...\n2. Mélanger...")
    
  # --- SECTION MÉDIAS  ---
    photos_fb = st.file_uploader(
        "📸 Photos de la recette", 
        type=["jpg", "png", "jpeg"], 
        key=f"fi_{f_id}", 
        accept_multiple_files=True
    )
    
    # --- BLOC BOUTON ENREGISTRER  ---
    if st.button("💾 Enregistrer", use_container_width=True):
        # 1. On détermine la catégorie finale avant de vérifier
        f_cat = st.session_state.cat_fixee
        
        # 2. LES VÉRIFICATIONS (Indispensables pour voir les messages d'erreur)
        if not nom_plat or nom_plat.strip() == "":
            st.error("⚠️ Le nom de la recette est obligatoire.")
        elif not f_cat or f_cat == "---":
            st.error("⚠️ Veuillez choisir ou ajouter une catégorie.")
        else:
            with st.spinner("Enregistrement..."):
                maintenant = datetime.now()
                ts = maintenant.strftime("%Y%m%d_%H%M%S")
                
                # --- ÉTAPE A : LE RENOMMAGE (Si besoin) ---
                if verifier_doublon_recette(nom_plat):
                    nom_plat = f"{nom_plat} ({maintenant.strftime('%d-%m-%Y')})"
                
                # --- ÉTAPE B : SÉCURITÉ (On crée la liste vide ici) ---
                nom_fic = nom_plat.replace(" ", "_").lower().replace("'", "_")
                liste_medias = []
                
                if photos_fb:
                    for idx, f in enumerate(photos_fb):
                        data_img, ext = traiter_et_compresser_image(f) 
                        ch_m = f"data/images/{ts}_{nom_fic}_{idx}.{ext}"
                        if envoyer_donnees_github(ch_m, data_img, "📸 Media", True): 
                            liste_medias.append(ch_m)

                ch_r = f"data/recettes/{ts}_{nom_fic}.json"
                rec_data = {
                    "nom": nom_plat, 
                    "categorie": f_cat, 
                    "appareil": type_appareil, 
                    "temps_preparation": tps_prep, 
                    "temps_cuisson": tps_cuis, 
                    "ingredients": st.session_state.ingredients_recette, 
                    "etapes": etapes_saisies if etapes_saisies.strip() != "" else "Voir image jointe", 
                    "images": liste_medias
                }
                
                if envoyer_donnees_github(ch_r, json.dumps(rec_data, indent=4, ensure_ascii=False), "📝 Recette"):
                    mettre_a_jour_index({
                        "nom": nom_plat, "categorie": f_cat, "appareil": type_appareil, 
                        "ingredients": [i['Ingrédient'] for i in st.session_state.ingredients_recette], 
                        "chemin": ch_r
                    })
                  
                    st.success("✅ Recette enregistrée avec succès !")
                        
                    # RESET mémoire
                    st.session_state.ingredients_recette = []
                    st.session_state.cat_fixee = ""
                    st.session_state.form_count += 1
                    time.sleep(1)
                    st.rerun()
