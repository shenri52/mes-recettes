import streamlit as st
import pandas as pd
from PIL import Image
import io

def afficher():
    st.markdown("<h2 style='text-align: center;'>➕ Saisie Manuelle</h2>", unsafe_allow_html=True)

    # --- 1. INITIALISATION DE LA MÉMOIRE (Apprentissage) ---
    if 'base_ingredients' not in st.session_state:
        st.session_state.base_ingredients = sorted(["Sel", "Poivre", "Farine", "Sucre", "Beurre", "Oeuf", "Lait", "Oignon", "Ail"])
    
    if 'ingredients_recette' not in st.session_state:
        st.session_state.ingredients_recette = []

    # --- 2. NOM DU PLAT ---
    nom_plat = st.text_input("Nom du plat", placeholder="Ex: Lasagnes maison")

    # --- 3. SYSTÈME D'INGRÉDIENTS ---
    st.write("### Ingrédients")
    
    # Zone Quantité au-dessus
    quantite = st.text_input("1. Quantité", placeholder="ex: 200g, 2 cuillères à soupe...")

    # Ligne : Liste déroulante
    choix = st.selectbox("2. Choisir un ingrédient existant", [""] + st.session_state.base_ingredients)

    # Ligne : Ajout si absent (Saisie + Bouton côte à côte)
    col_input, col_btn = st.columns([4, 1])
    with col_input:
        nouvel_ing = st.text_input("Ou ajouter un nouvel ingrédient", placeholder="Nom de l'ingrédient absent...")
    with col_btn:
        st.write("##") # Petit décalage pour aligner le bouton avec le champ
        if st.button("➕"):
            if nouvel_ing and nouvel_ing not in st.session_state.base_ingredients:
                st.session_state.base_ingredients.append(nouvel_ing)
                st.session_state.base_ingredients.sort()
                st.success(f"Ajouté !")
                st.rerun()

    # Bouton de validation pour la recette
    if st.button("✅ Valider cet ingrédient dans la recette", use_container_width=True):
        ing_final = choix if choix else nouvel_ing
        if ing_final and quantite:
            st.session_state.ingredients_recette.append({"Quantité": quantite, "Ingrédient": ing_final})
            st.rerun()
        else:
            st.warning("Veuillez remplir la quantité et l'ingrédient.")

    # Affichage de la liste en cours
    if st.session_state.ingredients_recette:
        st.table(pd.DataFrame(st.session_state.ingredients_recette))
        if st.button("🗑️ Vider la liste"):
            st.session_state.ingredients_recette = []
            st.rerun()

    # --- 4. ÉTAPES ---
    st.write("### Préparation")
    etapes = st.text_area("Description des étapes", height=150)

    # --- 5. LIEN HTTP ---
    st.write("### Source")
    lien_url = st.text_input("Lien vers la recette (URL)")

    # --- 6. MÉDIAS ---
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

    # --- 7. ENREGISTREMENT FINAL ---
    st.write("---")
    if st.button("💾 Enregistrer la recette complète", use_container_width=True):
        if nom_plat and st.session_state.ingredients_recette:
            st.success(f"Recette '{nom_plat}' prête !")
        else:
            st.error("Nom et ingrédients requis.")
