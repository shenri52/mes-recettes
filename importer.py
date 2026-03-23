import streamlit as st
import json, io, time
from datetime import datetime
from PIL import Image
from utils import config_github, envoyer_vers_github, recuperer_donnees_index

def compresser_image(upload_file):
    img = Image.open(upload_file)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    img.thumbnail((1200, 1200))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=80, optimize=True)
    return buf.getvalue()

def afficher():
    st.header("📥 Importer / Ajouter une recette")
    st.divider()

    # --- Initialisation session_state ---
    for k, v in {
        'form_count_img': 0,
        'ingredients_img': [],
        'liste_choix_img': ["---"],
        'liste_categories_img': ["---"],
        'cat_fixee': ""
    }.items():
        if k not in st.session_state:
            st.session_state[k] = v

    f_id = st.session_state.form_count_img

    # --- Toujours récupérer l'index complet pour ne rien perdre ---
    with st.spinner("📦 Synchronisation avec GitHub..."):
        index_complet, liste_choix, liste_categories = recuperer_donnees_index()
        st.session_state.index_recettes = index_complet
        st.session_state.liste_choix_img = ["---"] + sorted({i for r in index_complet for i in r.get('ingredients', [])})
        st.session_state.liste_categories_img = ["---"] + sorted({r.get('categorie','') for r in index_complet if r.get('categorie')})

    # --- Nom + Appareil + Temps ---
    nom_plat = st.text_input("Nom de la recette", key=f"ni_{f_id}")
    c_app, c_prep, c_cuis = st.columns(3)
    type_appareil = c_app.selectbox("Appareil", options=sorted(["Aucun","Cookeo","Thermomix","Ninja"]), key=f"ai_{f_id}")
    tps_prep = c_prep.text_input("Temps préparation", key=f"pri_{f_id}", placeholder="ex: 10 min")
    tps_cuis = c_cuis.text_input("Temps cuisson", key=f"cui_{f_id}", placeholder="ex: 5 min")

    # --- Catégorie ---
    def ajouter_cat_img_nettoyer():
        nom_nouveau = st.session_state.get(f"ncat_{f_id}","").strip()
        if nom_nouveau and nom_nouveau not in st.session_state.liste_categories_img:
            st.session_state.liste_categories_img.append(nom_nouveau)
        st.session_state[f"scat_{f_id}"] = "---"
        st.session_state[f"ncat_{f_id}"] = ""

    col_cat, col_btn_cat = st.columns([2,0.5])
    with col_cat:
        cat_sans_tiret = [c for c in st.session_state.liste_categories_img if c!="---"]
        opts_cat = ["---"] + sorted(cat_sans_tiret) + ["➕ Ajouter une nouvelle..."]
        choix_cat = st.selectbox("Catégorie", options=opts_cat, key=f"scat_{f_id}")
        if choix_cat == "➕ Ajouter une nouvelle...":
            st.text_input("Nom de la catégorie", key=f"ncat_{f_id}")
        else:
            st.session_state.cat_fixee = choix_cat
    with col_btn_cat:
        st.write(" "); st.write(" ")
        if choix_cat == "➕ Ajouter une nouvelle...":
            st.button("➕", key=f"bcat_{f_id}", on_click=ajouter_cat_img_nettoyer)

    # --- Ingrédients ---
    def ajouter_ing_img_nettoyer():
        nom_nouveau = st.session_state.get(f"new_ing_{f_id}", "").strip()
        choix_actuel = st.session_state[f"sel_{f_id}"]
        ing_final = nom_nouveau if choix_actuel=="➕ Ajouter un nouveau..." else choix_actuel
        qte_val = st.session_state[f"qte_{f_id}"]
        if ing_final and ing_final != "---":
            st.session_state.ingredients_img.append({"Ingrédient": ing_final, "Quantité": qte_val})
            if ing_final not in st.session_state.liste_choix_img:
                st.session_state.liste_choix_img.append(ing_final)
            st.session_state[f"qte_{f_id}"] = ""
            st.session_state[f"new_ing_{f_id}"] = ""
            st.session_state[f"sel_{f_id}"] = "---"

    col_ing, col_qte, col_btn_add = st.columns([2,1,0.6])
    with col_ing:
        liste_sans_tiret = [i for i in st.session_state.liste_choix_img if i!="---"]
        opts_ing = ["---", "➕ Ajouter un nouveau..."] + sorted(liste_sans_tiret)
        choix_i = st.selectbox("Ingrédient", options=opts_ing, key=f"sel_{f_id}")
        if choix_i=="➕ Ajouter un nouveau...":
            st.text_input("Nom de l'ingrédient", key=f"new_ing_{f_id}")
    with col_qte:
        st.text_input("Quantité", key=f"qte_{f_id}")
    with col_btn_add:
        st.write(" "); st.write(" ")
        if choix_i!="---":
            st.button("➕", key=f"btn_add_{f_id}", on_click=ajouter_ing_img_nettoyer)

    # --- Upload Images ---
    photos_fb = st.file_uploader("📷 Photos de la recette", type=["jpg","png","jpeg"], key=f"fi_{f_id}", accept_multiple_files=True)

    # --- Enregistrer ---
    if st.button("💾 Enregistrer", use_container_width=True):
        f_cat = st.session_state.cat_fixee
        noms_existants = [r['nom'].strip().upper() for r in st.session_state.index_recettes]

        if not nom_plat.strip():
            st.error("⚠️ Le nom de la recette est obligatoire.")
        elif nom_plat.strip().upper() in noms_existants:
            st.error(f"⚠️ La recette '{nom_plat.upper()}' existe déjà dans votre index.")
        elif not f_cat or f_cat=="---":
            st.error("⚠️ Veuillez choisir ou ajouter une catégorie.")
        elif not photos_fb:
            st.error("⚠️ L'ajout d'au moins une image est obligatoire.")
        else:
            with st.spinner("🚀 Envoi vers GitHub..."):
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                nom_fic = nom_plat.replace(" ","_").lower()
                liste_medias = []

                for idx,f in enumerate(photos_fb):
                    img_data = compresser_image(f)
                    ch_m = f"data/images/{ts}_{nom_fic}_{idx}.jpg"
                    if envoyer_vers_github(ch_m, img_data, "Media", True):
                        liste_medias.append(ch_m)

                ch_r = f"data/recettes/{ts}_{nom_fic}.json"
                rec_data = {
                    "nom": nom_plat,
                    "categorie": f_cat,
                    "appareil": type_appareil,
                    "temps_preparation": tps_prep,
                    "temps_cuisson": tps_cuis,
                    "ingredients": st.session_state.ingredients_img,
                    "etapes": "Voir image jointe",
                    "images": liste_medias
                }

                # --- Ajouter la recette à l'index complet et uploader ---
                if envoyer_vers_github(ch_r, json.dumps(rec_data, indent=4, ensure_ascii=False), "Import"):
                    idx_data = st.session_state.index_recettes.copy()
                    idx_data.append({
                        "nom": nom_plat,
                        "categorie": f_cat,
                        "appareil": type_appareil,
                        "ingredients": [i['Ingrédient'] for i in st.session_state.ingredients_img],
                        "chemin": ch_r
                    })

                    envoyer_vers_github("data/index_recettes.json", json.dumps(idx_data, indent=4, ensure_ascii=False), "MAJ Index")
                    refresh_index_session()
                    
                    # --- Mise à jour session_state ---
                    st.session_state.index_recettes = idx_data
                    st.session_state.ingredients_img = []
                    st.session_state.cat_fixee = ""
                    st.session_state.form_count_img += 1
                    st.success("✅ Recette importée avec succès !")
                    time.sleep(1)
                    st.rerun()

if __name__=="__main__":
    afficher()
