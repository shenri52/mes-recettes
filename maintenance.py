import streamlit as st
import requests, json, base64, time, io
from PIL import Image
from utils import config_github

# --------------------------
# FONCTIONS UTILES
# --------------------------
def envoyer_donnees(chemin, contenu, message, est_image=False):
    """Fonction universelle pour envoyer texte ou images vers GitHub."""
    conf = config_github()
    url = f"{conf['base_url']}{chemin}"
    res_get = requests.get(f"{url}?t={int(time.time())}", headers=conf['headers'])
    sha = res_get.json().get('sha') if res_get.status_code == 200 else None
    contenu_b64 = base64.b64encode(contenu if est_image else contenu.encode('utf-8')).decode('utf-8')
    payload = {"message": message, "content": contenu_b64, "branch": "main"}
    if sha: payload["sha"] = sha
    return requests.put(url, headers=conf['headers'], json=payload).status_code in [200, 201]

def charger_index_local():
    """Récupère l'index des recettes en contournant le cache."""
    url = f"https://raw.githubusercontent.com/{st.secrets['REPO_OWNER']}/{st.secrets['REPO_NAME']}/main/data/index_recettes.json?t={int(time.time())}"
    res = requests.get(url)
    return res.json() if res.status_code == 200 else []

# --------------------------
# INTERFACE MAINTENANCE
# --------------------------
def afficher():
    # Reset des variables session au lancement
    if "bouton_analyse_clique" not in st.session_state:
        for key in ["a_reparer", "index_a_sauvegarder", "fichiers_a_sauvegarder", "images_a_compresser", "orphelines"]:
            if key in st.session_state: del st.session_state[key]

    st.header("🛠️ Maintenance des recettes")
    st.divider()

    # --------------------------
    # SECTION 1 : SYNCHRONISATION INDEX
    # --------------------------
    if st.button("🔍 Réparer l'index des recettes", use_container_width=True):
        st.session_state.bouton_analyse_clique = True
        conf = config_github()
        res = requests.get(f"https://api.github.com/repos/{st.secrets['REPO_OWNER']}/{st.secrets['REPO_NAME']}/git/trees/main?recursive=1", headers=conf['headers'])
        if res.status_code == 200:
            tree = res.json().get('tree', [])
            # Fichiers physiques sur GitHub
            physiques = [i['path'] for i in tree if i['path'].startswith('data/recettes/') and i['path'].endswith('.json')]
            # Index actuel
            index_actuel = charger_index_local()
            chemins_index = {r['chemin'] for r in index_actuel}
            # Comparaison
            manquantes = [f for f in physiques if f not in chemins_index]
            orphelines = [r for r in index_actuel if r['chemin'] not in physiques]

            # Affichage statistiques
            col1, col2 = st.columns(2)
            col1.metric("📁 Fichiers de recettes", len(physiques))
            col2.metric("🗂️ Entrées dans l'index", len(index_actuel))

            # Fichiers manquants
            if manquantes:
                st.warning(f"⚠️ {len(manquantes)} fichier(s) ne sont pas dans l'index.")
                with st.expander("Voir les fichiers à intégrer"):
                    for m in manquantes:
                        st.write(f"📄 {m}")
                st.session_state.a_reparer = manquantes

            # Bouton intégrer les fichiers manquants
            if st.session_state.get("a_reparer"):
                if st.button("🚀 Intégrer les fichiers manquants", use_container_width=True):
                    with st.spinner("Analyse..."):
                        index_actuel = charger_index_local()
                        nouvelles = []
                        for chemin in st.session_state.a_reparer:
                            r = requests.get(f"https://raw.githubusercontent.com/{st.secrets['REPO_OWNER']}/{st.secrets['REPO_NAME']}/main/{chemin}")
                            if r.status_code == 200:
                                d = r.json()
                                nouvelles.append({
                                    "nom": d.get("nom", "Sans nom"),
                                    "categorie": d.get("categorie", "Non classé"),
                                    "appareil": d.get("appareil", "Aucun"),
                                    "ingredients": [i.get("Ingrédient") for i in d.get("ingredients", [])],
                                    "chemin": chemin
                                })
                        # Merge et tri
                        index_final = sorted(index_actuel + nouvelles, key=lambda x: x['nom'].lower())
                        if envoyer_donnees("data/index_recettes.json", json.dumps(index_final, indent=4, ensure_ascii=False), "🛠️ Réparation"):
                            st.success("✅ Index réparé !")
                            del st.session_state.a_reparer
                            st.rerun()

            # Recettes fantômes
            if orphelines:
                st.error(f"🚨 {len(orphelines)} recette(s) dans l'index n'ont plus de fichier !")
                with st.expander("Voir les recettes fantômes"):
                    for o in orphelines:
                        st.write(f"👻 **{o.get('nom')}** (`{o.get('chemin')}`)")
                st.session_state.orphelines = orphelines

            if not manquantes and not orphelines:
                st.success("✅ L'index et les fichiers sont parfaitement synchronisés !")

    # Supprimer les fantômes
    if st.session_state.get("orphelines"):
        if st.button("🗑️ Supprimer les recettes fantômes de l'index", use_container_width=True):
            index_actuel = charger_index_local()
            nouveau_index = [r for r in index_actuel if r not in st.session_state.orphelines]
            if envoyer_donnees("data/index_recettes.json", json.dumps(nouveau_index, indent=4, ensure_ascii=False), "🛠️ Suppression fantômes"):
                st.success("✅ Index nettoyé !")
                del st.session_state.orphelines
                st.rerun()

    # --------------------------
    # SECTION 2 : NETTOYAGE INGREDIENTS
    # --------------------------
    if st.button("🧹 Réparer le nom des ingrédients", use_container_width=True):
        index_actuel = charger_index_local()
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
                st.markdown(f"**{err['nom']}**")
                for d in err['details']: st.write(d)
                st.divider()
        else:
            st.success("✅ Tous les ingrédients sont propres !")

    if st.session_state.get("index_a_sauvegarder"):
        if st.button("🚀 Appliquer le nettoyage", use_container_width=True):
            for f in st.session_state.fichiers_a_sauvegarder:
                envoyer_donnees(f['chemin'], json.dumps(f['contenu'], indent=4, ensure_ascii=False), "🧹 Nettoyage")
            envoyer_donnees("data/index_recettes.json", json.dumps(st.session_state.index_a_sauvegarder, indent=4, ensure_ascii=False), "🧹 Nettoyage Index")
            del st.session_state.index_a_sauvegarder
            st.rerun()

    # --------------------------
    # SECTION 3 : OPTIMISATION IMAGES
    # --------------------------
    if st.button("🖼️ Optimiser les images", use_container_width=True):
        conf = config_github()
        res = requests.get(f"https://api.github.com/repos/{st.secrets['REPO_OWNER']}/{st.secrets['REPO_NAME']}/git/trees/main?recursive=1", headers=conf['headers'])
        if res.status_code == 200:
            lourdes = [i for i in res.json().get('tree', []) if i['path'].lower().endswith(('.jpg', '.jpeg', '.png')) and i.get('size', 0) > 500 * 1024]
            if lourdes:
                st.session_state.images_a_compresser = lourdes
                st.warning(f"⚠️ {len(lourdes)} image(s) lourde(s) :")
                for img in lourdes:
                    st.code(img['path'])
                    st.write(f"Taille : {img['size'] / 1024:.0f} Ko")
                    st.divider()
            else:
                st.success("Toutes les images sont légères. ✅")

    if st.session_state.get("images_a_compresser"):
        if st.button("⚡ Compresser les images", use_container_width=True):
            barre = st.progress(0)
            for idx, img in enumerate(st.session_state.images_a_compresser):
                r = requests.get(f"https://raw.githubusercontent.com/{st.secrets['REPO_OWNER']}/{st.secrets['REPO_NAME']}/main/{img['path']}")
                if r.status_code == 200:
                    img_p = Image.open(io.BytesIO(r.content)).convert("RGB")
                    img_p.thumbnail((1200, 1200))
                    buf = io.BytesIO()
                    img_p.save(buf, format="JPEG", quality=75, optimize=True)
                    envoyer_donnees(img['path'], buf.getvalue(), "📸 Opti Image", est_image=True)
                barre.progress((idx + 1) / len(st.session_state.images_a_compresser))
            del st.session_state.images_a_compresser
            st.success("Compression terminée ! 🚀")
            st.rerun()
