# --- STYLE CSS PERSONNALISÉ (Pour mobile) ---
st.markdown("""
    <style>
    /* On rend les boutons plus grands pour le tactile */
    div.stButton > button:first-child {
        height: 3.5em;
        border-radius: 12px;
        font-size: 18px;
        font-weight: bold;
        margin-bottom: 10px;
        border: 1px solid #ff4b4b;
    }
    /* Optimisation de l'espacement sur petit écran */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    </style>
    """, unsafe_allow_html=True) # <-- C'était ici l'erreur !
