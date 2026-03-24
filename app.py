import streamlit as st
import ajouter, recettes, maintenance, planning

# --- CONFIGURATION ---
st.set_page_config(page_title="Mes Recettes 🍳", page_icon="🍳", layout="centered")

def initialiser_session():
    if "authentifie" not in st.session_state: st.session_state.authentifie = False
    if "mode_public" not in st.session_state: st.session_state.mode_public = False
    if "page" not in st.session_state: st.session_state.page = "accueil"

def changer_page(nom_page):
    """Nettoie l'état et change de page."""
    for key in list(st.session_state.keys()):
        if any(key.startswith(p) for p in ["edit_", "init_done_", "ings_list_"]):
            del st.session_state[key]
    st.session_state.page = nom_page
    st.rerun()

# --- ECRAN DE CONNEXION ---
def ecran_connexion():
    st.markdown("<h3 style='text-align: center;'>🔑 Accès réservé</h3>", unsafe_allow_html=True)
    mdp = st.text_input("Mot de passe :", type="password")
    c1, c2 = st.columns(2)
    if c1.button("Se connecter", use_container_width=True):
        if mdp == st.secrets["APP_PASSWORD"]:
            st.session_state.authentifie = True
            st.rerun()
        else:
            st.error("Mot de passe incorrect ❌")
    if c2.button("Accès Public (Lecture seule)", use_container_width=True):
        st.session_state.mode_public = True
        st.rerun()

# --- MAIN ---
def main():
    initialiser_session()

    if not st.session_state.authentifie and not st.session_state.mode_public:
        ecran_connexion()
        return

    # 1. Définition du Menu horizontal
    menu = {"📚 Recettes": "recettes"}
    if st.session_state.authentifie:
        menu.update({
            "📅 Planning": "planning",
            "📥 Ajouter": "ajouter",
            "🛠️ Maintenance": "maintenance"
        })

    # 2. Affichage du Menu (Colonnes sur la page principale)
    st.title("🍳 Ma Cuisine")
    
    # Création d'une ligne de boutons pour la navigation
    cols = st.columns(len(menu))
    for i, (label, page_id) in enumerate(menu.items()):
        # Le bouton est coloré (primary) si c'est la page active
        if cols[i].button(label, use_container_width=True, 
                          type="primary" if st.session_state.page == page_id else "secondary"):
            changer_page(page_id)
    
    st.divider()

    # 3. Affichage du contenu
    if st.session_state.page == "accueil":
        st.info("Bienvenue ! Choisissez une option ci-dessus pour commencer. 👨‍🍳")
    else:
        pages = {
            "recettes": recettes.afficher,
            "ajouter": ajouter.afficher,
            "planning": planning.afficher,
            "maintenance": maintenance.afficher
        }
        
        if st.session_state.page in pages:
            pages[st.session_state.page]()

    # 4. Footer (Optionnel : Déconnexion / Retour)
    st.markdown("<div style='margin-top: 50px;'></div>", unsafe_allow_html=True)
    f1, f2 = st.columns([4, 1])
    if st.session_state.page != "accueil":
        if f1.button("🏠 Retour Accueil", size="small"):
            changer_page("accueil")
            
    if f2.button("🚪 Quitter", size="small"):
        st.session_state.clear()
        st.rerun()

if __name__ == "__main__":
    main()
