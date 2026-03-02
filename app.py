import streamlit as st

# Importation depuis le dossier "pages"
from pages import Importer
from pages import Saisir
from pages import Mes_recettes
from pages import Parametres
from pages import Sauver_importer
from pages import Partager
from pages import A_propos

# Configuration de la page
st.set_page_config(page_title="Mesrecettes", page_icon="🍳", layout="centered")

# --- Logique de Navigation ---
if 'page' not in st.session_state:
    st.session_state.page = 'accueil'

def changer_page(nom_page):
    st.session_state.page = nom_page

# --- CONTENU DE LA PAGE D'ACCUEIL ---
if st.session_state.page == 'accueil':
    # Titre principal et style
    st.title("🍳 Mes recettes")
    st.write("---")

    ### --- Section 1 : Boutons sur une seule colonne (Pleine largeur) ---
    # Ces boutons sont parfaits pour les actions principales
    if st.button("📥 Importer une recette", use_container_width=True):
        st.info("Chargement du module d'importation...")
        changer_page("importer")

    if st.button("➕ Ajouter une recette", use_container_width=True):
        st.info("Ouverture du formulaire d'ajout...")
        changer_page("ajouter")
        
    if st.button("📚 Mes recettes", use_container_width=True):
        st.info("Accès à votre bibliothèque...")
        changer_page("liste")

    st.write("---")

    ### --- Section 2 : Boutons sur deux colonnes ---
    # Idéal pour trier par catégories de façon compacte
    col1, col2 = st.columns(2)

    with col1:        
        if st.button("⚙️ Paramètres", use_container_width=True):
            st.info("Réglages de l'application")
            changer_page("parametres")

        if st.button("💾 Sauvegarder / Importer", use_container_width=True):
            st.info("Gestion des sauvegardes")
            changer_page("sauvegarde")
            
    with col2:            
        if st.button("🔗 Partager", use_container_width=True):
            st.info("Options de partage")
            changer_page("partager")
     
        if st.button("ℹ️ A propos", use_container_width=True):
            st.info("Informations sur Mesrecettes")
            changer_page("propos")

# --- ROUTAGE VERS LES PAGES (SCRIPTS EXTERNES) ---
# Note : Chaque script doit contenir une fonction : def afficher():

elif st.session_state.page == "importer":
    importer_recette.afficher()
    if st.button("⬅️ Retour"): changer_page('accueil')

elif st.session_state.page == "ajouter":
    ajouter_recette.afficher()
    if st.button("⬅️ Retour"): changer_page('accueil')

elif st.session_state.page == "liste":
    mes_recettes.afficher()
    if st.button("⬅️ Retour"): changer_page('accueil')

elif st.session_state.page == "parametres":
    parametres.afficher()
    if st.button("⬅️ Retour"): changer_page('accueil')

elif st.session_state.page == "sauvegarde":
    sauver_importer.afficher()
    if st.button("⬅️ Retour"): changer_page('accueil')

elif st.session_state.page == "partager":
    partager.afficher()
    if st.button("⬅️ Retour"): changer_page('accueil')

elif st.session_state.page == "propos":
    a_propos.afficher()
    if st.button("⬅️ Retour"): changer_page('accueil')
