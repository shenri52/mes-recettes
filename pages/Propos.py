import streamlit as st

def main():
    st.title("À propos de ce projet")
    
    st.divider() # Ajoute une ligne de séparation horizontale

    # Utilisation de colonnes ou d'une liste stylisée
    st.subheader("L'équipe derrière l'application")

    st.markdown(
        """
        * **Idée originale :** Stéphanie HENRI
        * **Prompteur :** Samuel HENRI
        * **Développement & Code :** Gemini (Google)
        """
    )

    st.info("Ce projet a été conçu pour allier créativité humaine et puissance de l'IA.")

if __name__ == "__main__":
    main()
