import streamlit as st
import requests
import json
import time
import uuid
import io

from PIL import Image
from utils import config_github, envoyer_vers_github, recuperer_donnees_index

# ------------------ SUPPRESSION GITHUB ------------------
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

    # reset edition
    def nettoyer():
        st.session_state.pop("img_idx", None)
        for key in list(st.session_state.keys()):
            if key.startswith(("edit_", "init_", "ings_")):
                del st.session_state[key]

    index, ingredients, categories = recuperer_donnees_index()

    st.title("📖 Mes recettes")
    st.divider()

    # ------------------ FILTRES ------------------
    recherche = st.text_input("🔍 Rechercher").lower()

    resultats = [
        r for r in index
        if not recherche or recherche in r['nom'].lower()
    ]

    noms = [r['nom'].upper() for r in resultats]

    choix = st.selectbox(
        "Choisir une recette",
        ["---"] + noms,
        key="select_recette",
        on_change=nettoyer
    )

    # ------------------ RESET SI SUPPRIMÉ ------------------
    if choix != "---" and choix not in noms:
        st.session_state.pop("select_recette", None)
        st.rerun()

    # ------------------ AFFICHAGE ------------------
    if choix != "---":
        info = resultats[noms.index(choix)]

        url = f"https://raw.githubusercontent.com/{config_github()['owner']}/{config_github()['repo']}/main/{info['chemin']}?t={int(time.time())}"
        res = requests.get(url)

        # 🔥 évite JSONDecodeError
        if res.status_code != 200:
            st.warning("⚠️ Recette supprimée")
            st.session_state.pop("select_recette", None)
            st.rerun()
            return

        recette = res.json()

        st.subheader(recette['nom'].upper())

        # infos
        st.write(f"**Catégorie :** {recette.get('categorie', '-')}")
        st.write(f"**Appareil :** {recette.get('appareil', '-')}")

        st.write("### Ingrédients")
        for i in recette.get('ingredients', []):
            st.write(f"- {i.get('Quantité','')} {i.get('Ingrédient','')}")

        st.write("### Instructions")
        st.write(recette.get('etapes', ""))

        # ------------------ IMAGE ------------------
        images = recette.get('images', [])

        if images:
            if "img_idx" not in st.session_state:
                st.session_state.img_idx = 0

            if st.session_state.img_idx >= len(images):
                st.session_state.img_idx = 0

            img_url = f"https://raw.githubusercontent.com/{config_github()['owner']}/{config_github()['repo']}/main/{images[st.session_state.img_idx]}"
            st.image(img_url)

        # ------------------ SUPPRESSION ------------------
        if st.session_state.get("authentifie", False):
            if st.button("🗑️ Supprimer la recette"):

                if supprimer_fichier_github(info['chemin']):

                    # supprimer images
                    for p in recette.get('images', []):
                        supprimer_fichier_github(p)

                    # MAJ index
                    nouvel_index = [
                        r for r in index if r['chemin'] != info['chemin']
                    ]
                    sauvegarder_index_global(nouvel_index)

                    # reset propre (IMPORTANT)
                    st.session_state.pop("select_recette", None)
                    st.session_state.pop("img_idx", None)

                    st.success("Recette supprimée")
                    st.rerun()


# ------------------ MAIN ------------------
if __name__ == "__main__":
    afficher()
