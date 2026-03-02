import streamlit as st

# 1. Configuration de la page
st.set_page_config(
    page_title="Mes Recettes",
    page_icon="🍳",
    layout="centered",
    initial_sidebar_state="collapsed" # Cache la barre au chargement
)

# 2. Style CSS pour mobile ET pour CACHER le menu de gauche
st.markdown("""
    <style>
    /* Cache le bouton du menu de gauche (hamburger) */
    [data-testid="stSidebarNav"] {display: none;}
    [data-testid="openSidebarNavigation"] {display: none;}
    
    /* Style des boutons */
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
    st.switch_page("pages/1_Importer.py")

if st.button("✍️ Saisir une recette", use_container_width=True):
    st.switch_page("pages/2_Saisir.py")

if st.button("📖 Mes recettes", use_container_width=True):
    st.switch_page("pages/3_Mes_Recettes.py")

st.divider()

# --- Grille du bas (2x2) ---
col1, col2 = st.columns(2)

with col1:
    if st.button("⚙️ Paramètres", use_container_width=True):
        st.switch_page("pages/4_Parametres.py")
    if st.button("🔗 Partager", use_container_width=True):
        st.switch_page("pages/6_Partager.py")

with col2:
    if st.button("💾 Sauvegarder / Importer", use_container_width=True):
        st.switch_page("pages/5_Sauvegarde.py")
    if st.button("ℹ️ À propos", use_container_width=True):
        st.switch_page("pages/7_A_propos.py") # <-- Nouveau lien
