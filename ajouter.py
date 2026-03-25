import streamlit as st
import json, base64, requests, time, io
from datetime import datetime
from PIL import Image
from utils import config_github, charger_index, sauvegarder_index, verifier_doublon

def recuperer_donnees_index():
    idx = charger_index()
    if idx:
        ing = {i for r in idx for i in r.get('ingredients', []) if i}
        cat = {r.get('categorie') for r in idx if r.get('categorie')}
        return ["---"] + sorted(list(ing)), ["---"] + sorted(list(cat))
    return ["---"], ["---"]

def afficher():

    # Initialisation session_state
    if 'form_count' not in st.session_state: st.session_state.form_count = 0
    if 'ingredients_recette' not in st.session_state: st.session_state.ingredients_recette = []
    if 'liste_choix' not in st.session_state: st.session_state.liste_choix = ["---"]
    if 'liste_categories' not in st.session_state: st.session_state.liste_categories = ["---"]
    if 'cat_fixee' not in st.session_state: st.session_state.cat_fixee = ""

    if len(st.session_state.liste_choix) <= 1:
        st.session_state.liste_choix, st.session_state.liste_categories = recuperer_donnees_index()

    f_id = st.session_state.form_count

    with st.container():
        nom_plat = st.text_input("Nom de la recette", key=f"nom_{f_id}")
        
        c_app, c_prep, c_cuis = st.columns(3)
        type_appareil = c_app.selectbox("Appareil", options=["Aucun", "Cookeo", "Thermomix", "Ninja"], key=f"app_{f_id}")
        tps_prep = c_prep.text_input("Prép. (ex: 10 min)", key=f"prep_{f_id}")
        tps_cuis = c_cuis.text_input("Cuis. (ex: 20 min)", key=f"cuis_{f_id}")
        
        # --- CATÉGORIE ---
        def ajouter_cat_et_nettoyer():
            n = st.session_state.get(f"ncat_{f_id}", "").strip()
            if n:
                if n not in st.session_state.liste_categories:
                    st.session_state.liste_categories.append(n)
                st.session_state[f"scat_{f_id}"] = n
                st.session_state.cat_fixee = n

        col_cat, col_btn_cat = st.columns([2, 0.5])
        with col_cat:
            cats = sorted([c for c in st.session_state.liste_categories if c and c != "---"])
            choix_cat = st.selectbox("Catégorie", ["---"] + cats + ["➕ Nouvelle..."], key=f"scat_{f_id}")
            if choix_cat == "➕ Nouvelle...":
                st.text_input("Nom catégorie", key=f"ncat_{f_id}")
                st.button("➕", key=f"bcat_{f_id}", on_click=ajouter_cat_et_nettoyer)
            else:
                st.session_state.cat_fixee = choix_cat

        # --- INGRÉDIENTS ---
        def ajouter_ing_et_nettoyer():
            new = st.session_state.get(f"new_ing_{f_id}", "").strip()
            sel = st.session_state[f"sel_{f_id}"]
            ing = new if sel == "➕ Nouveau..." else sel
            qte = st.session_state[f"qte_{f_id}"]
            if ing and ing != "---":
                st.session_state.ingredients_recette.append({"Ingrédient": ing, "Quantité": qte})
                st.session_state[f"qte_{f_id}"] = ""
                st.session_state[f"sel_{f_id}"] = "---"

        c1, c2, c3 = st.columns([2, 1, 0.5])
        with c1:
            opts_i = ["---", "➕ Nouveau..."] + [i for i in st.session_state.liste_choix if i != "---"]
            choix_i = st.selectbox("Ingrédient", opts_i, key=f"sel_{f_id}")
            if choix_i == "➕ Nouveau...": st.text_input("Nom", key=f"new_ing_{f_id}")
        c2.text_input("Qté", key=f"qte_{f_id}")
        if choix_i != "---":
            c3.write(" "); c3.write(" ")
            c3.button("➕", key=f"bi_{f_id}", on_click=ajouter_ing_et_nettoyer)

        for i in st.session_state.ingredients_recette:
            st.write(f"✅ {i['Quantité']} {i['Ingrédient']}")

    etapes = st.text_area("Étapes", key=f"et_{f_id}")
    photos = st.file_uploader("📸 Photos", type=["jpg","png","jpeg"], key=f"fi_{f_id}", accept_multiple_files=True)

    if st.button("💾 Enregistrer la recette", use_container_width=True):
        index_actuel = charger_index()
        if verifier_doublon(nom_plat, index_actuel):
                st.error(f"⚠️ Une recette nommée '{nom_plat}' existe déjà. Veuillez choisir un autre nom.")
        elif not nom_plat or st.session_state.cat_fixee == "---":
            st.error("⚠️ Nom et catégorie obligatoires")
        else:
            with st.spinner("Enregistrement..."):
                conf = config_github()
                ts = datetime.now().strftime("%Y%m%d_%H%M%S") # <--- L'erreur était ici
                nom_fic = nom_plat.replace(" ", "_").lower()
                
                liste_medias = []
                if photos:
                    for idx, f in enumerate(photos):
                        img = Image.open(f).convert("RGB")
                        img.thumbnail((1000, 1000))
                        buf = io.BytesIO()
                        img.save(buf, format="JPEG", quality=80)
                        ch_m = f"data/images/{ts}_{nom_fic}_{idx}.jpg"
                        
                        # Payload GitHub manuel pour éviter les erreurs d'import
                        url_m = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/{ch_m}"
                        b64_m = base64.b64encode(buf.getvalue()).decode()
                        requests.put(url_m, headers=conf['headers'], json={"message":"Photo","content":b64_m})
                        liste_medias.append(ch_m)

                ch_r = f"data/recettes/{ts}_{nom_fic}.json"
                rec_data = {
                    "nom": nom_plat, "categorie": st.session_state.cat_fixee,
                    "appareil": type_appareil, "temps_preparation": tps_prep,
                    "temps_cuisson": tps_cuis, "ingredients": st.session_state.ingredients_recette,
                    "etapes": etapes if etapes.strip() else "Voir photos",
                    "images": liste_medias
                }

                # Envoi Recette
                url_r = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/{ch_r}"
                b64_r = base64.b64encode(json.dumps(rec_data, indent=4, ensure_ascii=False).encode('utf-8')).decode()
                if requests.put(url_r, headers=conf['headers'], json={"message":"Recette","content":b64_r}).status_code in [200, 201]:
                    
                    # --- MAJ Index ---
                    idx_data = charger_index()
                    idx_data.append({
                        "nom": nom_plat, 
                        "categorie": st.session_state.cat_fixee,
                        "appareil": type_appareil,
                        "ingredients": [i['Ingrédient'] for i in st.session_state.ingredients_recette],
                        "chemin": ch_r
                    })

                    if sauvegarder_index(idx_data):
                        st.success("✅ Recette ajoutée !")
                        
                    st.session_state.ingredients_recette = []
                    st.session_state.form_count += 1
                    time.sleep(1)
                    st.rerun()

if __name__ == "__main__":
    afficher()
