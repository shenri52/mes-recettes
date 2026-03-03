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
# S'affiche sur toutes les pages SAUF l'accueil
if st.session_state.page != 'accueil':
    if st.button("⬅️ Retour à l'accueil"):
        changer_page('accueil')

# --- 2. Menu d'accueil ---
if st.session_state.page == 'accueil':
    st.title("🍳 Mes recettes")
    st.write("---")

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
# Ici, plus besoin de boutons retour, ils sont gérés au-dessus !

elif st.session_state.page == "Importer":
    importer.afficher()

elif st.session_state.page == "Ajouter":
    saisir.afficher()

elif st.session_state.page == "Recettes":
    recettes.afficher()

elif st.session_state.page == "Parametres":
    parametres.afficher()

elif st.session_state.page == "Sauvegarder":
    sauvegarder.afficher()

elif st.session_state.page == "propos":
    propos.afficher()
