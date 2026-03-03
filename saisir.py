import streamlit as st
import pandas as pd

def afficher():
    st.markdown("<h2 style='text-align: center;'>➕ Saisie Manuelle</h2>", unsafe_allow_html=True)

    # 1. Initialisation de la mémoire des ingrédients
    if 'suggestions' not in st.session_state:
        st.session_state.suggestions = sorted(["Sel", "Poivre", "Farine", "Sucre", "Beurre", "Oeuf"])

    # 2. Nom du plat
    nom_plat = st.text_input("Nom du plat")

    # 3. SYSTÈME D'APPRENTISSAGE : Ajout d'un nouvel ingrédient à la "mémoire"
    new_ing = st.text_input("✨ Ajouter un nouvel ingrédient à la base (si absent)", placeholder="Ex: Curcuma...")
    if st.button("Ajouter à mes suggestions"):
        if new_ing and new_ing not in st.session_state.suggestions:
            st.session_state.suggestions.append(new_ing)
            st.session_state.suggestions.sort()
            st.success(f"'{new_ing}' ajouté !")
            st.rerun()

    # 4. LE TABLEAU (Modifié pour être libre)
    st.write("### Liste des ingrédients de la recette")
    
    if 'df_ingredients' not in st.session_state:
        st.session_state.df_ingredients = pd.DataFrame([{"Quantité": "", "Ingrédient": ""}])

    # On utilise TextColumn (plus libre) au lieu de SelectboxColumn
    ingredients_edite = st.data_editor(
        st.session_state.df_ingredients, 
        num_rows="dynamic", 
        use_container_width=True,
        column_config={
            "Quantité": st.column_config.TextColumn("Quantité"),
            "Ingrédient": st.column_config.TextColumn("Ingrédient (Tapez librement)") 
        },
        key="mon_editeur"
    )

    # Affichage des suggestions actuelles pour aide visuelle
    with st.expander("Voir mes ingrédients enregistrés"):
        st.write(", ".join(st.session_state.suggestions))

    # ... (Le reste : Étapes, Médias, Bouton Enregistrer)
