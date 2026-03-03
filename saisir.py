import streamlit as st
import pandas as pd
from PIL import Image
import io

def afficher():
    st.markdown("<h2 style='text-align: center;'>➕ Saisie Manuelle</h2>", unsafe_allow_html=True)

    # --- 1. NOM DU PLAT ---
    nom_plat = st.text_input("Nom du plat", placeholder="Ex: Lasagnes maison")

    # --- 2. INGRÉDIENTS (Tableau libre) ---
    st.write("### Ingrédients")
    
    # On initialise le tableau s'il n'existe pas
    if 'df_ingredients' not in st.session_state:
        st.session_state.df_ingredients = pd.DataFrame([{"Quantité": "", "Ingrédient": ""}])

    # Saisie libre dans le tableau
    ingredients_edite = st.data_editor(
        st.session_state.df_ingredients, 
        num_rows="dynamic", 
        use_container_width=True,
        column_config={
            "Quantité": st.column_config.TextColumn("Quantité (ex: 200g)"),
            "Ingrédient": st.column_config.TextColumn("Ingrédient (Tapez librement)")
        },
        key="editeur_ingredients"
    )

    # --- 3. ÉTAPES ---
    st.write("### Préparation")
    etapes = st.text_area("Description des étapes", height=150, placeholder="1. Préchauffer le four...\n2. Mélanger...")

    # --- 4. LIEN HTTP ---
    st.write("### Source")
    lien_url = st.text_input("Lien vers la recette (URL)", placeholder="https://www.exemple.com")

    # --- 5. MÉDIAS (Plusieurs Images ou PDF) ---
    st.write("### Médias (Photos ou PDF)")
    fichiers = st.file_uploader(
        "Sélectionnez vos fichiers", 
        type=["jpg", "jpeg", "png", "pdf"], 
        accept_multiple_files=True
    )

    if fichiers:
        cols = st.columns(3) # Pour afficher les aperçus en petit
        for i, f in enumerate(fichiers):
            if f.type in ["image/png", "image/jpeg"]:
                img = Image.open(f)
                # Compression "sans perte" pour l'affichage
                with cols[i % 3]:
                    st.image(img, caption=f.name, use_container_width=True)
            else:
                with cols[i % 3]:
                    st.info(f"📄 {f.name[:15]}...")

    # --- 6. SAUVEGARDE ET APPRENTISSAGE ---
    st.write("---")
    if st.button("💾 Enregistrer la recette", use_container_width=True):
        if nom_plat:
            # Ici on récupère les nouveaux ingrédients pour la "mémoire" (optionnel)
            liste_saisie = ingredients_edite["Ingrédient"].dropna().tolist()
            
            # Message de succès
            st.success(f"La recette '{nom_plat}' a été saisie avec succès !")
            
            # --- LOGIQUE DE COMPRESSION SANS PERTE (Pour le stockage futur) ---
            # Pour chaque image, on pourrait faire :
            # img.save(buffer, format="PNG", optimize=True)
            
        else:
            st.error("Le nom du plat est obligatoire pour enregistrer.")

# Ce fichier doit être nommé saisir.py à la racine.
