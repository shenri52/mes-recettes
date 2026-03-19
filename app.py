import streamlit as st
import streamlit.components.v1 as components
import importer, saisir, recettes, stats, maintenance, planning, coursesaisir, coursevisualiser

# --- FONCTION DE PROTECTION ---
def verifier_mot_de_passe():
    for cle in ["authentifie", "mode_public"]:
        if cle not in st.session_state:
            st.session_state[cle] = False

    if not st.session_state["authentifie"] and not st.session_state["mode_public"]:
        st.set_page_config(page_title="Mesrecettes", page_icon="🍳", layout="centered")
        st.markdown("<h2 style='text-align: center;'>🍳 Mes recettes</h2>", unsafe_allow_html=True)
        st.divider()
        st.markdown("<h3 style='text-align: center;'>🔒 Accès réservé</h3>", unsafe_allow_html=True)
        
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
    # On désactive le mode public pour revenir à l'écran de verrouillage 
    st.session_state["mode_public"] = False

# --- EXÉCUTION DE L'APPLICATION ---
if verifier_mot_de_passe():
    if 'page' not in st.session_state:
        st.session_state.page = 'accueil'

    def changer_page(nom):
        st.session_state.page = nom
        st.rerun()

    # --- BLOC ANTI-VEILLE ---
    PAGES_CUISINE = ["planning", "recettes", "ajouter", "coursesaisir", "coursevisualiser"]

    if st.session_state.page in PAGES_CUISINE and st.checkbox("🚫 Garder l'écran allumé", value=False):
        video_url = "https://raw.githubusercontent.com/anars/blank-audio/master/250-milliseconds-of-silence.mp3"
        components.html(f'<video autoplay loop muted playsinline style="display:none;"><source src="{video_url}" type="video/mp4"></video>', height=0)

    # --- MENU D'ACCUEIL ---
    if st.session_state.page == 'accueil':
        if st.session_state["authentifie"]:
            # Liste des boutons (Texte, Cible)
            actions = [
                ("📥 Importer une recette", "importer"), ("✍️ Créer une recette", "ajouter"),
                ("📅 Mon planning", "planning"), ("📝 Liste des courses", "coursesaisir"),
                ("🛒 Mode magasin", "coursevisualiser"), ("📊 Statistiques", "stats"),
                ("🛠️ Maintenance", "maintenance")
            ]
        
        # Affichage auto sur 2 colonnes
        cols = st.columns(2)
        for i, (label, page) in enumerate(actions):
            if cols[i % 2].button(label, use_container_width=True):
                changer_page(page)
    else:
        st.info("💡 Mode consultation actif. Connectez-vous pour l'administration.")

    # --- ROUTAGE 
else:
        # Pages accessibles à tous
        pages = {"recettes": recettes.afficher}
        
        # Ajout des pages admin si connecté
        if st.session_state["authentifie"]:
            pages.update({
                "importer": importer.afficher, "ajouter": saisir.afficher,
                "coursesaisir": coursesaisir.afficher, "coursevisualiser": coursevisualiser.afficher,
                "stats": stats.afficher, "planning": planning.afficher, "maintenance": maintenance.afficher
            })

        # Exécution ou message d'erreur
        if st.session_state.page in pages:
            pages[st.session_state.page]()
        else:
            st.error("🚫 Accès restreint.")
            st.button("Retour", on_click=aller_accueil)

        # Bouton retour (masqué sur le planning)
        st.divider()

        if st.session_state.page != "planning":
            st.button("⬅️ Retour accueil", use_container_width=True, on_click=aller_accueil)
