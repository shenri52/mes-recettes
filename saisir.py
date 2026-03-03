import streamlit as st
import pandas as pd
from PIL import Image

def afficher():
    st.markdown("<h2 style='text-align: center;'>➕ Saisie Manuelle</h2>", unsafe_allow_html=True)

    # 1. Initialisation de la liste de suggestions dans la mémoire de la session
    if 'suggestions_ingredients' not in st.session_state:
        # Liste de base au premier démarrage
        st.session_state.suggestions_ingredients = [
            "Sel", "Poivre", "Huile d'olive", "Oignon", "Ail", "Oeuf", "Farine", "Sucre"
        ]

    # 2. Nom du plat
    nom_plat = st.text_input("Nom du plat", placeholder="Ex: Gratin Dauphinois")

    # 3. Ingrédients avec auto-complétion dynamique
    st.write("### Ingrédients")
    
    if 'df_ingredients' not in st.session_state:
        st.session_state.df_ingredients = pd.DataFrame([{"Quantité": "", "Ingrédient": ""}])

    # Le data_editor utilise la liste de session_state pour les options
    ingredients_edite = st.data_editor(
        st.session_state.df_ingredients, 
        num_rows="dynamic", 
        use_container_width=True,
        column_config={
            "Quantité": st.column_config.TextColumn("Quantité"),
            "Ingrédient": st.column_config.SelectboxColumn(
                "Ingrédient",
                options=st.session_state.suggestions_ingredients,
                required=True
            )
        },
        key="editeur_ingredients" # Clé importante pour récupérer les données
    )

    # 4. Étapes, Liens et Médias (Code précédent conservé)
    etapes = st.text_area("Étapes de préparation")
    fichiers_charges = st.file_uploader("Images ou PDF", accept_multiple_files=True)

    # 5. BOUTON ENREGISTRER (C'est ici que l'apprentissage se fait)
    if st.button("💾 Enregistrer la recette", use_container_width=True):
        if nom_plat:
            # Récupérer les ingrédients saisis dans l'éditeur
            nouveaux_saisis = ingredients_edite["Ingrédient"].tolist()
            
            # Apprentissage : Ajouter les nouveaux ingrédients à la liste de suggestions s'ils n'y sont pas
            for ing in nouveaux_saisis:
                if ing and ing not in st.session_state.suggestions_ingredients:
                    st.session_state.suggestions_ingredients.append(ing)
            
            # Trier la liste pour que ce soit plus propre la prochaine fois
            st.session_state.suggestions_ingredients.sort()
            
            st.success(f"Recette '{nom_plat}' enregistrée ! Les nouveaux ingrédients ont été ajoutés à vos suggestions.")
            st.rerun() # Relance pour mettre à jour la liste dans l'interface
        else:
            st.error("Veuillez donner un nom au plat.")
