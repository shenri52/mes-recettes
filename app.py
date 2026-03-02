import streamlit as st

# --- 1. Tes Imports (Les noms des fichiers .py ) ---
import Propos

# Configuration de la page
st.set_page_config(page_title="Mesrecettes", page_icon="🍳", layout="centered")

if 'page' not in st.session_state:
    st.session_state.page = 'accueil'

def changer_page(nom_page):
    st.session_state.page = nom_page
    st.rerun()

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

# --- 3. Routage (Correction des noms ici) ---

elif st.session_state.page == "Importer":
    Importer.afficher()    # Utilise 'Importer' (nom du fichier importé)
    if st.button("⬅️ Retour"): changer_page('accueil')

elif st.session_state.page == "Ajouter":
    Saisir.afficher()      # Utilise 'Saisir' (nom du fichier importé)
    if st.button("⬅️ Retour"): changer_page('accueil')

elif st.session_state.page == "Recettes":
    Recettes.afficher()    # Utilise 'Recettes' (nom du fichier importé)
    if st.button("⬅️ Retour"): changer_page('accueil')

elif st.session_state.page == "Parametres":
    Parametres.afficher()
    if st.button("⬅️ Retour"): changer_page('accueil')

elif st.session_state.page == "Sauvegarder":
    Sauvegarder.afficher()
    if st.button("⬅️ Retour"): changer_page('accueil')

elif st.session_state.page == "Partager":
    Partager.afficher()
    if st.button("⬅️ Retour"): changer_page('accueil')

elif st.session_state.page == "Propos":
    Propos.afficher()
    if st.button("⬅️ Retour"): changer_page('accueil')
