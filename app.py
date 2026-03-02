import streamlit as st

# --- 1. Tes Imports (Les noms des fichiers .py dans /pages) ---
from pages import Importer
from pages import Saisir
from pages import Recettes
from pages import Parametres
from pages import Sauvegarder
from pages import Partager
from pages import Propos

# Configuration de la page
st.set_page_config(page_title="Mesrecettes", page_icon="🍳", layout="centered")

if 'page' not in st.session_state:
    st.session_state.page = 'accueil'

def changer_page(nom_page):
    st.session_state.page = nom_page

# --- 2. Menu d'accueil ---
if st.session_state.page == 'accueil':
    st.title("🍳 Mes recettes")
    st.write("---")

    if st.button("📥 Importer une recette", use_container_width=True):
        changer_page("importer")

    if st.button("➕ Ajouter une recette", use_container_width=True):
        changer_page("ajouter")
        
    if st.button("📚 Mes recettes", use_container_width=True):
        changer_page("liste")

    st.write("---")
    col1, col2 = st.columns(2)

    with col1:        
        if st.button("⚙️ Paramètres", use_container_width=True):
            changer_page("parametres")
        if st.button("💾 Sauvegarder / Importer", use_container_width=True):
            changer_page("sauvegarde")
            
    with col2:            
        if st.button("🔗 Partager", use_container_width=True):
            changer_page("partager")
        if st.button("ℹ️ A propos", use_container_width=True):
            changer_page("propos")

# --- 3. Routage (Correction des noms ici) ---

elif st.session_state.page == "importer":
    Importer.afficher()    # Utilise 'Importer' (nom du fichier importé)
    if st.button("⬅️ Retour"): changer_page('accueil')

elif st.session_state.page == "ajouter":
    Saisir.afficher()      # Utilise 'Saisir' (nom du fichier importé)
    if st.button("⬅️ Retour"): changer_page('accueil')

elif st.session_state.page == "liste":
    Recettes.afficher()    # Utilise 'Recettes' (nom du fichier importé)
    if st.button("⬅️ Retour"): changer_page('accueil')

elif st.session_state.page == "parametres":
    Parametres.afficher()
    if st.button("⬅️ Retour"): changer_page('accueil')

elif st.session_state.page == "sauvegarde":
    Sauvegarder.afficher()
    if st.button("⬅️ Retour"): changer_page('accueil')

elif st.session_state.page == "partager":
    Partager.afficher()
    if st.button("⬅️ Retour"): changer_page('accueil')

elif st.session_state.page == "propos":
    Propos.afficher()
    if st.button("⬅️ Retour"): changer_page('accueil')
