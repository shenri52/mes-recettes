import streamlit as st

# --- 1. Tes Imports (Les noms des fichiers .py) ---
import Propos

# Configuration de la page
st.set_page_config(page_title="Mesrecettes", page_icon="🍳", layout="centered")

if 'page' not in st.session_state:
    st.session_state.page = 'accueil'

# Fonction pour changer de page
def changer_page(nom_page):
    st.session_state.page = nom_page

# --- 2. Menu d'accueil ---
if st.session_state.page == 'accueil':
    st.title("🍳 Mes recettes")
    st.write("---")

    if st.button("📥 Importer une recette", use_container_width=True):
        changer_page("Importer")
        # Forcer le rafraîchissement pour n'avoir qu'un clic
        st.rerun() 

    if st.button("➕ Ajouter une recette", use_container_width=True):
        changer_page("Ajouter")
        # Forcer le rafraîchissement pour n'avoir qu'un clic
        st.rerun()
        
    if st.button("📚 Mes recettes", use_container_width=True):
        changer_page("Recettes")
        # Forcer le rafraîchissement pour n'avoir qu'un clic
        st.rerun()

    st.write("---")
    col1, col2 = st.columns(2)

    with col1:        
        if st.button("⚙️ Paramètres", use_container_width=True):
            changer_page("Parametres")
            # Forcer le rafraîchissement pour n'avoir qu'un clic
            st.rerun()
        if st.button("💾 Sauvegarder / Importer", use_container_width=True):
            changer_page("Sauvegarder")
            # Forcer le rafraîchissement pour n'avoir qu'un clic
            st.rerun()
            
    with col2:            
        if st.button("🔗 Partager", use_container_width=True):
            changer_page("Partager")
            # Forcer le rafraîchissement pour n'avoir qu'un clic
            st.rerun()
        if st.button("ℹ️ A propos", use_container_width=True):
            changer_page("Propos")
            # Forcer le rafraîchissement pour n'avoir qu'un clic
            st.rerun()

