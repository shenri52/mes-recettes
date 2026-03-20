import streamlit as st
import requests
import time
from PIL import Image

# Importations depuis utils
from utils import get_github_config, charger_json_github, envoyer_donnees_github, scanner_depot_complet, sauvegarder_json_github

def afficher():
    st.header("🛠️ Réparation et optimisation")
    st.divider()

    # Nettoyage du session state au démarrage
    if "bouton_analyse_clique" not in st.session_state:
        for key in ["a_reparer", "index_a_sauvegarder", "fichiers_a_sauvegarder", "images_a_compresser"]:
            if key in st.session_state: 
                del st.session_state[key]

    # --- SECTION 1 : SYNCHRONISATION INDEX ---
    if st.button("🔍 Réparer l'index des recettes", use_container_width=True):
        st.session_state.bouton_analyse_clique = True
        tree = scanner_depot_complet()

        physiques = [
            i['path'] for i in tree 
            if i['path'].startswith('data/recettes/') and i['path'].endswith('.json')
        ]
        
        index_actuel = charger_json_github("data/index_recettes.json")
        
        if index_actuel is None: index_actuel = []
            
        chemins_index = {r['chemin'] for r in index_actuel}
        manquantes = [f for f in physiques if f not in chemins_index]
        
        st.write(f"📁 **Fichiers détectés dans /data :** {len(physiques)}")
        st.write(f"🗂️ **Recettes actuellement dans l'index :** {len(index_actuel)}")
        
        if manquantes:
            st.warning(f"⚠️ {len(manquantes)} fichiers hors index.")
            st.session_state.a_reparer = manquantes
        else: 
            st.success("✅ Index à jour.")

    if st.session_state.get("a_reparer"):
        if st.button("🚀 Intégrer les fichiers manquants", use_container_width=True):
            with st.spinner("Analyse..."):
                index_actuel = charger_json_github("data/index_recettes.json")
                nouvelles = []
                conf = get_github_config()
                for chemin in st.session_state.a_reparer:
                    # Lecture directe sur le Raw pour le contenu
                    url_raw = f"https://raw.githubusercontent.com/{conf['owner']}/{conf['repo']}/main/{chemin}"
                    r = requests.get(url_raw)
                    if r.status_code == 200:
                        d = r.json()
                        nouvelles.append({
                            "nom": d.get("nom", "Sans nom"), 
                            "categorie": d.get("categorie", "Non classé"), 
                            "appareil": d.get("appareil", "Aucun"), 
                            "ingredients": [i.get("Ingrédient") for i in d.get("ingredients", [])], 
                            "chemin": chemin
                        })
                
                    index_final = sorted(index_actuel + nouvelles, key=lambda x: x['nom'].lower())
                    if sauvegarder_json_github("data/index_recettes.json", index_final, "🛠️ Réparation"):
                        st.success("✅ Index réparé !")
                    del st.session_state.a_reparer
                    st.rerun()

# --- SECTION 2 : NETTOYAGE INGRÉDIENTS ---
    if st.button("🧹 Réparer le nom des ingrédients", use_container_width=True):
        index_actuel = charger_json_github("data/index_recettes.json") or []
        conf = get_github_config()
        erreurs, index_nettoye, fichiers_maj = [], [], []
        
        barre = st.progress(0)
        
        for i, recette in enumerate(index_actuel):
            # Logique invisible : on compare en mémoire d'abord
            n_idx = recette.get("ingredients", [])
            n_propres = [" ".join(n.split()).capitalize() for n in n_idx]
            
            if n_propres != n_idx:
                # On ne télécharge QUE si nécessaire
                r = requests.get(f"https://raw.githubusercontent.com/{conf['owner']}/{conf['repo']}/main/{recette['chemin']}")
                if r.status_code == 200:
                    data = r.json()
                    for item in data.get("ingredients", []):
                        item["Ingrédient"] = " ".join(item["Ingrédient"].split()).capitalize()
                    fichiers_maj.append({"chemin": recette["chemin"], "contenu": data})
                    erreurs.append(recette["nom"])
            
            recette_clean = recette.copy()
            recette_clean["ingredients"] = n_propres
            index_nettoye.append(recette_clean)
            barre.progress((i + 1) / len(index_actuel))
        
        if erreurs:
            st.session_state.index_a_sauvegarder, st.session_state.fichiers_a_sauvegarder = index_nettoye, fichiers_maj
            st.warning(f"⚠️ {len(erreurs)} recette(s) à corriger :")
            for nom in erreurs:
                st.write(f"📍 {nom}")
        else:
            sauvegarder_json_github("data/index_recettes.json", index_nettoye, "🧹 Nettoyage Index")
            st.success("✅ Tous les ingrédients sont propres !")
            
    if st.session_state.get("index_a_sauvegarder"):
        if st.button("🚀 Appliquer le nettoyage", use_container_width=True):
            for f in st.session_state.fichiers_a_sauvegarder: 
                sauvegarder_json_github(f['chemin'], f['contenu'], "🧹 Nettoyage")
            sauvegarder_json_github("data/index_recettes.json", st.session_state.index_a_sauvegarder, "🧹 Nettoyage Index")
            del st.session_state.index_a_sauvegarder
            st.rerun()

    # --- SECTION 3 : OPTIMISATION IMAGES ---
    if st.button("🖼️ Optimiser les images", use_container_width=True):
        tree = scanner_depot_complet()
        lourdes = [i for i in tree if i['path'].lower().endswith(('.jpg', '.jpeg', '.png')) and i.get('size', 0) > 500 * 1024]
        if lourdes:
            st.session_state.images_a_compresser = lourdes
            st.warning(f"⚠️ {len(lourdes)} image(s) lourde(s) :")
            for img in lourdes:
                st.code(img['path'])
                st.write(f"Taille : {img['size'] / 1024:.0f} Ko")
                st.divider()
        else: st.success("Toutes les images sont légères. ✅")

    if st.session_state.get("images_a_compresser"):
        if st.button("⚡ Compresser les images", use_container_width=True):
            barre = st.progress(0)
            conf = get_github_config()
            for idx, img in enumerate(st.session_state.images_a_compresser):
                url_raw = f"https://raw.githubusercontent.com/{conf['owner']}/{conf['repo']}/main/{img['path']}"
                r = requests.get(url_raw)
                if r.status_code == 200:
                    img_p = Image.open(io.BytesIO(r.content)).convert("RGB")
                    img_p.thumbnail((1200, 1200))
                    buf = io.BytesIO()
                    img_p.save(buf, format="JPEG", quality=75, optimize=True)
                    envoyer_donnees_github(img['path'], buf.getvalue(), "📸 Opti Image", est_image=True)
                barre.progress((idx + 1) / len(st.session_state.images_a_compresser))
            del st.session_state.images_a_compresser
            st.success("Compression terminée ! 🚀")
            st.rerun()

    st.divider()

    # --- SECTION 4 : GESTION CATALOGUE ---
    st.subheader("🛒 Modifier ou ranger les produits")
    idx_z = st.session_state.get("index_zones", {})
    tous_p = sorted(list(idx_z.keys()))
    if not tous_p: 
        st.info("Veuillez charger la page 'Courses' pour initialiser le catalogue.")
    else:
        sel = st.selectbox("Produit à corriger", ["---"] + tous_p)
        if sel != "---":
            z_act = int(idx_z.get(sel, 0)) + 1
            with st.form("form_maint"):
                c1, c2 = st.columns([2, 1])
                n_nom = c1.text_input("Nouveau Nom", value=sel)
                n_zone = c2.text_input("Zone (1-12)", value=str(z_act))
                col_b1, col_b2 = st.columns(2)
                b_s = col_b1.form_submit_button("💾 ENREGISTRER")
                b_d = col_b2.form_submit_button("🗑️ SUPPRIMER")
                
                if b_s:
                    f_nom = n_nom.strip().capitalize()
                    d_idx = str(int("".join(filter(str.isdigit, n_zone))) - 1)
                    if sel in st.session_state.index_zones: del st.session_state.index_zones[sel]
                    st.session_state.index_zones[f_nom] = d_idx
                    
                    for k in range(12):
                        cat = st.session_state.data_a5[str(k)]["catalogue"]
                        if sel in cat: cat.remove(sel)
                        for p in st.session_state.data_a5[str(k)]["panier"]:
                            if p["nom"].lower() == sel.lower(): p["nom"] = f_nom
                    
                    new_cat = st.session_state.data_a5[d_idx]["catalogue"]
                    if f_nom not in new_cat:
                        new_cat.append(f_nom)
                        new_cat.sort()
                    
                    sauvegarder_json_github("data/index_produits_zones.json", st.session_state.index_zones, "🛠️ Maj Catalogue")
                    sauvegarder_json_github("courses/index_courses.json", st.session_state.data_a5, "🛠️ Maj Data")
                    st.success("Mise à jour réussie ! 🚀")
                    time.sleep(1)
                    st.rerun()
                
                if b_d:
                    if sel in st.session_state.index_zones: del st.session_state.index_zones[sel]
                    for k in range(12):
                        if sel in st.session_state.data_a5[str(k)]["catalogue"]: 
                            st.session_state.data_a5[str(k)]["catalogue"].remove(sel)
                    sauvegarder_json_github("data/index_produits_zones.json", st.session_state.index_zones, "🗑️ Suppression")
                    sauvegarder_json_github("courses/index_courses.json", st.session_state.data_a5, "🗑️ Suppression")
                    st.rerun()
