import streamlit as st

def afficher():
    st.divider()
    st.subheader("Crédits & Collaboration")
    
    # Mise en page propre avec des colonnes ou du Markdown
    st.markdown(
        """
        * **Idée originale :** Stéphanie HENRI
        * **Prompteur :** Samuel HENRI
        * **Code :** Gemini
        """
    )
    st.info("Ce projet est le fruit d'une collaboration entre l'humain et l'intelligence artificielle.")
