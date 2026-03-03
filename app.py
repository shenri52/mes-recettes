import streamlit as st

# --- 1. Imports ---
import importer, saisir, recettes, parametres, sauvegarder, propos

# Configuration
st.set_page_config(page_title="Mesrecettes", page_icon="🍳", layout="centered")

# --- Initialisation et Fonction ---
if 'page' not in st.session_state:
    st.session_state.page = 'accueil'

def changer_page(nom):
    st.session_state.page = nom
    st.rerun()

# --- BOUTON RETOUR UNIQUE ---
if st.session_state.page != 'accueil':
    if st.button("⬅️ Retour à l'accueil"):
        changer_page('accueil')
    st.write("---") 

# --- 2. Menu d'accueil ---
if st.session_state.page == 'accueil':
    # Titre centré
    st.markdown("<h1 style='text-align: center;'>🍳 Mes recettes</h1>", unsafe_allow_html=True)
    st.write("---")

    # TOUS LES BOUTONS CI-DESSOUS DOIVENT ÊTRE DÉCALÉS (INDENTÉS)
    if st.button("📥 Importer une recette", use_container_width=True):
        changer_page("importer")

    if st.button("➕ Ajouter une recette", use_container_width=True):
        changer_page("ajouter")
        
    if st.button("📚 Mes recettes", use_container_width=True):
        changer_page("recettes")

    if st.button("💾 Sauvegarder / Importer", use_container_width=True):
        changer_page("sauvegarder")

    if st.button("⚙️ Paramètres", use_container_width=True):
        changer_page("parametres")

    if st.button("ℹ️ A propos", use_container_width=True):
        changer_page("propos")

# --- 3. Routage ---
# Le "elif" est aligné sur le "if" de la ligne 21
elif st.session_state.page == "importer":
    importer.afficher()

elif st.session_state.page == "ajouter":
    saisir.afficher()

elif st.session_state.page == "recettes":
    recettes.afficher()

elif st.session_state.page == "parametres":
    parametres.afficher()

elif st.session_state.page == "sauvegarder":
    sauvegarder.afficher()

elif st.session_state.page == "propos":
    propos.afficher()
