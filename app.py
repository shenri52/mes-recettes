import streamlit as st

# 1. Configuration de la page
st.set_page_config(
    page_title="Mes Recettes",
    page_icon="🍳",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 2. CSS pour cacher le menu et styliser les boutons centraux
st.markdown("""
    <style>
    /* Cache le menu latéral */
    [data-testid="stSidebar"], .stSidebar {display: none;}
    [data-testid="openSidebarNavigation"] {display: none;}
    
    /* Supprime les marges inutiles en haut */
    .block-container {
        padding-top: 2rem;
    }

    /* Style des boutons : Pleine largeur, arrondis et hauts */
    div.stButton > button:first-child {
        width: 100%;
        height: 4em;
        border-radius: 15px;
        font-size: 18px;
        font-weight: bold;
        margin-bottom: 15px;
        border: 1px solid #ddd;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Interface - Titre
st.title("🍳 Mes Recettes")
st.write("---")

# 4. Liste des boutons (uniquement au milieu)
if st.button("📥 Importer une recette"):
    st.switch_page("pages/1_Importer.py")

if st.button("✍️ Saisir une recette"):
    st.switch_page("pages/2_Saisir.py")

if st.button("📖 Mes recettes"):
    st.switch_page("pages/3_Mes_Recettes.py")

if st.button("⚙️ Paramètres"):
    st.switch_page("pages/4_Parametres.py")

if st.button("💾 Sauvegarder / Importer"):
    st.switch_page("pages/5_Sauvegarde.py")

if st.button("🔗 Partager"):
    st.switch_page("pages/6_Partager.py")

if st.button("ℹ️ À propos"):
    st.switch_page("pages/7_A_propos.py")
