import streamlit as st
import streamlit.components.v1 as components
# Importation des modules (chaque fichier contient une fonction afficher())
import importer, saisir, recettes, stats, maintenance, planning, coursesaisir, coursevisualiser

# Configuration de l'onglet du navigateur
st.set_page_config(page_title="Mesrecettes", page_icon="🍳", layout="centered")

# --- FONCTION DE PROTECTION ---
def verifier_mot_de_passe():
    """Vérifie l'identité via le mot de passe stocké dans les secrets."""
    if "authentifie" not in st.session_state:
        st.session_state["authentifie"] = False

    if not st.session_state["authentifie"]:
        st.markdown("<h1 style='text-align: center;'>🔒 Accès réservé</h1>", unsafe_allow_html=True)
        # Saisie sécurisée sans afficher le MDP en clair dans le code source
        mdp_saisi = st.text_input("Veuillez saisir le mot de passe :", type="password")
        if st.button("Se connecter", use_container_width=True):
            if mdp_saisi == st.secrets["APP_PASSWORD"]:
                st.session_state["authentifie"] = True
                st.rerun() # Recharge l'application pour accéder au menu
            else:
                st.error("Mot de passe incorrect")
        return False
    return True

# --- EXÉCUTION DE L'APPLICATION ---
if verifier_mot_de_passe():
    # Initialisation de la page d'accueil si aucune page n'est définie
    if 'page' not in st.session_state:
        st.session_state.page = 'accueil'

    def changer_page(nom):
        """Change la page active dans le session_state et rafraîchit l'affichage."""
        st.session_state.page = nom
        st.rerun()

    # --- BLOC ANTI-VEILLE (Centralisé) ---
    # Pages sur lesquelles on active l'option de maintien de connexion
    PAGES_CUISINE = ["planning", "recettes", "ajouter", "coursesaisir", "coursevisualiser"]

    if st.session_state.page in PAGES_CUISINE:
        mode_cuisine = st.checkbox("🚫 Garder l'application connectée", value=False)
        if mode_cuisine:
            # Astuce HTML : une vidéo invisible force le navigateur à rester actif
            components.html(
                """
                <div style="display:none;">
                    <video autoplay loop muted playsinline style="width:1px; height:1px;">
                        <source src="https://raw.githubusercontent.com/anars/blank-audio/master/250-milliseconds-of-silence.mp3" type="video/mp4">
                    </video>
                </div>
                """,
                height=0
            )

    # --- MENU D'ACCUEIL ---
    if st.session_state.page == 'accueil':
        st.markdown("<h1 style='text-align: center;'>🍳 Mes recettes</h1>", unsafe_allow_html=True)
        st.divider()

        # Navigation via boutons principaux
        if st.button("📚 Mes recettes", use_container_width=True):
            changer_page("recettes")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📥 Importer une recette", use_container_width=True):
                changer_page("importer")
        with col2:
            if st.button("✍️ Créer une recette", use_container_width=True):
                changer_page("ajouter")

        if st.button("📅 Mon planning", use_container_width=True):
            changer_page("planning")
        if st.button("📝 Liste des courses", use_container_width=True):
            changer_page("coursesaisir")
        if st.button("🛒 Mode magasin", use_container_width=True):
            changer_page("coursevisualiser")

        col3, col4 = st.columns(2)
        with col3:
            if st.button("📊 Statistiques", use_container_width=True):
                changer_page("stats")
        with col4:
            if st.button("🛠️ Maintenance", use_container_width=True):
                changer_page("maintenance")

    # --- ROUTAGE (Contenu de la page) ---
    else:
        # Utilisation d'un dictionnaire pour simplifier et accélérer le routage
        pages = {
            "importer": importer.afficher,
            "ajouter": saisir.afficher,
            "recettes": recettes.afficher,
            "coursesaisir": coursesaisir.afficher,
            "coursevisualiser": coursevisualiser.afficher,
            "stats": stats.afficher,
            "planning": planning.afficher,
            "maintenance": maintenance.afficher
        }
        
        # Appel de la fonction afficher() correspondante
        if st.session_state.page in pages:
            pages[st.session_state.page]()

        # Bouton retour (masqué sur le planning)
        st.write("") 
        if st.session_state.page != "planning":
            if st.button("⬅️ Retour à l'accueil", use_container_width=True):
                changer_page('accueil')
