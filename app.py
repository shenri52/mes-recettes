import streamlit as st
import streamlit.components.v1 as components
import ajouter, importer, saisir, recettes, maintenance, planning

# --- CONFIGURATION INITIALE ---
# Doit être la PREMIÈRE commande Streamlit du script
st.set_page_config(page_title="Mesrecettes", page_icon="🍳", layout="centered")

# --- FONCTION DE PROTECTION ---
def verifier_mot_de_passe():
    """Vérifie l'identité via le mot de passe ou autorise l'accès public restreint."""
    if "authentifie" not in st.session_state:
        st.session_state["authentifie"] = False
    if "mode_public" not in st.session_state:
        st.session_state["mode_public"] = False

    if not st.session_state["authentifie"] and not st.session_state["mode_public"]:
        st.markdown("<h3 style='text-align: center;'>🔒 Accès réservé</h3>", unsafe_allow_html=True)
        
        def valider():
            # Vérification sécurisée du mot de passe via st.secrets
            if st.session_state["mdp_temp"] == st.secrets["APP_PASSWORD"]:
                st.session_state["authentifie"] = True
                st.session_state["mode_public"] = False
            else:
                st.error("Mot de passe incorrect ❌")

        st.text_input(
            "Veuillez saisir le mot de passe :", 
            type="password", 
            key="mdp_temp", 
            on_change=valider
        )
        
        col_auth, col_pub = st.columns(2)
        with col_auth:
            if st.button("Se connecter", use_container_width=True):
                valider()
                if st.session_state["authentifie"]:
                    st.rerun()
        
        with col_pub:
            # Accès direct pour la consultation simple
            if st.button("📖 Mode Public", use_container_width=True):
                st.session_state["mode_public"] = True
                st.session_state.page = "recettes"
                st.rerun()
            
        return False
    return True

def aller_accueil():
    """Réinitialise la navigation vers l'accueil."""
    st.session_state.page = 'accueil'
    # On ne réinitialise pas forcément le mode_public ici pour éviter de 
    # redemander le MDP à chaque retour menu si on est en consultation.
    # Si tu veux forcer le verrouillage au retour accueil, décommente la ligne dessous :
    # st.session_state["mode_public"] = False

# --- EXÉCUTION DE L'APPLICATION ---
if verifier_mot_de_passe():
    if 'page' not in st.session_state:
        st.session_state.page = 'accueil'

    def changer_page(nom):
        """Change la page active dans le session_state."""
        st.session_state.page = nom
        st.rerun()

    # --- BLOC ANTI-VEILLE ---
    PAGES_CUISINE = ["planning", "recettes", "ajouter", "saisir"]
    if st.session_state.page in PAGES_CUISINE:
        mode_cuisine = st.toggle("🚫 Garder l'écran allumé", value=False)
        if mode_cuisine:
            # Injection d'un élément vidéo invisible pour empêcher la mise en veille
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
        st.title("👨‍🍳 Menu Principal")
        
        if st.button("📚 Consulter les recettes", use_container_width=True):
            changer_page("recettes")
        
        st.divider()

        # Affichage des options réservées à l'administrateur
        if st.session_state["authentifie"]:
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📥 Importer (Web)", use_container_width=True):
                    changer_page("importer")
            with col2:
                if st.button("✍️ Créer (Manuel)", use_container_width=True):
                    changer_page("saisir")

            if st.button("📅 Mon planning repas", use_container_width=True):
                changer_page("planning")
            
            if st.button("🛠️ Maintenance système", use_container_width=True):
                changer_page("maintenance")
                
            if st.button("🚪 Se déconnecter", use_container_width=True):
                st.session_state["authentifie"] = False
                st.rerun()
        else:
            st.info("💡 Mode consultation active. Connectez-vous pour modifier ou planifier.")
            if st.button("🔒 Se connecter (Admin)", use_container_width=True):
                st.session_state["mode_public"] = False
                st.rerun()

    # --- ROUTAGE DES PAGES ---
    else:
        # Pages accessibles à tous
        pages_disponibles = {
            "recettes": recettes.afficher
        }
        
        # Pages réservées à l'admin
        if st.session_state["authentifie"]:
            pages_disponibles.update({
                "importer": importer.afficher,
                "ajouter": ajouter.afficher,
                "saisir": saisir.afficher,
                "planning": planning.afficher,
                "maintenance": maintenance.afficher
            })

        # Appel de la fonction de la page
        if st.session_state.page in pages_disponibles:
            pages_disponibles[st.session_state.page]()
        else:
            st.error("🚫 Accès restreint ou page inexistante.")
            if st.button("Retour à l'accueil", use_container_width=True):
                aller_accueil()
                st.rerun()

        # --- PIED DE PAGE / RETOUR ---
        st.divider()
        if st.session_state.page != "planning":
            if st.button("⬅️ Retour au menu principal", use_container_width=True):
                aller_accueil()
                st.rerun()
