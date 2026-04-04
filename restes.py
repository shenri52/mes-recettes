import streamlit as st
from utils import charger_index, recuperer_donnees_index, ouvrir_fiche

def afficher():
    # --- INITIALISATION ---
    # On crée la liste qui va stocker les ingrédients choisis
    if 'mes_restes' not in st.session_state:
        st.session_state.mes_restes = []

    # --- BOUTON RETOUR ---
    def aller_accueil():
        # On vide la liste des ingrédients avant de repartir
        st.session_state.mes_restes = []
        st.session_state.page = 'accueil'

    st.button("⬅️ Retour à l'accueil", use_container_width=True, on_click=aller_accueil)
    st.divider()

    # --- SÉLECTION DES INGRÉDIENTS ---
    st.subheader("🛒 Qu'y a-t-il dans ton frigo ?")
    
    # On récupère la liste complète de tes ingrédients existants
    liste_ing, _ = recuperer_donnees_index()
    
    def ajouter_reste():
        choix = st.session_state.sel_reste
        # Si on choisit un vrai ingrédient et qu'il n'est pas déjà dans la liste
        if choix != "---" and choix not in st.session_state.mes_restes:
            st.session_state.mes_restes.append(choix)
            st.session_state.sel_reste = "---" # Remet la liste déroulante à zéro

    c1, c2 = st.columns([3, 1])
    with c1:
        st.selectbox("Choisis un ingrédient", liste_ing, key="sel_reste")
    with c2:
        st.write(" ") # Pour aligner le bouton avec le champ de saisie
        st.write(" ")
        st.button("➕ Ajouter", use_container_width=True, on_click=ajouter_reste)

    # --- LISTE DES INGRÉDIENTS SÉLECTIONNÉS ---
    if st.session_state.mes_restes:
        st.markdown("**Ingrédients à utiliser :**")
        for idx, ing in enumerate(st.session_state.mes_restes):
            col_txt, col_del = st.columns([0.85, 0.15])
            with col_txt:
                st.write(f"✅ {ing}")
            with col_del:
                if st.button("❌", key=f"del_reste_{idx}"):
                    st.session_state.mes_restes.pop(idx)
                    st.rerun()
    
    st.divider()

    # --- RECHERCHE DE RECETTES ---
    st.subheader("💡 Idées de recettes")
    
    if not st.session_state.mes_restes:
        st.info("Ajoute des ingrédients pour voir les recettes possibles ! 🥗")
    else:
        index = charger_index()
        recettes_trouvees = []
        
        # Logique : La recette doit contenir TOUS les ingrédients sélectionnés
        for recette in index:
            ing_recette = [i.lower() for i in recette.get('ingredients', [])]
            match_all = True
            
            for reste in st.session_state.mes_restes:
                # On vérifie si l'ingrédient choisi est présent dans la liste de la recette
                if not any(reste.lower() in ir for ir in ing_recette):
                    match_all = False
                    break
                    
            if match_all:
                recettes_trouvees.append(recette)

        # --- AFFICHAGE DES RÉSULTATS ---
        if recettes_trouvees:
            st.success(f"{len(recettes_trouvees)} recette(s) trouvée(s) ! 🎉")
            for r in recettes_trouvees:
                # Un bouton cliquable qui ouvre la fiche, comme dans le planning
                if st.button(f"📖 {r['nom']}", use_container_width=True, key=f"btn_r_{r['nom']}"):
                    ouvrir_fiche(r['nom'])
        else:
            st.warning("Aucune recette ne contient tous ces ingrédients en même temps. 🕵️‍♂️")
