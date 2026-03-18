import streamlit as st
import streamlit.components.v1 as components
# Importation des modules (chaque fichier contient une fonction afficher())
import importer, saisir, recettes, stats, maintenance, planning, coursesaisir, coursevisualiser

# Configuration de l'onglet du navigateur
st.set_page_config(page_title="Mesrecettes", page_icon="🍳", layout="centered")

# --- FONCTION DE PROTECTION ---
def verifier_mot_de_passe():
    """Vérifie l'identité via le mot de passe ou autorise l'accès public restreint."""
    if "authentifie" not in st.session_state:
        st.session_state["authentifie"] = False
    if "mode_public" not in st.session_state:
        st.session_state["mode_public"] = False

    if not st.session_state["authentifie"] and not st.session_state["mode_public"]:
        st.markdown("<h1 style='text-align: center;'>🔒 Accès réservé</h1>", unsafe_allow_html=True)
        
        def valider():
            if st.session_state["mdp_temp"] == st.secrets["APP_PASSWORD"]:
                st.session_state["authentifie"] = True
            else:
                st.error("Mot de passe incorrect ❌")

        st.text_input(
            "Veuillez saisir le mot de passe :", 
            type="password", 
            key="mdp_temp", 
            on_change=valider
        )
        
        if st.button("Se connecter", use_container_width=True):
            valider()
            if st.session_state["authentifie"]:
                st.rerun()
        
        st.divider()
        
        # Bouton d'accès direct pour la consultation simple
        if st.button("📖 Consulter les recettes (Public)", use_container_width=True):
            st.session_state["mode_public"] = True
            st.session_state.page = "recettes"
            st.rerun()
            
        return False
    return True

def aller_accueil():
    st.session_state.page = 'accueil'

# --- EXÉCUTION DE L'APPLICATION ---
if verifier_mot_de_passe():
    if 'page' not in st.session_state:
        st.session_state.page = 'accueil'

    def changer_page(nom):
        """Change la page active dans le session_state et rafraîchit l'affichage."""
        st.session_state.page = nom
        st.rerun()

    # --- BLOC ANTI-VEILLE ---
    PAGES_CUISINE = ["planning", "recettes", "ajouter", "coursesaisir", "coursevisualiser"]

    if st.session_state.page in PAGES_CUISINE:
        mode_cuisine = st.checkbox("🚫 Garder l'application connectée", value=False)
        if mode_cuisine:
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
        
        # Affichage des options réservées à l'administrateur
        if st.session_state["authentifie"]:
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
        else:
            st.info("💡 Mode consultation active. Connectez-vous pour accéder au planning et à la création.")

    # --- ROUTAGE (Contenu de la page) ---
    else:
        # Dictionnaire des pages autorisées en mode public
        pages_publiques = {
            "recettes": recettes.afficher
        }
        
        # Dictionnaire des pages réservées (admin)
        pages_admin = {
            "importer": importer.afficher,
            "ajouter": saisir.afficher,
            "coursesaisir": coursesaisir.afficher,
            "coursevisualiser": coursevisualiser.afficher,
            "stats": stats.afficher,
            "planning": planning.afficher,
            "maintenance": maintenance.afficher
        }
        
        # Sélection du dictionnaire selon le statut
        if st.session_state["authentifie"]:
            pages_disponibles = {**pages_publiques, **pages_admin}
        else:
            pages_disponibles = pages_publiques

        # Appel de la fonction afficher() si autorisée
        if st.session_state.page in pages_disponibles:
            pages_disponibles[st.session_state.page]()
        else:
            st.error("🚫 Accès restreint. Veuillez vous connecter pour voir cette page.")
            if st.button("Retour à l'accueil", use_container_width=True):
                aller_accueil()

        # Bouton retour (masqué sur le planning)
        st.write("") 

        if st.session_state.page != "planning":
            st.button("⬅️ Retour accueil", use_container_width=True, on_click=aller_accueil)
