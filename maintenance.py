import streamlit as st
import requests, json, time, io
from PIL import Image
from utils import config_github, envoyer_vers_github, charger_donnees, compresser_image

# --- INTERFACE DE MAINTENANCE ---
def afficher():
    st.header("🛠️ Maintenance")
    st.divider()

    if "bouton_analyse_clique" not in st.session_state:
        for key in ["a_reparer", "index_a_sauvegarder", "images_a_compresser", "fichiers_a_sauvegarder"]:
            if key in st.session_state:
                del st.session_state[key]

    # --- SECTION 1 : SYNCHRONISATION INDEX ---
    if st.button("🔍 Réparer l'index des recettes", use_container_width=True):
        st.session_state.bouton_analyse_clique = True
        conf = config_github()
        res = requests.get(f"https://api.github.com/repos/{st.secrets['REPO_OWNER']}/{st.secrets['REPO_NAME']}/git/trees/main?recursive=1", headers=conf['headers'])
        if res.status_code == 200:
            tree = res.json().get('tree', [])
            exclus = ['data/index_recettes.json', 'data/index_produits_zones.json', 'data/planning.json', 'data/plats_rapides.json']
            physiques = [i['path'] for i in tree if i['path'].startswith('data/') and i['path'].endswith('.json') and i['path'] not in exclus]
            index_actuel = charger_donnees("data/index_recettes.json")
            chemins_index = {r['chemin'] for r in index_actuel}
            manquantes = [f for f in physiques if f not in chemins_index]
            st.write(f"📁 **Fichiers /data :** {len(physiques)}")
            st.write(f"🗂️ **Index des recettes :** {len(index_actuel)}")
            if manquantes:
                st.warning(f"⚠️ {len(manquantes)} fichiers hors index.")
                with st.expander("📄 Voir la liste des fichiers manquants"):
                    for m in manquantes:
                        st.write(f"- `{m}`")
                st.session_state.a_reparer = manquantes
            else: st.success("✅ Index à jour.")

    if st.session_state.get("a_reparer"):
        if st.button("🚀 Intégrer les fichiers manquants", use_container_width=True):
            with st.spinner("Analyse..."):
                index_actuel = charger_donnees("data/index_recettes.json")
                nouvelles = []
                for chemin in st.session_state.a_reparer:
                    r = requests.get(f"https://raw.githubusercontent.com/{st.secrets['REPO_OWNER']}/{st.secrets['REPO_NAME']}/main/{chemin}")
                    if r.status_code == 200:
                        d = r.json()
                        nouvelles.append({"nom": d.get("nom", "Sans nom"), "categorie": d.get("categorie", "Non classé"), "appareil": d.get("appareil", "Aucun"), "ingredients": [i.get("Ingrédient") for i in d.get("ingredients", [])], "chemin": chemin})
                index_final = sorted(index_actuel + nouvelles, key=lambda x: x['nom'].lower())
                if envoyer_vers_github("data/index_recettes.json", index_final, "🛠️ Réparation"):
                    st.success("✅ Index réparé !")
                    del st.session_state.a_reparer
                    st.rerun()

    # --- SECTION 2 : NETTOYAGE INGRÉDIENTS ---
    if st.button("🧹 Réparer le nom des ingrédients", use_container_width=True):
        index_actuel = charger_donnees("data/index_recettes.json")
        erreurs, index_nettoye, fichiers_maj = [], [], []
        for recette in index_actuel:
            r = requests.get(f"https://raw.githubusercontent.com/{st.secrets['REPO_OWNER']}/{st.secrets['REPO_NAME']}/main/{recette['chemin']}?t={int(time.time())}")
            if r.status_code == 200:
                data, i_clean, noms_i, modif, details = r.json(), [], [], False, []
                for item in data.get("ingredients", []):
                    n_orig = item.get("Ingrédient", "")
                    n_propre = " ".join(n_orig.split()).capitalize()
                    i_clean.append({"Ingrédient": n_propre, "Quantité": item.get("Quantité", "")})
                    noms_i.append(n_propre)
                    if n_propre != n_orig:
                        modif = True
                        details.append(f"  ❌ `{n_orig}` ➡️ ✅ `{n_propre}`")
                if modif:
                    erreurs.append({"nom": recette["nom"], "chemin": recette["chemin"], "details": details})
                    data["ingredients"] = i_clean
                    fichiers_maj.append({"chemin": recette["chemin"], "contenu": data})
                recette_copie = recette.copy()
                recette_copie["ingredients"] = noms_i
                index_nettoye.append(recette_copie)
        if erreurs:
            st.session_state.index_a_sauvegarder, st.session_state.fichiers_a_sauvegarder = index_nettoye, fichiers_maj
            st.warning(f"⚠️ {len(erreurs)} recette(s) à corriger :")
            for err in erreurs:
                st.markdown(f"**📍 {err['nom']}**")
                for d in err['details']: st.write(d)
                st.divider()
        else: st.success("✅ Tous les ingrédients sont propres !")

    if st.session_state.get("index_a_sauvegarder"):
        if st.button("🚀 Appliquer le nettoyage", use_container_width=True):
            for f in st.session_state.fichiers_a_sauvegarder:
                envoyer_vers_github(f['chemin'], f['contenu'], "🧹 Nettoyage")
            envoyer_vers_github("data/index_recettes.json", st.session_state.index_a_sauvegarder, "🧹 Nettoyage Index")
            del st.session_state.index_a_sauvegarder
            st.rerun()

    # --- SECTION 3 : OPTIMISATION IMAGES ---
    if st.button("🖼️ Optimiser les images", use_container_width=True):
        conf = config_github()
        res = requests.get(f"https://api.github.com/repos/{st.secrets['REPO_OWNER']}/{st.secrets['REPO_NAME']}/git/trees/main?recursive=1", headers=conf['headers'])
        if res.status_code == 200:
            lourdes = [i for i in res.json().get('tree', []) if i['path'].lower().endswith(('.jpg', '.jpeg', '.png')) and i.get('size', 0) > 500 * 1024]
            if lourdes:
                st.session_state.images_a_compresser = lourdes
                st.warning(f"⚠️ {len(lourdes)} image(s) lourde(s) :")
                with st.expander("📸 Voir le détail des fichiers à optimiser"):
                    for img in lourdes:
                        st.code(img['path'])
                        st.write(f"Taille : {img['size'] / 1024:.0f} Ko")
                        st.divider()
            else: st.success("Toutes les images sont légères. ✅")

    if st.session_state.get("images_a_compresser"):
        if st.button("⚡ Compresser les images", use_container_width=True):
            barre = st.progress(0)
            for idx, img in enumerate(st.session_state.images_a_compresser):
                r = requests.get(f"https://raw.githubusercontent.com/{st.secrets['REPO_OWNER']}/{st.secrets['REPO_NAME']}/main/{img['path']}")
                if r.status_code == 200:
                    data_compressee = compresser_image(io.BytesIO(r.content))
                    envoyer_vers_github(img['path'], data_compressee, "📸 Opti Image", est_binaire=True)
                barre.progress((idx + 1) / len(st.session_state.images_a_compresser))
            del st.session_state.images_a_compresser
            st.success("Compression terminée ! 🚀")
            st.rerun()
