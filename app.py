import streamlit as st

# 1. Configuration de la page
st.set_page_config(
    page_title="Mes Recettes",
    page_icon="🍳",
    layout="centered"
)

# 2. Style CSS pour mobile
st.markdown("""
    <style>
    div.stButton > button:first-child {
        height: 3.5em;
        border-radius: 12px;
        font-size: 16px;
        font-weight: bold;
        margin-bottom: 8px;
    }
    .stMainContainer {
        padding-top: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Interface
st.title("🍳 Mes Recettes")

# --- Lignes de boutons ---
if st.button("📥 Importer une recette", use_container_width=True):
    st.switch_page("pages/Importer.py")

if st.button("✍️ Saisir une recette", use_container_width=True):
    st.switch_page("pages/Saisir.py")

if st.button("📖 Mes recettes", use_container_width=True):
    st.switch_page("pages/Mes_Recettes.py")

st.divider()

# --- Grille du bas (2x2) ---
col1, col2 = st.columns(2)

with col1:
    if st.button("⚙️ Paramètres", use_container_width=True):
        st.switch_page("pages/Parametres.py")
    if st.button("🔗 Partager", use_container_width=True):
        st.switch_page("pages/Partager.py")

with col2:
    if st.button("💾 Sauvegarder / Importer", use_container_width=True):
        st.switch_page("pages/Sauver_Importer.py")
    if st.button("ℹ️ À propos", use_container_width=True):
        # Ici on peut soit changer de page, soit afficher un message direct
        st.toast("Version 1.0")
