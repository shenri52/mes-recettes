import streamlit as st
import streamlit.components.v1 as components
import utils
import importer, saisir, recettes, stats, maintenance, planning, coursesaisir, coursevisualiser

# --- FONCTION DE PROTECTION ---
def verifier_mot_de_passe():
    """Vérifie l'identité via le mot de passe ou autorise l'accès public restreint."""
    utils.initialiser_session()

    if not st.session_state["authentifie"] and not st.session_state["mode_public"]:
        st.set_page_config(page_title="Mesrecettes", page_icon="🍳", layout="centered")
        st.markdown("<h2 style='text-align: center; color: #000000;'>🥘 Mon catalogue de recettes</h2>", unsafe_allow_html=True)
        st.divider()
        st.markdown("<h3 style='text-align: center; color: #000000;'>🔑 Accès réservé</h3>", unsafe_allow_html=True)
        
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
        
        st.markdown("<h3 style='text-align: center; color: #000000;'>📖 Accès public</h3>", unsafe_allow_html=True)
        
        # Bouton d'accès direct pour la consultation simple
        if st.button("Consulter les recettes", use_container_width=True):
            st.session_state["mode_public"] = True
            st.session_state.page = "recettes"
            st.rerun()
            
        return False
    return True

# --- EXÉCUTION DE L'APPLICATION ---
if verifier_mot_de_passe():
    if 'page' not in st.session_state:
        st.session_state.page = 'accueil'

    def changer_page(nom):
        utils.naviguer_vers(nom)

    # --- BLOC ANTI-VEILLE ---
    # S'affiche sur toutes les pages sauf l'accueil et la maintenance
    if st.session_state.page not in ['accueil', 'maintenance']:
        mode_cuisine = st.checkbox("🚫 Garder l'application connectée", value=False)
        if mode_cuisine:
            components.html("""<div style="display:none;"><video autoplay loop muted playsinline style="width:1px; height:1px;"><source src="https://raw.githubusercontent.com/anars/blank-audio/master/250-milliseconds-of-silence.mp3" type="video/mp4"></video></div>""", height=0)
            
    # --- MENU D'ACCUEIL ---
    if st.session_state.page == 'accueil':
        if st.button("📚 Mes recettes", use_container_width=True):
            changer_page("recettes")
        
        if st.session_state["authentifie"]:
            # On définit les boutons par ligne (Listes de tuples : "Label", "Page")
            L1 = [("📥 Importer une recette", "importer"), ("✍️ Créer une recette", "ajouter")]
            L2 = [("📥 Importer des recettes ODT", "import_odt"), ("✍️ Importer des recettes PDF", "import_pdf")]
            L3 = [("📅 Mon planning", "planning"), ("📝 Liste des courses", "coursesaisir"), ("🛒 Mode magasin", "coursevisualiser")]
            L4 = [("📊 Statistiques", "stats"), ("🛠️ Maintenance", "maintenance")]

            # Ligne 1 : 2 colonnes
            cols1 = st.columns(2)
            for i, (label, page) in enumerate(L1):
                if cols1[i].button(label, use_container_width=True): changer_page(page)
                    
            # Ligne 2 : 2 colonnes
            cols1 = st.columns(2)
            for i, (label, page) in enumerate(L2):
                if cols1[i].button(label, use_container_width=True): changer_page(page)

            # Ligne 3 : Boutons un par un (Plein écran)
            for label, page in L3:
                if st.button(label, use_container_width=True): changer_page(page)

            # Ligne 4 : 2 colonnes
            cols3 = st.columns(2)
            for i, (label, page) in enumerate(L4):
                if cols3[i].button(label, use_container_width=True): changer_page(page)
        else:
            st.info("💡 Mode consultation active. Connectez-vous pour accéder au planning et à la création.")

    # --- ROUTAGE (Contenu de la page) ---
    else:
        # 1. Centralisation de toutes les pages
        toutes_pages = {
            "recettes": recettes.afficher, "importer": importer.afficher,
            "ajouter": saisir.afficher, "coursesaisir": coursesaisir.afficher,
            "coursevisualiser": coursevisualiser.afficher, "stats": stats.afficher,
            "planning": planning.afficher, "maintenance": maintenance.afficher
        }
        
        # 2. Vérification des droits (Seul 'recettes' est public)
        p_actuelle = st.session_state.page
        autorise = st.session_state["authentifie"] or p_actuelle == "recettes"

        if autorise and p_actuelle in toutes_pages:
            toutes_pages[p_actuelle]()
        else:
            st.error("🚫 Accès restreint. Veuillez vous connecter.")
            if st.button("Retour à l'accueil", use_container_width=True):
                utils.deconnexion()
                st.rerun()

        # 3. Bouton retour automatique (Sauf sur planning)
        if p_actuelle != "planning":
            st.divider()
            st.button("⬅️ Retour accueil", use_container_width=True, on_click=utils.deconnexion)
