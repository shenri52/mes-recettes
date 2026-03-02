import streamlit as st

# 1. Config & Masquage menu
st.set_page_config(page_title="Importer", layout="centered")
st.markdown("<style>[data-testid='stSidebar'] {display: none;} [data-testid='openSidebarNavigation'] {display: none;}</style>", unsafe_allow_html=True)

# 2. Bouton Retour
if st.button("⬅️ Retour au menu"):
    st.switch_page("app.py")

st.title("📥 Importer une recette")

# 3. Options d'importation
st.subheader("Depuis le Web")
url = st.text_input("Collez le lien de la recette (Marmiton, Cuisine AZ, etc.)")
if st.button("Analyser le lien"):
    st.info(f"Analyse de l'URL : {url} (Fonctionnalité à venir)")

st.divider()

st.subheader("Depuis un fichier")
uploaded_file = st.file_uploader("Choisissez un fichier (PDF ou Image)", type=["pdf", "jpg", "png"])
if uploaded_file is not None:
    st.success("Fichier reçu !")
