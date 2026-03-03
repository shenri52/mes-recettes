import streamlit as st
import pandas as pd
from PIL import Image

def afficher():
    st.markdown("<h2 style='text-align: center;'>➕ Saisie Manuelle</h2>", unsafe_allow_html=True)

    # --- 1. INITIALISATION ---
    if 'base_ingredients' not in st.session_state:
        st.session_state.base_ingredients = sorted(["Sel", "Poivre", "Farine", "Sucre", "Beurre", "Oeuf", "Lait", "Oignon", "Ail"])
    
    if 'ingredients_recette' not in st.session_state:
        st.session_state.ingredients_recette = []

    # --- 2. NOM DU PLAT ---
    nom_plat = st.text_input("Nom du plat", placeholder="Ex: Lasagnes maison")

    # --- 3. SYSTÈME D'INGRÉDIENTS (Sur une seule ligne) ---
    st.write("### Ingrédients")
    
    quantite = st.text_input("1. Quantité", placeholder="ex: 200g, 2 pincées...")

    # Alignement : Liste (40%) | Saisie libre (40%) | Bouton (10%)
    col_list, col_new, col_btn = st.columns([2, 2, 0.5])

    with col_list:
        choix = st.selectbox("Existant", [""] + st.session_state.base_ingredients, label_visibility="collapsed")

    with col_new:
        nouvel_ing = st.text_input("Nouveau", placeholder="Si absent...", label_visibility="collapsed")

    with col_btn:
        if st.button("➕", use_container_width=True):
            if nouvel_ing and nouvel_ing not in st.session_state.base_ingredients:
                st.session_state.base_ingredients.append(nouvel_ing)
                st.session_state.base_ingredients.sort()
                st.rerun()

    # Bouton de validation
    if st.button("✅ Valider cet ingrédient dans la recette", use_container_width=True):
        ing_final = choix if choix else nouvel_ing
        if ing_final and quantite:
            st.session_state.ingredients_recette.append({"Quantité": quantite, "Ingrédient": ing_final})
            st.rerun()
        else:
            st.warning("Veuillez remplir la quantité et l'ingrédient.")

    # Table de visualisation
    if st.session_state.ingredients_recette:
        # Utilise st.dataframe ou st.table avec hide_index=True
        st.dataframe(st.session_state.ingredients_recette, use_container_width=True, hide_index=True)
        if st.button("🗑️ Vider la liste"):
            st.session_state.ingredients_recette = []
            st.rerun()

    # --- 4. ÉTAPES, LIEN ET MÉDIAS ---
    st.write("### Préparation")
    etapes = st.text_area("Description des étapes", height=150)

    st.write("### Source")
    lien_url = st.text_input("Lien vers la recette (URL)")

    st.write("### Médias (Photos ou PDF)")
    fichiers = st.file_uploader("Ajouter des fichiers", type=["jpg", "jpeg", "png", "pdf"], accept_multiple_files=True)

    if fichiers:
        cols = st.columns(4)
        for i, f in enumerate(fichiers):
            with cols[i % 4]:
                if f.type in ["image/png", "image/jpeg"]:
                    st.image(Image.open(f), use_container_width=True)
                else:
                    st.info("📄 PDF")

    # --- 5. ENREGISTREMENT FINAL ---
    st.write("---")
    if st.button("💾 Enregistrer la recette complète", use_container_width=True):
        if nom_plat and st.session_state.ingredients_recette:
            st.success(f"Recette '{nom_plat}' enregistrée !")
        else:
            st.error("Le nom et au moins un ingrédient sont requis.")
