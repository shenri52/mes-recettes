import streamlit as st

# Configuration optimisée pour mobile
st.set_page_config(
    page_title="Mes Recettes",
    page_icon="🍳",
    layout="centered",  # Centré pour garder le contenu compact sur mobile
    initial_sidebar_state="collapsed" # Cache le menu pour gagner de la place au départ
)

# --- STYLE CSS PERSONNALISÉ (Pour de gros boutons tactiles) ---
st.markdown("""
    <style>
    div.stButton > button:first-child {
        height: 3em;
        border-radius: 10px;
        font-size: 18px;
        font-weight: bold;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_stdio=False)

# --- TITRE PRINCIPAL ---
st.title("🍳 Mes Recettes")
st.write("Votre carnet de cuisine de poche.")

st.divider()

# --- NAVIGATION PRINCIPALE (Format Liste Mobile) ---

# Section 1 : Création
st.subheader("➕ Nouvelle Recette")
if st.button("📥 Importer une recette", use_container_width=True):
    st.switch_page("pages/1_Importer.py")

if st.button("✍️ Saisir une recette", use_container_width=True):
    st.switch_page("pages/2_Saisir.py")

st.divider()

# Section 2 : Consultation
st.subheader("📚 Ma Collection")
if st.button("📖 Consulter Mes recettes", use_container_width=True):
    st.switch_page("pages/3_Mes_Recettes.py")

st.divider()

# Section 3 : Outils & Partage
st.subheader("🛠️ Outils")
col1, col2 = st.columns(2)
with col1:
    if st.button("💾 Sauvegarder", use_container_width=True):
        st.switch_page("pages/4_Sauvegarde.py")
    if st.button("⚙️ Paramètres", use_container_width=True):
        st.switch_page("pages/5_Parametres.py")
with col2:
    if st.button("🔗 Partager", use_container_width=True):
        st.switch_page("pages/6_Partager.py")
    if st.button("ℹ️ À propos", use_container_width=True):
        st.switch_page("pages/7_A_propos.py")
