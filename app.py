import streamlit as st

# --- 1. Imports ---
import importer, saisir, recettes

# Configuration
st.set_page_config(page_title="Mesrecettes", page_icon="🍳", layout="centered")

# --- Initialisation et Fonction ---
if 'page' not in st.session_state:
    st.session_state.page = 'accueil'

def changer_page(nom):
    st.session_state.page = nom
    st.rerun()

# --- 2. Menu d'accueil ---
if st.session_state.page == 'accueil':
    st.markdown("<h1 style='text-align: center;'>🍳 Mes recettes</h1>", unsafe_allow_html=True)
    st.write("---")

    if st.button("📥 Importer une recette", use_container_width=True):
        changer_page("importer")
    if st.button("✍️ Ajouter une recette", use_container_width=True):
        changer_page("ajouter")
    if st.button("📚 Mes recettes", use_container_width=True):
        changer_page("recettes")

# --- 3. Routage (Contenu de la page) ---
else:
    # On affiche le contenu de la page demandée
    if st.session_state.page == "importer":
        importer.afficher()
    elif st.session_state.page == "ajouter":
        saisir.afficher()
    elif st.session_state.page == "recettes":
        recettes.afficher()

    # --- 4. BOUTON RETOUR (Toujours en bas des pages secondaires) ---
    if st.button("⬅️ Retour à l'accueil", use_container_width=True):
        changer_page('accueil')
