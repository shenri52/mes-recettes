import streamlit as st
import requests
import json
import base64
import time

# --- CONSULTATION ---
def afficher():
    index = charger_index()
    st.header("📚 Mes recettes")
    st.write("---")

    # FILTRES (Version d'origine 4 colonnes)
    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
    recherche = c1.text_input("🔍 Rechercher", "").lower()
    
    cats = ["Tous"] + sorted(list(set(r.get('categorie', 'Non classé') for r in index)))
    apps = ["Tous"] + sorted(list(set(r.get('appareil', 'Aucun') for r in index)))
    
    tous_ings = []
    for r in index: 
        if r.get('ingredients'): tous_ings.extend(r['ingredients'])
    ings = ["Tous"] + sorted(list(set(tous_ings)))

    f_cat = c2.selectbox("Catégorie", cats)
    f_app = c3.selectbox("Appareil", apps)
    f_ing = c4.selectbox("Ingrédient", ings)

    # Filtrage
    resultats = [
        r for r in index 
        if (not recherche or recherche in r['nom'].lower())
        and (f_cat == "Tous" or r['categorie'] == f_cat)
        and (f_app == "Tous" or r['appareil'] == f_app)
        and (f_ing == "Tous" or f_ing in r.get('ingredients', []))
    ]

    noms_filtres = [r['nom'].upper() for r in resultats]
    id_unique = f"sel_{recherche}_{f_cat}_{f_app}_{f_ing}"
    
    # --- ZONE SÉLECTEUR + ICÔNE ACTUALISER ---
    st.write("📖 Sélectionner une recette")
    col_liste, col_btn = st.columns([0.9, 0.1])

    with col_liste:
        choix = st.selectbox("📖 Sélectionner une recette", ["---"] + noms_filtres, key=id_unique, label_visibility="collapsed")

    with col_btn:
        if st.button("🔄", help="Actualiser"):
            if 'index_recettes' in st.session_state:
                del st.session_state.index_recettes
            st.rerun()

    st.write("---")

    if choix != "---":
        info = resultats[noms_filtres.index(choix)]
        # Note: config_github() doit être accessible (soit dans ce fichier, soit via import)
        from app import config_github, supprimer_fichier_github, sauvegarder_index_global, charger_index
        
        url_full = f"https://raw.githubusercontent.com/{config_github()['owner']}/{config_github()['repo']}/main/{info['chemin']}"
        recette = requests.get(url_full).json()
        
        st.subheader(recette['nom'].upper())
        st.write(f"**Catégorie :** {recette.get('categorie', 'Non classé')}")
        st.write(f"**Appareil :** {recette.get('appareil', 'Aucun')}")
        
        col_t, col_i = st.columns([1, 1])
        with col_t:
            st.write("**Ingrédients :**")
            for i in recette.get('ingredients', []):
                st.write(f"- {i.get('Quantité', '')} {i.get('Ingrédient', '')}")
            st.write(f"**Instructions :**\n{recette.get('etapes')}")
        
        with col_i:
            images = recette.get('images', [])
            if images:
                # Gestion de l'index pour la navigation des photos
                if "img_idx" not in st.session_state or st.session_state.get("last_recette") != choix:
                    st.session_state.img_idx = 0
                    st.session_state.last_recette = choix

                img_url = f"https://raw.githubusercontent.com/{config_github()['owner']}/{config_github()['repo']}/main/{images[st.session_state.img_idx].strip('/')}"
                st.image(img_url, use_container_width=True)
                
                # Boutons de navigation
                if len(images) > 1:
                    nb_col1, nb_col2, nb_col3 = st.columns([1, 2, 1])
                    if nb_col1.button("⬅️", key="prev_img"):
                        st.session_state.img_idx = (st.session_state.img_idx - 1) % len(images)
                        st.rerun()
                    nb_col2.write(f"{st.session_state.img_idx + 1} / {len(images)}")
                    if nb_col3.button("➡️", key="next_img"):
                        st.session_state.img_idx = (st.session_state.img_idx + 1) % len(images)
                        st.rerun()

        st.divider()
        b1, b2 = st.columns(2)
        if b1.button("🗑️ Supprimer", use_container_width=True):
            if supprimer_fichier_github(info['chemin']):
                nouvel_index = [r for r in index if r['chemin'] != info['chemin']]
                sauvegarder_index_global(nouvel_index)
                st.rerun()
        if b2.button("✍️ Modifier", use_container_width=True):
            st.info("Modification bientôt disponible.")
