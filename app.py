import streamlit as st

# Configuration de la page
st.set_page_config(page_title="Mes Recettes", layout="centered")

# --- STYLE CSS PERSONNALISÉ ---
st.markdown("""
    <style>
    /* Fond de l'application (gris très léger pour faire ressortir le blanc) */
    .stApp {
        background-color: #F7F7F7;
    }

    /* Suppression des marges par défaut des colonnes */
    [data-testid="column"] {
        display: flex;
        justify-content: center;
    }

    /* Style des boutons Streamlit */
    div.stButton > button {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border: 1px solid #E0E0E0 !important;
        border-radius: 15px !important;
        height: 120px !important;
        width: 150px !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.05) !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        transition: all 0.3s ease !important;
        white-space: normal !important; /* Permet au texte de passer à la ligne */
        line-height: 1.2 !important;
    }

    /* Effet au survol / clic */
    div.stButton > button:hover {
        border-color: #CCCCCC !important;
        background-color: #FAFAFA !important;
        transform: translateY(-2px);
    }

    /* Titre centré */
    .main-title {
        text-align: center;
        color: #000000;
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 800;
        margin-bottom: 30px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CONTENU ---

st.markdown('<h1 class="main-title">Mes Recettes</h1>', unsafe_allow_html=True)

# Création d'une grille centrée (2 colonnes)
col1, col2 = st.columns(2)

with col1:
    if st.button("📥\nImporter une recette"):
        pass
    if st.button("📚\nMes recettes"):
        pass
    if st.button("💾\nSauvegarder / Importer"):
        pass
    if st.button("ℹ️\nA propos"):
        pass

with col2:
    if st.button("✍️\nSaisir une recette"):
        pass
    if st.button("⚙️\nParamètres"):
        pass
    if st.button("🔗\nPartager"):
        pass

# Pied de page discret
st.markdown("<br><p style='text-align: center; color: #AAAAAA; font-size: 12px;'>v 1.0</p>", unsafe_allow_html=True)
