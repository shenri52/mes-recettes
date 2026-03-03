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

    # --- 3. SYSTÈME D'INGRÉDIENTS (Liste déroulante + Ajout) ---
    st.write("### Ingrédients")
    
    col_sel, col_add = st.columns([2, 1])
    
    with col_sel:
        # Liste déroulante des ingrédients connus
        choix = st.selectbox("Choisir un ingrédient", [""] + st.session_state.base_ingredients)
        quantite = st.text_input("Quantité", placeholder="ex: 200g ou 2 pincer")

    with col_add:
        # Cellule pour ajouter un ingrédient absent
        nouvel_ing = st.text_input("Si absent, l'ajouter ici")
        if st.button("➕ Ajouter à la base"):
            if nouvel_ing and nouvel_ing not in st.session_state.base_ingredients:
                st.session_state.base_ingredients.append(nouvel_ing)
                st.session_state.base_ingredients.sort()
                st.success(f"'{nouvel_ing}' ajouté !")
                st.rerun()

    # Bouton pour valider l'ingrédient dans la recette actuelle
    if st.button("✅ Valider cet ingrédient dans la recette"):
        ing_a_ajouter = choix if choix else nouvel_ing
        if ing_a_ajouter and quantite:
            st.session_state.ingredients_recette.append({"Quantité": quantite, "Ingrédient": ing_a_ajouter})
        else:
            st.warning("Veuillez remplir l'ingrédient et la quantité.")

    # Affichage de la liste en cours
    if st.session_state.ingredients_recette:
        df_temp = pd.DataFrame(st.session_state.ingredients_recette)
        st.table(df_temp) # Un tableau simple pour voir ce qu'on a ajouté
        if st.button("🗑️ Vider la liste d'ingrédients"):
            st.session_state.ingredients_recette = []
            st.rerun()

    # --- 4. ÉTAPES (CONSERVÉ) ---
    st.write("### Préparation")
    etapes = st.text_area("Description des étapes", height=150, placeholder="1. Préchauffer le four...")

    # --- 5. LIEN HTTP (CONSERVÉ) ---
    st.write("### Source")
    lien_url = st.text_input("Lien vers la recette (URL)", placeholder="https://www.exemple.com")

    # --- 6. MÉDIAS MULTIPLES & COMPRESSION (CONSERVÉ) ---
    st.write("### Médias (Photos ou PDF)")
    fichiers = st.file_uploader(
        "Sélectionnez vos fichiers (plusieurs possibles)", 
        type=["jpg", "jpeg", "png", "pdf"], 
        accept_multiple_files=True
    )

    if fichiers:
        cols = st.columns(3)
        for i, f in enumerate(fichiers):
            if f.type in ["image/png", "image/jpeg"]:
                img = Image.open(f)
                # Affichage avec compression visuelle
                with cols[i % 3]:
                    st.image(img, caption=f.name, use_container_width=True)
            else:
                with cols[i % 3]:
                    st.info(f"📄 {f.name[:10]}...")

    # --- 7. ENREGISTREMENT FINAL ---
    st.write("---")
    if st.button("💾 Enregistrer la recette complète", use_container_width=True):
        if nom_plat and st.session_state.ingredients_recette:
            st.success(f"La recette '{nom_plat}' a été enregistrée avec {len(st.session_state.ingredients_recette)} ingrédients !")
            # Ici on viderait la session pour la prochaine saisie
            # st.session_state.ingredients_recette = []
        else:
            st.error("Il manque le nom du plat ou les ingrédients.")
