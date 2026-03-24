import streamlit as st
import ajouter, recettes, maintenance, planning

# --- CONFIGURATION (Doit être la toute première commande) ---
st.set_page_config(page_title="Mes recettes", page_icon="🍳", layout="centered")

# --- INITIALISATION DU SESSION STATE ---
def initialiser_session():
    """Centralise l'initialisation pour éviter les erreurs de clés manquantes."""
    defaults = {
        "authentifie": False,
        "mode_public": False,
        "page": "accueil"
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

# --- FONCTIONS DE NAVIGATION ---
def aller_accueil():
    st.session_state.page = "accueil"

def changer_page(nom):
    """Change de page et nettoie les données temporaires pour éviter les conflits."""
    # Nettoyage des clés de modification/ajout des autres modules
    for key in list(st.session_state.keys()):
        if any(key.startswith(p) for p in ["edit_", "init_done_", "ings_list_"]):
            del st.session_state[key]
    st.session_state.page = nom

# --- FONCTION DE PROTECTION ---
def verifier_mot_de_passe():
    """Vérifie l'identité via le mot de passe ou autorise l'accès public restreint."""
    if not st.session_state["authentifie"] and not st.session_state["mode_public"]:
        st.markdown("<h3 style='text-align: center;'>🔑 Accès réservé</h3>", unsafe_allow_html=True)
        
        def valider():
            if st.session_state.get("mdp_temp") == st.secrets["APP_PASSWORD"]:
                st.session_state["authentifie"] = True
            else:
                st.error("Mot de passe incorrect ❌")

        st.text_input(
            "Veuillez saisir le mot de passe :", 
            type="password", 
            key="mdp_temp", 
            on_change=valider
        )
        
        col1, col2 = st.columns(2)
        if col1.button("Se connecter", use_container_width=True):
            valider()
            if st.session_state["authentifie"]: st.rerun()
               
        if col2.button("Accès Public (Lecture seule)", use_container_width=True):
            st.session_state["mode_public"] = True
            st.rerun()
        return False
    return True

# --- LOGIQUE PRINCIPALE ---
initialiser_session()

if verifier_mot_de_passe():
    # --- BARRE LATÉRALE (Interface d'origine) ---
    with st.sidebar:
        st.title("🍳 Menu")
        
        if st.button("📚 Mes recettes", use_container_width=True):
            changer_page("recettes")
            
        if st.session_state["authentifie"]:
            if st.button("📅 Mon planning", use_container_width=True):
                changer_page("planning")
            if st.button("📥 Ajouter une recette", use_container_width=True):
                changer_page("ajouter")
            if st.button("🛠️ Maintenance", use_container_width=True):
                changer_page("maintenance")
        
        st.divider()
        if st.button("🚪 Déconnexion", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    # --- ROUTAGE (Contenu de la page) ---
    # Définition statique des pages pour plus de rapidité
    pages_publiques = {"recettes": recettes.afficher}
    pages_admin = {
        "ajouter": ajouter.afficher,
        "planning": planning.afficher,
        "maintenance": maintenance.afficher
    }
    
    # Fusion selon les droits
    pages_disponibles = {**pages_publiques, **pages_admin} if st.session_state["authentifie"] else pages_publiques

    if st.session_state.page == "accueil":
        st.title("🍴 Bienvenue dans ma cuisine !")
        st.info("Utilisez le menu à gauche pour naviguer.")
    elif st.session_state.page in pages_disponibles:
        pages_disponibles[st.session_state.page]()
    else:
        st.error("🚫 Accès restreint ou page inconnue.")
        if st.button("Retour à l'accueil", use_container_width=True):
            aller_accueil()
            st.rerun()

    # Bouton retour universel
    if st.session_state.page not in ["accueil", "planning"]:
        st.divider()
        if st.button("⬅️ Retour accueil", use_container_width=True):
            aller_accueil()
            st.rerun()
