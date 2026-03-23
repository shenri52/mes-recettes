import streamlit as st
import streamlit.components.v1 as components
import importer, saisir, recettes, stats, maintenance, planning, coursesaisir, coursevisualiser

# --- FONCTION DE PROTECTION ---
def verifier_mot_de_passe():
    """Vérifie l'identité via le mot de passe ou autorise l'accès public restreint."""
    if "authentifie" not in st.session_state:
        st.session_state["authentifie"] = False
    if "mode_public" not in st.session_state:
        st.session_state["mode_public"] = False

    if not st.session_state["authentifie"] and not st.session_state["mode_public"]:
        st.set_page_config(page_title="Mesrecettes", page_icon="🍳", layout="centered")
        st.markdown("<h2 style='text-align: center;'>🍳 Mes recettes</h2>", unsafe_allow_html=True)
        st.divider()
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

        st.markdown("<h3 style='text-align: center;'>👀 Accès public</h3>", unsafe_allow_html=True)
      
        # Bouton d'accès direct pour la consultation simple
        if st.button("📖 Consulter les recettes", use_container_width=True):
            st.session_state["mode_public"] = True
            st.session_state.page = "recettes"
            st.session_state.titre_page = "📖 Consulter les recettes"
            st.rerun()
            
        return False
    return True

def aller_accueil():
    # 1. Liste des clés critiques à NE PAS supprimer (pour rester connecté)
    cles_a_conserver = ['authentifie', 'mode_public', 'mdp_temp']
    
    # 2. On supprime tout le reste
    for cle in list(st.session_state.keys()):
        if cle not in cles_a_conserver:
            del st.session_state[cle]
    
    # 3. On redirige vers l'accueil
    st.session_state.page = 'accueil'

# --- EXÉCUTION DE L'APPLICATION ---
if verifier_mot_de_passe():
    if 'page' not in st.session_state:
        st.session_state.page = 'accueil'
    if 'titre_page' not in st.session_state:
        st.session_state.titre_page = ""

    def changer_page(nom, titre):
        """Change la page active dans le session_state, sauvegarde le titre et rafraîchit."""
        st.session_state.page = nom
        st.session_state.titre_page = titre
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
        # Navigation via boutons principaux
        if st.button("📚 Mes recettes", use_container_width=True):
            changer_page("recettes", "📚 Mes recettes")
        
        # Affichage des options réservées à l'administrateur
        if st.session_state["authentifie"]:
            # Simplification L1, L2... via une liste de lignes de boutons
            lignes_boutons = [
                [("📥 Importer une recette", "importer"), ("✍️ Créer une recette", "ajouter")],
                [("📅 Mon planning", "planning")],
                [("📝 Liste des courses", "coursesaisir")],
                [("🛒 Mode magasin", "coursevisualiser")],
                [("📊 Statistiques", "stats"), ("🛠️ Maintenance", "maintenance")]
            ]

            for ligne in lignes_boutons:
                colonnes = st.columns(len(ligne))
                for index, (titre_bouton, nom_page) in enumerate(ligne):
                    with colonnes[index]:
                        if st.button(titre_bouton, use_container_width=True):
                            changer_page(nom_page, titre_bouton)
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

        if st.session_state.page in pages_disponibles:
            # PROPULSION DU TITRE
            if "titre_page" in st.session_state and st.session_state.titre_page != "":
                st.header(st.session_state.titre_page)

        # Appel de la fonction afficher() si autorisée
        if st.session_state.page in pages_disponibles:
            pages_disponibles[st.session_state.page]()
        else:
            st.error("🚫 Accès restreint. Veuillez vous connecter pour voir cette page.")
            if st.button("Retour à l'accueil", use_container_width=True):
                aller_accueil()
        # Bouton retour (masqué sur le planning)
        st.divider()

        if st.session_state.page != "planning":
            st.button("⬅️ Retour accueil", use_container_width=True, on_click=aller_accueil)
