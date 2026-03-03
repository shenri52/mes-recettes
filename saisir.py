# --- 3. SYSTÈME D'INGRÉDIENTS ---
    st.write("### Ingrédients")
    
    # Zone Quantité seule au-dessus
    quantite = st.text_input("1. Quantité", placeholder="ex: 200g, 2 pincées...")

    # Alignement sur une seule ligne : Liste (40%) | Saisie libre (40%) | Bouton (20%)
    col_list, col_new, col_btn = st.columns([2, 2, 1])

    with col_list:
        choix = st.selectbox("Choisir existant", [""] + st.session_state.base_ingredients, label_visibility="collapsed")

    with col_new:
        nouvel_ing = st.text_input("Nouveau...", placeholder="Si absent...", label_visibility="collapsed")

    with col_btn:
        if st.button("➕", use_container_width=True):
            if nouvel_ing and nouvel_ing not in st.session_state.base_ingredients:
                st.session_state.base_ingredients.append(nouvel_ing)
                st.session_state.base_ingredients.sort()
                st.rerun()

    # Bouton de validation pour la recette
    if st.button("✅ Valider cet ingrédient dans la recette", use_container_width=True):
        ing_final = choix if choix else nouvel_ing
        if ing_final and quantite:
            st.session_state.ingredients_recette.append({"Quantité": quantite, "Ingrédient": ing_final})
            st.rerun()
        else:
            st.warning("Remplissez la quantité et l'ingrédient.")
