import streamlit as st

# Configuration de la page pour mobile
st.set_page_config(page_title="Mes Recettes", page_icon="🍳", layout="centered")

# --- STYLE CSS (Le secret du look App) ---
st.markdown("""
    <style>
    /* Fond de l'application */
    .stApp {
        background-color: #F2F2F7;
    }

    /* Conteneur de la grille */
    .main-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 15px;
        padding: 10px;
    }

    /* Style des boutons personnalisés */
    .app-button {
        background-color: white;
        border-radius: 20px;
        padding: 25px 10px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        transition: transform 0.2s;
        cursor: pointer;
        border: none;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-decoration: none;
        color: #1C1C1E !important;
    }

    .app-button:active {
        transform: scale(0.95);
        background-color: #E5E5EA;
    }

    .icon {
        font-size: 28px;
        margin-bottom: 8px;
    }

    .label {
        font-family: 'Segoe UI', Roboto, Helvetica;
        font-size: 14px;
        font-weight: 600;
    }

    /* Titre personnalisé */
    .app-title {
        text-align: center;
        font-family: 'Segoe UI', sans-serif;
        font-weight: 800;
        color: #000000;
        margin-top: 20px;
        margin-bottom: 30px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- HEADER ---
st.markdown('<h1 class="app-title">🍳 Mes Recettes</h1>', unsafe_allow_html=True)

# --- CORPS DE L'INTERFACE (Grille de boutons) ---
# Note : Comme Streamlit ne gère pas nativement les clics sur du HTML personnalisé facilement, 
# on utilise des colonnes Streamlit classiques mais stylisées via le CSS injecté plus haut.

def draw_button(icon, label):
    # On utilise un bouton Streamlit classique qu'on va "hacker" visuellement
    if st.button(f"{icon}\n\n{label}", key=label):
        st.toast(f"Ouverture de : {label}")

col1, col2 = st.columns(2)

with col1:
    draw_button("📥", "Importer une recette")
    draw_button("📚", "Mes recettes")
    draw_button("💾", "Sauvegarder / Importer")
    draw_button("ℹ️", "A propos")

with col2:
    draw_button("✍️", "Saisir une recette")
    draw_button("⚙️", "Paramètres")
    draw_button("🔗", "Partager")

# --- PIED DE PAGE ---
st.markdown("<br><p style='text-align: center; color: #8E8E93; font-size: 12px;'>Version 1.2.0</p>", unsafe_allow_html=True)
