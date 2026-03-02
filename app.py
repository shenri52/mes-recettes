import streamlit as st

# Configuration de la page
st.set_page_config(page_title="Mes Recettes", layout="centered")

# --- CSS RADICAL ET PROPRE ---
st.markdown("""
    <style>
    /* Fond de page gris clair pour faire ressortir les boutons blancs */
    .stApp {
        background-color: #F0F2F5;
    }

    /* Titre Noir, Gras, Centré */
    .titre-app {
        color: #000000;
        text-align: center;
        font-size: 2.5rem;
        font-weight: 800;
        margin-bottom: 20px;
    }

    /* BOUTONS : Fond Blanc, Texte Noir, Centrés, Arrondis */
    div.stButton > button {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border: none !important;
        border-radius: 15px !important;
        width: 100% !important;
        height: 100px !important;
        font-size: 18px !important;
        font-weight: bold !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
        display: block !important;
        margin: 0 auto !important;
    }

    /* Ajustement de l'espacement des colonnes pour mobile */
    [data-testid="column"] {
        padding: 5px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CORPS DE L'APPLICATION ---

st.markdown('<h1 class="titre-app">Mes Recettes</h1>', unsafe_allow_html=True)

# Grille de boutons 2x2
col1, col2 = st.columns(2)

with col1:
    if st.button("📥\nImporter"):
        st.write("Import")
    if st.button("📚\nMes recettes"):
        st.write("Liste")
    if st.button("💾\nSauvegarde"):
        st.write("Save")

with col2:
    if st.button("✍️\nSaisir"):
        st.write("Saisie")
    if st.button("⚙️\nParamètres"):
        st.write("Réglages")
    if st.button("🔗\nPartager"):
        st.write("Partage")

# Bouton large en bas
st.write("---")
if st.button("ℹ️ A propos"):
    st.info("Version 1.0 - Épurée")
