import streamlit as st
import streamlit.components.v1 as components
import ajouter, recettes, maintenance, planning

# --- FONCTION DE PROTECTION ---
def verifier_mot_de_passe():
    """Vérifie l'identité via le mot de passe ou autorise l'accès public restreint."""
    if "authentifie" not in st.session_state:
        st.session_state["authentifie"] = False
    if "mode_public" not in st.session_state:
        st.session_state["mode_public"] = False

    if not st.session_state["authentifie"] and not st.session_state["mode_public"]:
        st.set_page_config(page_title="Mesrecettes", page_icon="🍳", layout="centered")
        st.markdown("<h3 style='text-align: center;'>🔑 Accès réservé</h3>", unsafe_allow_html=True)
        
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
    # On remet la page sur accueil
    st.session_state.page = 'accueil'
    # On désactive le mode public pour revenir à l'écran de verrouillage 🔒
    st.session_state["mode_public"] = False

# --- EXÉCUTION DE L'APPLICATION ---
if verifier_mot_de_passe():
    if 'page' not in st.session_state:
        st.session_state.page = 'accueil'

    def changer_page(nom):
        """Change la page active dans le session_state et rafraîchit l'affichage."""
        st.session_state.page = nom
        st.rerun()
        
    # --- MENU D'ACCUEIL ---
    if st.session_state.page == 'accueil':
        if st.button("📚 Mes recettes", use_container_width=True):
            changer_page("recettes")
        if st.button("📥 Ajouter une recette", use_container_width=True):
            changer_page("ajouter")
        if st.button("📅 Mon planning", use_container_width=True):
            changer_page("planning")
        if st.button("🛠️ Maintenance", use_container_width=True):
            changer_page("maintenance")
    else:
        st.info("💡 Mode consultation active. Connectez-vous pour accéder au planning et à la création.")

    # --- ROUTAGE (Contenu de la page) ---
    else:
        # Dictionnaire des pages en mode public
        pages_publiques = {
            "recettes": recettes.afficher
        }
        
        # Dictionnaire des pages réservées
        pages_admin = {
            "ajouter": ajouter.afficher,
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

        if st.session_state.page != "planning":
            st.divider()
            st.button("⬅️ Retour accueil", use_container_width=True, on_click=aller_accueil)
