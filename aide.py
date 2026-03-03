# Dans le fichier aide.py
import streamlit as st

def afficher():
    st.subheader("💡 Aide")
    # ... ton contenu ...

# --- MESSAGE D'INFORMATION ---
    st.info("Les modifications (ajout, édition, suppression) ne sont pas instantanées. "
            "Un délai de quelques secondes à une minute peut être nécessaire pour que GitHub mette à jour les données.")
