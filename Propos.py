import streamlit as st

def afficher():
    st.markdown("---")
    st.subheader("Crédits du Projet")
    
    # Utilisation de colonnes pour une présentation plus pro
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("💡 **Idée originale :**")
        st.write("✍️ **Prompteur :**")
        st.write("🤖 **Code :**")
        
    with col2:
        st.write("Stéphanie HENRI")
        st.write("Samuel HENRI")
        st.write("Gemini")
    
    st.info("Ce projet est le fruit d'une collaboration entre l'humain et l'intelligence artificielle.")
