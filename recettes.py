import streamlit as st
import requests
import json
import time
import uuid
import io

from PIL import Image
from utils import config_github, envoyer_vers_github, recuperer_donnees_index

# ------------------ SUPPRESSION ------------------
def supprimer_fichier_github(chemin):
    conf = config_github()
    url = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/{chemin.strip('/')}"
    
    get_res = requests.get(url, headers=conf['headers'])
    if get_res.status_code == 200:
        sha = get_res.json()['sha']
        res_del = requests.delete(
            url,
            headers=conf['headers'],
            json={"message": "Suppression", "sha": sha, "branch": "main"}
        )
        return res_del.status_code in [200, 204]
    return False

# ------------------ IMAGE ------------------
def compresser_image(upload_file):
    img = Image.open(upload_file)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    img.thumbnail((1200, 1200))
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=80, optimize=True)
    return buffer.getvalue()

# ------------------ INDEX ------------------
def sauvegarder_index_global(index_maj):
    index_trie = sorted(index_maj, key=lambda x: x['nom'].lower())

    envoyer_vers_github(
        "data/index_recettes.json",
        json.dumps(index_trie, indent=4, ensure_ascii=False),
        "MAJ Index"
    )

    st.session_state.index_recettes = index_trie


# ------------------ APP ------------------
def afficher():

    def nettoyer_modif():
        if "img_idx" in st.session_state:
            del st.session_state["img_idx"]
        for key in list(st.session_state.keys()):
            if any(key.startswith(p) for p in ["edit_", "init_done_", "ings_list_"]):
                del st.session_state[key]

    index, ingredients, categories = recuperer_donnees_index()
    st.divider()

    # ------------------ FILTRES ------------------
    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
    recherche = c1.text_input("🔍 Rechercher", "").lower()

    cats_existantes = sorted(list(set(r.get('categorie', 'Non classé') for r in index)))
    apps = ["Tous"] + sorted(list(set(r.get('appareil', 'Aucun') for r in index)))

    tous_ings_bruts = []
    for r in index:
        if r.get('ingredients'):
            tous_ings_bruts.extend(r['ingredients'])
    liste_ingredients_unique = sorted(list(set(tous_ings_bruts)))

    f_cat = c2.selectbox("Catégorie", ["Tous"] + cats_existantes)
    f_app = c3.selectbox("Appareil", apps)
    f_ing = c4.selectbox("Ingrédient", ["Tous"] + liste_ingredients_unique)

    # ------------------ FILTRAGE ------------------
    resultats = [
        r for r in index 
        if (not recherche or recherche in r['nom'].lower())
        and (f_cat == "Tous" or r['categorie'] == f_cat)
        and (f_app == "Tous" or r['appareil'] == f_app)
        and (f_ing == "Tous" or f_ing in r.get('ingredients', []))
    ]

    noms_filtres = [r['nom'].upper() for r in resultats]

    st.session_state['liste_recettes_filtrees'] = ["---"] + noms_filtres

    choix = st.selectbox(
        "📖 Sélectionner une recette",
        st.session_state['liste_recettes_filtrees'],
        key="select_recette",
        on_change=nettoyer_modif
    )

    # ------------------ AFFICHAGE ------------------
    if choix != "---":
        info = resultats[noms_filtres.index(choix)]

        url_full = f"https://raw.githubusercontent.com/{config_github()['owner']}/{config_github()['repo']}/main/{info['chemin']}?t={int(time.time())}"
        res = requests.get(url_full)

        # 🔥 CORRECTION JSON ERROR
        if res.status_code != 200:
            st.warning("⚠️ Recette supprimée ou introuvable")
            st.session_state.pop("select_recette", None)
            st.rerun()
            return

        recette = res.json()

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
                if "img_idx" not in st.session_state:
                    st.session_state.img_idx = 0

                if st.session_state.img_idx >= len(images):
                    st.session_state.img_idx = 0

                img_url = f"https://raw.githubusercontent.com/{config_github()['owner']}/{config_github()['repo']}/main/{images[st.session_state.img_idx]}?t={int(time.time())}"
                st.image(img_url, use_container_width=True)

    # ------------------ ADMIN ------------------
    if choix != "---" and st.session_state.get("authentifie", False):

        b1, b2 = st.columns(2)

# ------------------ BOUTON SUPPRIMER ------------------
if choix != "---" and st.session_state.get("authentifie", False):
    b1, b2 = st.columns(2)

    if b1.button("🗑️ Supprimer la recette", use_container_width=True):
        # 1️⃣ Supprimer le fichier recette sur GitHub
        if supprimer_fichier_github(info['chemin']):
            # Supprimer les images associées
            for p in recette.get('images', []):
                supprimer_fichier_github(p)

            # 2️⃣ Mettre à jour l'index
            nouvel_index = [r for r in index if r['chemin'] != info['chemin']]
            sauvegarder_index_global(nouvel_index)

            # 3️⃣ Réinitialiser la liste et la sélection de manière sûre
            st.session_state['liste_recettes_filtrees'] = ["---"] + [r['nom'].upper() for r in nouvel_index]

            # Supprimer la clé select_recette avant le rerun pour éviter l'erreur
            if "select_recette" in st.session_state:
                del st.session_state["select_recette"]

            # 4️⃣ Supprimer les variables temporaires
            if "img_idx" in st.session_state:
                del st.session_state["img_idx"]
            for key in list(st.session_state.keys()):
                if any(key.startswith(p) for p in ["edit_", "init_done_", "ings_list_"]):
                    del st.session_state[key]

            # 5️⃣ Forcer la page à se rerun pour afficher "---"
            st.experimental_rerun()

        if b2.button("✍️ Modifier", use_container_width=True):
            st.session_state[f"edit_{info['chemin']}"] = True
            st.rerun()


# ------------------ MAIN ------------------
if __name__ == "__main__":
    afficher()
