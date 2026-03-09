import streamlit as st
import importer, saisir, recettes, stats, maintenance, planning

# Configuration
st.set_page_config(page_title="Mesrecettes", page_icon="🍳", layout="centered")

# --- FONCTION DE PROTECTION ---
def verifier_mot_de_passe():
    if "authentifie" not in st.session_state:
        st.session_state["authentifie"] = False

    if not st.session_state["authentifie"]:
        st.markdown("<h1 style='text-align: center;'>🔒 Accès réservé</h1>", unsafe_allow_html=True)
        # On utilise st.secrets pour ne pas afficher le MDP dans le code public
        mdp_saisi = st.text_input("Veuillez saisir le mot de passe :", type="password")
        if st.button("Se connecter", use_container_width=True):
            if mdp_saisi == st.secrets["APP_PASSWORD"]:
                st.session_state["authentifie"] = True
                st.rerun()
            else:
                st.error("Mot de passe incorrect")
        return False
    return True

# --- EXÉCUTION DE L'APPLICATION ---
if verifier_mot_de_passe():
    # --- Initialisation et Fonction ---
    if 'page' not in st.session_state:
        st.session_state.page = 'accueil'

    def changer_page(nom):
        st.session_state.page = nom
        st.rerun()

    # --- 2. Menu d'accueil ---
    if st.session_state.page == 'accueil':
        st.markdown("<h1 style='text-align: center;'>🍳 Mes recettes</h1>", unsafe_allow_html=True)

        st.divider()

        # Ligne 1 : Bouton principal
        if st.button("📚 Mes recettes", use_container_width=True):
            changer_page("recettes")
        
        # Ligne 2 : Sur 2 colonnes
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📥 Importer une recette", use_container_width=True):
                changer_page("importer")
        with col2:
            if st.button("✍️ Saisir une recette", use_container_width=True):
                changer_page("ajouter")

        # Ligne 3 : Planning
        if st.button("📅 Mon planning", use_container_width=True):
            changer_page("planning")

        # Ligne 4 : Sur 2 colonnes
        col3, col4 = st.columns(2)
        with col3:
            if st.button("📊 Statistiques", use_container_width=True):
                changer_page("stats")
        with col4:
            if st.button("🛠️ Maintenance", use_container_width=True):
                changer_page("maintenance")

    # --- 3. Routage (Contenu de la page) ---
    else:
        if st.session_state.page == "importer":
            importer.afficher()
        elif st.session_state.page == "ajouter":
            saisir.afficher()
        elif st.session_state.page == "recettes":
            recettes.afficher()
        elif st.session_state.page == "stats":
            stats.afficher()
        elif st.session_state.page == "planning":
            planning.afficher()
        elif st.session_state.page == "maintenance":
            maintenance.afficher()

        # --- 4. BOUTON RETOUR ---
        if st.button("⬅️ Retour à l'accueil", use_container_width=True):
            changer_page('accueil')
