import streamlit as st

def afficher():
    st.subheader("A propos du projet")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("💡 **Idée originale :**")
        st.write("✍️ **Prompteur :**")
        st.write("💻 **Code :**")
        
    with col2:
        st.write("Stéphanie HENRI")
        st.write("Samuel HENRI")
        st.write("Gemini")
    
    st.markdown("""
    ### Pourquoi cette application ?
    
    **Mesrecettes** est née d'un constat simple : la plupart des applications de cuisine actuelles sont soit trop complexes, soit saturées de publicités.
    
    Cette application a été développée spécifiquement pour **répondre à un besoin non satisfait par les solutions existantes** : offrir un outil épuré, rapide et entièrement personnalisé pour centraliser vos recettes sans contraintes.
    
    *Ce projet est le fruit d'une collaboration entre l'humain et l'intelligence artificielle.*
    """)
