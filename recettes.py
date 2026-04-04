import streamlit as st
import requests, json, base64, time, uuid
from utils import config_github, charger_index, sauvegarder_index, verifier_doublon, envoyer_vers_github, compresser_image, supprimer_fichier_github

# --- 3. LOGIQUE D'AFFICHAGE ET MODIFICATION ---
def afficher():        
    def nettoyer_modif():
        """Supprime les données temporaires d'édition quand on change de recette."""
        if "img_idx" in st.session_state:
            st.session_state.img_idx = 0
        for key in list(st.session_state.keys()):
            if any(key.startswith(p) for p in ["edit_", "init_done_", "ings_list_"]):
                del st.session_state[key]
                
    index = charger_index()

    # --- FILTRAGE DYNAMIQUE (MODIFICATION DEMANDÉE) ---
    c2, c3, c4 = st.columns([1, 1, 1])
    
    cats_existantes = sorted(list(set(r.get('categorie', 'Non classé') for r in index)))
    apps = ["Tous"] + sorted(list(set(r.get('appareil', 'Aucun') for r in index)))
    
    tous_ings_bruts = []
    for r in index: 
        if r.get('ingredients'): tous_ings_bruts.extend(r['ingredients'])
    liste_ingredients_unique = sorted(list(set(tous_ings_bruts)))

    f_cat = c2.selectbox("Catégorie", ["Tous"] + cats_existantes)
    f_app = c3.selectbox("Appareil", apps)
    f_ing = c4.selectbox("Ingrédient", ["Tous"] + liste_ingredients_unique)

    # Logique : On vérifie si l'utilisateur utilise un filtre
    filtre_actif = (f_cat != "Tous" or f_app != "Tous" or f_ing != "Tous")

    resultats = [
        r for r in index 
        if (f_cat == "Tous" or r.get('categorie') == f_cat)
        and (f_app == "Tous" or r.get('appareil') == f_app)
        and (f_ing == "Tous" or f_ing in r.get('ingredients', []))
    ]

    # AFFICHAGE DES BOUTONS : Uniquement si un filtre est actif
    if filtre_actif:
        if resultats:
            st.write(f"### 📋 {len(resultats)} recette(s) trouvée(s)")
            for r in resultats:
                nom_btn = r['nom'].upper()
                if st.button(f"📖 {nom_btn}", key=f"btn_{r['chemin']}", use_container_width=True):
                    st.session_state["select_recette"] = nom_btn
                    st.rerun()
        else:
            st.warning("❌ Aucune recette ne correspond.")

    st.divider()

    # --- TA LISTE DÉROULANTE (CONSERVÉE À L'IDENTIQUE) ---
    # Elle montre tout par défaut, ou les résultats si filtré
    options_select = [r['nom'].upper() for r in (resultats if filtre_actif else index)]
    options = ["---"] + sorted(options_select)
    
    valeur_actuelle = st.session_state.get("select_recette", "---")
    idx_depart = options.index(valeur_actuelle) if valeur_actuelle in options else 0
        
    choix = st.selectbox(
        "Sélectionner une recette directement", 
        options,
        index=idx_depart,
        key="choix_recette_gui",
        on_change=nettoyer_modif
    )

    st.session_state["select_recette"] = choix
    
    # --- AFFICHAGE DE LA FICHE (TES LOGIQUES INCHANGÉES) ---
    if choix != "---":
        info = next((r for r in index if r['nom'].upper() == choix), None)
        
        if info:
            conf = config_github()
            # ... ICI RESTE DE TON CODE (Requête GitHub, Mode Edition, etc.) ...
