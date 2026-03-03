import streamlit as st

   
def afficher():
    st.write("---")
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

    st.write("---")
    
    st.write("""
    ### Pourquoi cette application ?
    
    **Mesrecettes** est née d'un constat simple : la plupart des applications de cuisine actuelles sont soit trop complexes, soit saturées de publicités, soit ne permettent pas une gestion vraiment libre de ses propres découvertes.
    
    Cette application a été développée spécifiquement pour **répondre à un besoin non satisfait par les solutions existantes** : offrir un outil épuré, rapide et entièrement personnalisé pour centraliser, saisir et partager vos recettes préférées sans contraintes.
    
    ---
    
    ### Les engagements de l'appli :
    * **Simplicité** : Pas de fonctions inutiles, on va à l'essentiel.
    * **Liberté** : Vous gérez vos données comme vous l'entendez.
    * **Efficacité** : Une interface pensée pour la rapidité, que ce soit en cuisine ou en déplacement.
    """)
    
    st.write("---")
    
    st.info("Ce projet est le fruit d'une collaboration entre l'humain et l'intelligence artificielle.")

if st.button("⬅️ Retour", use_container_width=True):
    st.session_state.page = 'app'
    # Forcer le rafraîchissement pour n'avoir qu'un clic
    st.rerun()
