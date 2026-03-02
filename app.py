import streamlit as st

# Configuration de la page
st.set_page_config(page_title="Mes Recettes", page_icon="🍳", layout="centered")

# CSS personnalisé pour un look "App Mobile"
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        height: 100px;
        border-radius: 15px;
        border: 1px solid #eee;
        background-color: #ffffff;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
        font-size: 18px;
        font-weight: bold;
    }
    .main {
        background-color: #f8f9fa;
    }
    </style>
    """, unsafe_allow_html=True)

# Titre principal
st.markdown("<h1 style='text-align: center; color: #E63946;'>🍳 Mes Recettes</h1>", unsafe_allow_html=True)
st.write("---")

# Grille de boutons (2 colonnes pour l'aspect mobile)
col1, col2 = st.columns(2)

with col1:
    if st.button("📥\n\nImporter"):
        st.info("Fonction d'importation")
        
    if st.button("📚\n\nMes recettes"):
        st.info("Ouverture du carnet")

    if st.button("💾\n\nSauvegarder"):
        st.info("Exportation des données")

with col2:
    if st.button("✍️\n\nSaisir"):
        st.info("Nouvelle recette")

    if st.button("⚙️\n\nParamètres"):
        st.info("Réglages")

    if st.button("🔗\n\nPartager"):
        st.info("Partage en cours...")

# Bouton large pour le "À propos" en bas
st.write("")
if st.button("ℹ️ À propos"):
    st.write("Version 1.0 - Créé pour les passionnés de cuisine.")

# Barre de navigation simulée ou pied de page
st.markdown("<br><p style='text-align: center; color: gray; font-size: 0.8em;'>Fait avec ❤️ pour ta cuisine</p>", unsafe_allow_html=True)
