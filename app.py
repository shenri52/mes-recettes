import streamlit as st
import random
import ajouter, recettes, maintenance, planning, restes
from utils import charger_index, obtenir_taille_depot, ouvrir_fiche

# --- CONFIGURATION DES MENUS ---
# Clé = Nom exact du bouton (qui devient aussi le nom de la page)
# Valeur = {"module": fichier.py à appeler, "public": True/False si accessible sans mot de passe}
MENUS = {
    "📚 Mes recettes": {"module": recettes, "public": True},
    "💡 Que faire avec mes restes ?": {"module": restes, "public": True},
    "📅 Mon planning": {"module": planning, "public": False},
    "📥 Ajouter une recette": {"module": ajouter, "public": False},
    "🛠️ Maintenance": {"module": maintenance, "public": False}
}

# --- FONCTION DE PROTECTION ---
def verifier_mot_de_passe():
    """Vérifie l'identité via le mot de passe ou autorise l'accès public restreint."""
    if "authentifie" not in st.session_state: st.session_state["authentifie"] = False
    if "mode_public" not in st.session_state: st.session_state["mode_public"] = False

    if not st.session_state["authentifie"] and not st.session_state["mode_public"]:
        st.set_page_config(page_title="Mesrecettes", page_icon="🍳", layout="centered")
        st.markdown("<h3 style='text-align: center;'>🔑 Accès réservé</h3>", unsafe_allow_html=True)
        
        def valider():
            if st.session_state["mdp_temp"] == st.secrets["APP_PASSWORD"]:
                st.session_state["authentifie"] = True
            else:
                st.error("Mot de passe incorrect ❌")

        st.text_input("Veuillez saisir le mot de passe :", type="password", key="mdp_temp", on_change=valider)
        
        if st.button("Se connecter", use_container_width=True):
            valider()
            if st.session_state["authentifie"]: st.rerun()

        # --- ACCÈS DIRECTE A UNE RECETTE PARTAGEE ---
        if "recette" in st.query_params:
            # On active le mode public immédiatement
            st.session_state["mode_public"] = True
            # On définit la page cible (doit être identique à la clé dans MENUS)
            st.session_state["page"] = "📚 Mes recettes"
            # On pré-remplit la sélection pour le module recettes
            st.session_state["select_recette"] = st.query_params["recette"].upper()
            st.rerun()
    
        # --- BOUTON D'ACCÈS PUBLIC ---
        st.markdown("<h3 style='text-align: center;'>👁️ Accès public</h3>", unsafe_allow_html=True)
        
        col_recettes, col_restes = st.columns(2)
        with col_recettes:
            if st.button("📖 Consulter les recettes", use_container_width=True):
                st.session_state["mode_public"] = True
                st.session_state.page = "📚 Mes recettes" # Le nom exact de la clé du menu
                st.rerun()
                
        with col_restes:
            if st.button("💡 Que faire avec mes restes ?", use_container_width=True):
                st.session_state["mode_public"] = True
                st.session_state.page = "💡 Que faire avec mes restes ?" # Redirige vers le nouveau module
                st.rerun()
        
        st.markdown("<h3 style='text-align: center;'>🎲 Recette aléatoire</h3>", unsafe_allow_html=True)
        
        index = charger_index()
        
        if index:
            # Nettoyage et récupération des catégories
            toutes_categories = sorted(list(set(r.get('categorie', 'Non classé') for r in index)))
            
            # Définition des 3 catégories stars
            stars_cibles = {"Entrées": "🥗 Entrées", "Plats": "🥘 Plats", "Desserts": "🍰 Desserts"}
            stars_presentes = [c for c in toutes_categories if c in stars_cibles.keys()]
            autres_categories = [c for c in toutes_categories if c not in stars_cibles.keys()]

            # Création de la grille : 3 colonnes pour les stars + 1 pour le reste
            cols = st.columns(4)
            choix_final = None

            # Boutons pour les catégories Stars
            # Note : On affiche "Entrées" mais on cherche la clé exacte dans ton index
            if cols[0].button("🥗 Entrées", use_container_width=True):
                choix_final = "Entrées"
            if cols[1].button("🥘 Plats", use_container_width=True):
                choix_final = "Plats"
            if cols[2].button("🍰 Desserts", use_container_width=True):
                choix_final = "Desserts"

            # Le bouton "Autres" sous forme de popover pour ne pas encombrer
            with cols[3]:
                with st.popover("➕ Autres"):
                    choix_popover = st.selectbox("Toutes les catégories", ["---"] + autres_categories, label_visibility="collapsed")
                    if choix_popover != "---":
                        choix_final = choix_popover

            # Bouton d'action si une catégorie est sélectionnée
            if choix_final:
                st.write("") # Petit espace
                if st.button(f"✨ Tirer un(e) {choix_final} au sort", type="primary", use_container_width=True):
                    pool = [r for r in index if r.get('categorie') == choix_final]
                    if pool:
                        choix = random.choice(pool)
                        st.session_state.alerte_recette = choix['nom']
                        st.rerun()
                    else:
                        st.error(f"Aucune recette dans la catégorie {choix_final} ! 🫙")

        # L'affichage de la fiche (toujours hors du bouton pour le dialogue)
        if "alerte_recette" in st.session_state:
            nom = st.session_state.alerte_recette
            del st.session_state.alerte_recette
            ouvrir_fiche(nom)
            
        # --- AFFICHAGE DU COMPTEUR DE RECETTES ---
        if "index_recettes" not in st.session_state:
            charger_index()
            
        nb_recettes = len(st.session_state.get("index_recettes", []))
        if nb_recettes > 0:
            taille_ko = obtenir_taille_depot()
            if taille_ko > 0:
                taille_mo = taille_ko / 1024

            st.info(f"""📊 **Mon livre de recettes** : {nb_recettes} recttes - {taille_mo:.2f} Mo""")
                
        return False
    return True

def aller_accueil():
    st.query_params.clear()
    st.session_state.page = 'accueil'
    st.session_state["mode_public"] = False
    st.session_state["select_recette"] = "---"
    if "choix_recette_gui" in st.session_state:
        del st.session_state["choix_recette_gui"]
    if "mes_restes" in st.session_state:
        del st.session_state["mes_restes"]

# --- EXÉCUTION DE L'APPLICATION ---
if verifier_mot_de_passe():
    if 'page' not in st.session_state: st.session_state.page = 'accueil'

    # --- MENU D'ACCUEIL ---
    if st.session_state.page == 'accueil':
        if not st.session_state["authentifie"]:
            st.info("💡 Mode consultation active. Connectez-vous pour accéder au planning et à la création.")
        
        # Génération automatique des boutons depuis le dictionnaire MENUS
        for nom_bouton, config in MENUS.items():
            # On affiche le bouton seulement s'il est public ou si l'utilisateur est connecté
            if config["public"] or st.session_state["authentifie"]:
                if st.button(nom_bouton, use_container_width=True):
                    st.session_state.page = nom_bouton
                    st.rerun()

        # 2. Ajout du bouton de déconnexion (uniquement si connecté)
        if st.session_state["authentifie"]:
            st.divider() # Petite séparation visuelle
            if st.button("🚪 Se déconnecter", use_container_width=True, type="primary"):
                # On vide TOUTE la session pour revenir à l'écran de verrouillage
                st.session_state.clear()
                st.rerun()

    # --- ROUTAGE DYNAMIQUE (Contenu de la page) ---
    else:
        page_actuelle = st.session_state.page
        
        # Si la page existe dans notre menu
        if page_actuelle in MENUS:
            config_page = MENUS[page_actuelle]
            
            # Sécurité finale (au cas où on force l'URL ou un état)
            if not st.session_state["authentifie"] and not config_page["public"]:
                st.error("🚫 Accès restreint. Veuillez vous connecter pour voir cette page.")
            else:
                # 👉 AFFICHE AUTOMATIQUEMENT LE NOM DU BOUTON COMME TITRE DE PAGE
                st.title(page_actuelle)
                # Exécute la fonction afficher() du bon module
                config_page["module"].afficher()
        else:
            st.error("🚫 Page introuvable.")
            if st.button("Retour à l'accueil", use_container_width=True):
                aller_accueil()     

        # Affichage conditionnel du bouton retour (comme dans ton code original)
        if st.session_state.page != "📅 Mon planning":
            st.divider()
            st.button("⬅️ Retour accueil", use_container_width=True, on_click=aller_accueil)
