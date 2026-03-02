import streamlit as st

# 1. Configuration (TOUJOURS EN PREMIER)
st.set_page_config(
    page_title="Mes Recettes",
    page_icon="🍳",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 2. CSS Ciblé (Uniquement pour le menu et le style des boutons)
st.markdown("""
    <style>
    /* Cache uniquement la navigation latérale */
    [data-testid="stSidebar"], .stSidebar {
        display: none;
    }
    /* Supprime la marge de la barre latérale pour centrer le contenu */
    .stMain {
        margin-left: 0px;
    }
    /* Style des gros boutons pour mobile */
    div.stButton > button:first-child {
        height: 3.8em;
        border-radius: 15px;
        font-size: 16px;
        font-weight: bold;
        margin-bottom: 10px;
        width: 100%;
        background-color: #f0f2f6;
        border: 1px solid #d1d5db;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Interface - Titre
st.title("🍳 Mes Recettes")

# --- BLOC CENTRAL : Les boutons principaux ---
# On les met dans un conteneur pour s'assurer qu'ils s'affichent
with st.container():
    if st.button("📥 Importer une recette"):
        st.switch_page("pages/1_Importer.py")

    if st.button("✍️ Saisir une recette"):
        st.switch_page("pages/2_Saisir.py")

    if st.button("📖 Mes recettes"):
        st.switch_page("pages/3_Mes_Recettes.py")

st.divider()

# --- BLOC BAS : Grille 2x2 ---
col1, col2 = st.columns(2)

with col1:
    if st.button("⚙️ Paramètres"):
        st.switch_page("pages/4_Parametres.py")
    if st.button("🔗 Partager"):
        st.switch_page("pages/6_Partager.py")

with col2:
    if st.button("💾 Sauv. / Importer"):
        st.switch_page("pages/5_Sauvegarde.py")
    if st.button("ℹ️ À propos"):
        st.switch_page("pages/7_A_propos.py")
