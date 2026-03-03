import streamlit as st
import importlib

# --- 1. Imports ---
from pages import Importer, Saisir, Recettes, Parametres, Sauvegarder, Partager, Propos

# On force le rechargement des modules pour que tes changements de texte apparaissent
importlib.reload(Propos)
importlib.reload(Saisir)
importlib.reload(Recettes)

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
        changer_page("Importer")

    if st.button("➕ Ajouter une recette", use_container_width=True):
        changer_page("Ajouter")
        
    if st.button("📚 Mes recettes", use_container_width=True):
        changer_page("Recettes")

    st.write("---")
    col1, col2 = st.columns(2)

    with col1:        
        if st.button("⚙️ Paramètres", use_container_width=True):
            changer_page("Parametres")
        if st.button("💾 Sauvegarder / Importer", use_container_width=True):
            changer_page("Sauvegarder")
            
    with col2:            
        if st.button("🔗 Partager", use_container_width=True):
            changer_page("Partager")
        if st.button("ℹ️ A propos", use_container_width=True):
            changer_page("Propos")

# --- 3. Routage ---
# Ici, plus besoin de boutons retour, ils sont gérés au-dessus !

elif st.session_state.page == "Importer":
    Importer.afficher()

elif st.session_state.page == "Ajouter":
    Saisir.afficher()

elif st.session_state.page == "Recettes":
    Recettes.afficher()

elif st.session_state.page == "Parametres":
    Parametres.afficher()

elif st.session_state.page == "Sauvegarder":
    Sauvegarder.afficher()

elif st.session_state.page == "Partager":
    Partager.afficher()

elif st.session_state.page == "Propos":
    Propos.afficher()
