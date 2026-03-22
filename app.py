import streamlit as st
import streamlit.components.v1 as components
import utils
import importer, saisir, recettes, import_odt, import_pdf, stats, maintenance, planning, coursesaisir, coursevisualiser

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
    PAGES = {
            "recettes": "📚 Mes recettes",
            "importer": "📥 Importer une recette",
            "ajouter": "✍️ Créer une recette",
            "import_odt": "🖋️ Charger une recette (ODT)",
            "import_pdf": "📕 Charger une recette (PDF)",
            "planning": "📅 Mon planning",
            "coursesaisir": "📝 Liste des courses",
            "coursevisualiser": "🛒 Mode magasin",
            "stats": "📊 Statistiques",
            "maintenance": "🛠️ Maintenance"
        }
    
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
        if st.button(PAGES["recettes"], use_container_width=True):
            changer_page("recettes")

        if st.session_state["authentifie"]:
            L1 = ["importer", "ajouter"]
            L2 = ["import_odt", "import_pdf"]
            L3 = ["planning", "coursesaisir", "coursevisualiser"]
            L4 = ["stats", "maintenance"]
            
            # Ligne 1 : 2 colonnes
            cols1 = st.columns(2)
            for i, cle in enumerate(L1):
                if cols1[i].button(PAGES[cle], use_container_width=True): 
                    changer_page(cle)
                    
            # Ligne 2 : 2 colonnes
            cols2 = st.columns(2) # On utilise cols2 pour éviter les conflits
            for i, cle in enumerate(L2):
                if cols2[i].button(PAGES[cle], use_container_width=True): 
                    changer_page(cle)

            # Ligne 3 : Boutons un par un (Plein écran)
            for cle in L3:
                if st.button(PAGES[cle], use_container_width=True): 
                    changer_page(cle)

            # Ligne 4 : 2 colonnes
            cols4 = st.columns(2)
            for i, cle in enumerate(L4):
                if cols4[i].button(PAGES[cle], use_container_width=True): 
                    changer_page(cle)
        else:
            st.info("💡 Mode consultation active. Connectez-vous pour accéder au planning et à la création.")

    # --- ROUTAGE (Contenu de la page) ---
    else:
        p_actuelle = st.session_state.page
        
        # 1. On définit les fonctions d'abord
        toutes_pages = {
            "recettes": recettes.afficher, 
            "importer": importer.afficher,
            "import_odt": import_odt.afficher, 
            "import_pdf": lambda: st.info("📕 Le module PDF est en cours de développement !"),
            "ajouter": saisir.afficher, 
            "coursesaisir": coursesaisir.afficher,
            "coursevisualiser": coursevisualiser.afficher, 
            "stats": stats.afficher,
            "planning": planning.afficher, 
            "maintenance": maintenance.afficher
        }

        # 2. Vérification des droits
        autorise = st.session_state["authentifie"] or p_actuelle == "recettes"

        if autorise and p_actuelle in toutes_pages:
            # --- AFFICHAGE DU TITRE AUTO ---
            st.header(PAGES.get(p_actuelle, "Page inconnue"))
            st.divider()
            
            # --- APPEL DE LA PAGE ---
            toutes_pages[p_actuelle]()
        else:
            st.error("🚫 Accès restreint. Veuillez vous connecter.")
            if st.button("Retour à l'accueil", use_container_width=True):
                utils.deconnexion()
                st.rerun()

        # 3. Bouton retour (Sauf sur planning)
        if p_actuelle != "planning":
            st.divider()
            st.button("⬅️ Retour accueil", use_container_width=True, on_click=utils.deconnexion)
