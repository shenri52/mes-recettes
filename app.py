import streamlit as st

# Configuration de la page
st.set_page_config(page_title="Mesrecettes", page_icon="🍳", layout="centered")

# Titre principal et style
st.title("🍳 Bienvenue sur Mesrecettes")
st.subheader("Quelle délicieuse préparation allons-nous cuisiner aujourd'hui ?")
st.write("---")

# Création des colonnes pour organiser les boutons de manière esthétique
# On peut faire une grille de 2 ou 3 colonnes
col1, col2 = st.columns(2)

with col1:
    if st.button("🌟 Bouton Personnalisé 1", use_container_width=True):
        st.info("Action pour le bouton 1")
        
    if st.button("🥗 Bouton Personnalisé 2", use_container_width=True):
        st.info("Action pour le bouton 2")
        
    if st.button("🍰 Bouton Personnalisé 3", use_container_width=True):
        st.info("Action pour le bouton 3")
        
    if st.button("⏱️ Bouton Personnalisé 4", use_container_width=True):
        st.info("Action pour le bouton 4")

with col2:
    if st.button("🥩 Bouton Personnalisé 5", use_container_width=True):
        st.info("Action pour le bouton 5")
        
    if st.button("🥦 Bouton Personnalisé 6", use_container_width=True):
        st.info("Action pour le bouton 6")
        
    if st.button("🍷 Bouton Personnalisé 7", use_container_width=True):
        st.info("Action pour le bouton 7")

# Footer simple
st.write("---")
st.caption("Fait avec ❤️ pour les passionnés de cuisine.")
