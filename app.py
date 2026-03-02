import streamlit as st

# Configuration optimisée pour mobile
st.set_page_config(page_title="Mes Recettes", layout="centered")

# --- DESIGN "MOBILE FIRST" ---
st.markdown("""
    <style>
    /* Fond de l'écran plus doux */
    .stApp {
        background-color: #F8F9FA;
    }

    /* Suppression des éléments parasites de Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Style des boutons : Fond Blanc, Texte Noir, Ombre légère */
    div.stButton > button {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border-radius: 20px !important;
        border: none !important;
        height: 110px !important;
        width: 100% !important;
        margin-bottom: 10px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08) !important;
        font-size: 16px !important;
        font-weight: 500 !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
    }

    /* Effet tactile au clic */
    div.stButton > button:active {
        background-color: #F0F0F0 !important;
        transform: scale(0.98);
    }

    /* Centrage du titre */
    .title-container {
        text-align: center;
        padding: 20px 0;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }
    </style>
    """, unsafe_allow_html=True)

# --- TITRE ---
st.markdown('<div class="title-container"><h1>🍳 Mes Recettes</h1></div>', unsafe_allow_html=True)

# --- GRILLE DE BOUTONS ---
# On utilise 2 colonnes pour l'aspect "App"
col1, col2 = st.columns(2)

with col1:
    if st.button("📥\nImporter"):
        st.write("Action : Importer")
    
    if st.button("📚\nMes recettes"):
        st.write("Action : Mes recettes")

    if st.button("💾\nSauvegarder"):
        st.write("Action : Sauvegarder")

with col2:
    if st.button("✍️\nSaisir"):
        st.write("Action : Saisir")

    if st.button("⚙️\nParamètres"):
        st.write("Action : Paramètres")

    if st.button("🔗\nPartager"):
        st.write("Action : Partager")

# Bouton "A propos" centré en bas (plus large)
st.write("---")
if st.button("ℹ️ A propos"):
    st.info("Mes Recettes v1.0 - Votre carnet de cuisine digital.")
