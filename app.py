import streamlit as st

# 1. Configuration de la page (Doit être la TOUTE PREMIÈRE commande Streamlit)
st.set_page_config(
    page_title="Mes Recettes",
    page_icon="🍳",
    layout="centered"
)

# 2. Style CSS pour mobile (Corrigé avec unsafe_allow_html=True)
st.markdown("""
    <style>
    div.stButton > button:first-child {
        height: 3.5em;
        border-radius: 12px;
        font-size: 18px;
        font-weight: bold;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Contenu de l'interface
st.title("🍳 Mes Recettes")

st.subheader("Menu Principal")

if st.button("📥 Importer une recette", use_container_width=True):
    st.switch_page("pages/1_Importer.py")

if st.button("✍️ Saisir une recette", use_container_width=True):
    st.switch_page("pages/2_Saisir.py")

if st.button("📖 Mes recettes", use_container_width=True):
    st.switch_page("pages/3_Mes_Recettes.py")

col1, col2 = st.columns(2)
with col1:
    if st.button("⚙️ Paramètres", use_container_width=True):
        st.switch_page("pages/4_Parametres.py")
with col2:
    if st.button("🔗 Partager", use_container_width=True):
        st.switch_page("pages/5_Partager.py")

st.divider()
if st.button("ℹ️ À propos", use_container_width=True):
    st.info("Application de recettes mobile.")
