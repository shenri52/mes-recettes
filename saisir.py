import streamlit as st
import pandas as pd
from PIL import Image
import io

def afficher():
    st.markdown("<h2 style='text-align: center;'>➕ Saisie Manuelle</h2>", unsafe_allow_html=True)
    
    # 1. Nom du plat
    nom_plat = st.text_input("Nom du plat", placeholder="Ex: Gratin Dauphinois")

    # 2. Ingrédients (Liste modifiable)
    st.write("### Ingrédients")
    # On crée une structure de base pour le tableau
    if 'df_ingredients' not in st.session_state:
        st.session_state.df_ingredients = pd.DataFrame([{"Quantité": "", "Ingrédient": ""}])

    # Éditeur de données interactif
    ingredients_edite = st.data_editor(
        st.session_state.df_ingredients, 
        num_rows="dynamic", 
        use_container_width=True,
        column_config={
            "Quantité": st.column_config.TextColumn("Quantité (ex: 500g)"),
            "Ingrédient": st.column_config.TextColumn("Ingrédient (ex: Pommes de terre)")
        }
    )

    # 3. Étapes de préparation
    st.write("### Préparation")
    etapes = st.text_area("Décrivez les étapes", height=200, placeholder="1. Éplucher les légumes...\n2. Cuire à 180°C...")

    # 4. Lien HTTP
    st.write("### Source")
    lien_web = st.text_input("Lien vers la recette originale (URL)", placeholder="https://www.exemple.com/recette")

    # 5. Médias (Images ou PDF)
    st.write("### Médias")
    fichiers_charges = st.file_uploader(
        "Ajouter des images ou des fichiers PDF", 
        type=["jpg", "jpeg", "png", "pdf"], 
        accept_multiple_files=True
    )

    if fichiers_charges:
        for fichier in fichiers_charges:
            if fichier.type in ["image/png", "image/jpeg"]:
                # Simulation de compression sans perte (Optimisation)
                img = Image.open(fichier)
                # On pourrait ici sauvegarder avec un niveau d'optimisation
                st.image(img, caption=f"Aperçu : {fichier.name}", width=200)
            else:
                st.write(f"📄 PDF chargé : {fichier.name}")

    # Bouton de sauvegarde final
    st.write("---")
    if st.button("💾 Enregistrer la recette", use_container_width=True):
        if nom_plat:
            st.success(f"Recette '{nom_plat}' prête à être enregistrée (Logique de stockage à venir) !")
        else:
            st.error("Veuillez au moins donner un nom à votre plat.")
