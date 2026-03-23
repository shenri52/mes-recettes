import streamlit as st
import json, base64, time, io
from datetime import datetime
from PIL import Image
from utils import config_github, envoyer_vers_github, recuperer_donnees_index

def afficher():
    st.divider()

    # --- Initialisation session_state ---
    for k, v in {
        'form_count': 0,
        'ingredients_recette': [],
        'liste_choix': [""],
        'liste_categories': [""],
        'cat_fixee': ""
    }.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # --- Récupération de l'index complet si besoin ---
    if len(st.session_state.liste_choix) <= 1 or 'index_recettes' not in st.session_state:
        with st.spinner("📦 Synchronisation..."):
            index_complet, st.session_state.liste_choix, st.session_state.liste_categories = recuperer_donnees_index()
            st.session_state.index_recettes = index_complet

    f_id = st.session_state.form_count

    with st.container():
        # --- Nom de la recette ---
        nom_plat = st.text_input("Nom de la recette", key=f"nom_{f_id}")

        # --- Appareil, préparation, cuisson ---
        c_app, c_prep, c_cuis = st.columns(3)
        type_appareil = c_app.selectbox(
            "Appareil utilisé",
            options=sorted(["Aucun", "Cookeo", "Thermomix", "Ninja"]),
            key=f"app_{f_id}"
        )
        tps_prep = c_prep.text_input("Temps préparation", key=f"prep_{f_id}", placeholder="ex: 15 min")
        tps_cuis = c_cuis.text_input("Temps cuisson", key=f"cuis_{f_id}", placeholder="ex: 20 min")

        # --- CATÉGORIE ---
        def ajouter_cat_et_nettoyer():
            nom_nouveau = st.session_state.get(f"ncat_{f_id}", "").strip()
            if nom_nouveau and nom_nouveau not in st.session_state.liste_categories:
                st.session_state.liste_categories.append(nom_nouveau)
            st.session_state[f"scat_{f_id}"] = "---"
            st.session_state[f"ncat_{f_id}"] = ""

        col_cat, col_btn_cat = st.columns([2, 0.5])
        with col_cat:
            cats_existantes = sorted([c for c in st.session_state.liste_categories if c and c != "---"])
            opts_cat = ["---"] + cats_existantes + ["➕ Ajouter une nouvelle..."]
            choix_cat = st.selectbox("Catégorie", options=opts_cat, key=f"scat_{f_id}")
            if choix_cat == "➕ Ajouter une nouvelle...":
                st.text_input("Nom de la catégorie", key=f"ncat_{f_id}")
            else:
                st.session_state.cat_fixee = choix_cat

        with col_btn_cat:
            st.write(" "); st.write(" ")
            if choix_cat == "➕ Ajouter une nouvelle...":
                st.button("➕", key=f"bcat_valider_{f_id}", on_click=ajouter_cat_et_nettoyer)

        # --- INGRÉDIENTS ---
        def ajouter_ing_et_nettoyer():
            nom_nouveau = st.session_state.get(f"new_ing_{f_id}", "")
            choix_actuel = st.session_state[f"sel_{f_id}"]
            ing_final = nom_nouveau if choix_actuel == "➕ Ajouter un nouveau..." else choix_actuel
            qte_val = st.session_state[f"qte_{f_id}"]

            if ing_final and ing_final != "---":
                st.session_state.ingredients_recette.append({"Ingrédient": ing_final, "Quantité": qte_val})
                if ing_final not in st.session_state.liste_choix:
                    st.session_state.liste_choix.append(ing_final)
                st.session_state[f"new_ing_{f_id}"] = ""
                st.session_state[f"qte_{f_id}"] = ""
                st.session_state[f"sel_{f_id}"] = "---"

        col_ing, col_qte, col_btn_add = st.columns([2, 1, 0.6])
        with col_ing:
            opts_ing = ["---", "➕ Ajouter un nouveau..."] + st.session_state.liste_choix[1:]
            choix_i = st.selectbox("Ingrédient", options=opts_ing, key=f"sel_{f_id}")
            if choix_i == "➕ Ajouter un nouveau...":
                st.text_input("Nom de l'ingrédient", key=f"new_ing_{f_id}")

        with col_qte:
            st.text_input("Quantité", key=f"qte_{f_id}")

        with col_btn_add:
            st.write(" "); st.write(" ")
            if choix_i != "---":
                st.button("➕", key=f"btn_add_ing_{f_id}", on_click=ajouter_ing_et_nettoyer)

        # Affichage des ingrédients ajoutés
        for i in st.session_state.ingredients_recette:
            st.write(f"✅ {i['Quantité']} {i['Ingrédient']}")

    # --- MÉDIAS ---
    photos_fb = st.file_uploader(
        "📸 Photos de la recette",
        type=["jpg", "png", "jpeg"],
        key=f"fi_{f_id}",
        accept_multiple_files=True
    )

    # --- ENREGISTREMENT ---
    if st.button("💾 Enregistrer", use_container_width=True):
        f_cat = st.session_state.cat_fixee
        noms_existants = [r['nom'].strip().upper() for r in st.session_state.index_recettes]

        # --- Vérifications ---
        if not nom_plat.strip():
            st.error("⚠️ Le nom de la recette est obligatoire.")
        elif nom_plat.strip().upper() in noms_existants:
            st.error(f"⚠️ La recette '{nom_plat.upper()}' existe déjà dans votre index.")
        elif not f_cat or f_cat == "---":
            st.error("⚠️ Veuillez choisir ou ajouter une catégorie.")
        else:
            with st.spinner("Enregistrement en cours..."):
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                nom_fic, liste_medias = nom_plat.replace(" ", "_").lower(), []

                if photos_fb:
                    for idx, f in enumerate(photos_fb):
                        ext, data_env = f.name.lower().split('.')[-1], f.getvalue()
                        if ext in ["jpg", "jpeg", "png"]:
                            img = Image.open(f).convert("RGB")
                            img.thumbnail((1200, 1200))
                            buf = io.BytesIO()
                            img.save(buf, format="JPEG", quality=80, optimize=True)
                            data_env, ext = buf.getvalue(), "jpg"
                        ch_m = f"data/images/{ts}_{nom_fic}_{idx}.{ext}"
                        if envoyer_vers_github(ch_m, data_env, "Media", True):
                            liste_medias.append(ch_m)

                ch_r = f"data/recettes/{ts}_{nom_fic}.json"
                rec_data = {
                    "nom": nom_plat,
                    "categorie": f_cat,
                    "appareil": type_appareil,
                    "temps_preparation": tps_prep,
                    "temps_cuisson": tps_cuis,
                    "ingredients": st.session_state.ingredients_recette,
                    "etapes": "Voir image jointe",
                    "images": liste_medias
                }

                if envoyer_vers_github(ch_r, json.dumps(rec_data, indent=4, ensure_ascii=False), "Import"):
                    # --- Utilisation du session_state pour ne jamais écraser ---
                    idx_data = st.session_state.index_recettes.copy()
                    idx_data.append({
                        "nom": nom_plat,
                        "categorie": f_cat,
                        "appareil": type_appareil,
                        "ingredients": [i['Ingrédient'] for i in st.session_state.ingredients_recette],
                        "chemin": ch_r
                    })
                    envoyer_vers_github(
                        "data/index_recettes.json",
                        json.dumps(idx_data, indent=4, ensure_ascii=False),
                        "MAJ Index"
                    )

                    # --- Mise à jour session_state ---
                    st.session_state.index_recettes = idx_data
                    st.session_state.ingredients_recette = []
                    st.session_state.cat_fixee = ""
                    st.session_state.form_count += 1

                    time.sleep(1)
                    st.success("✅ Recette importée avec succès !")
                    st.rerun()
