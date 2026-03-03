# --- 1. CHARGEMENT DES DONNÉES ---
    # Ajout d'un bouton pour rafraîchir manuellement si besoin
    if st.button("🔄 Actualiser la bibliothèque"):
        if 'toutes_recettes' in st.session_state:
            del st.session_state.toutes_recettes
        st.rerun()

    if 'toutes_recettes' not in st.session_state:
        with st.spinner("Chargement de la bibliothèque..."):
            fichiers = charger_fichiers("data/recettes")
            data_recettes = []
            for f in fichiers:
                if f['name'].endswith('.json'):
                    # On utilise l'URL download_url pour avoir le contenu frais
                    content_res = requests.get(f['download_url'])
                    if content_res.status_code == 200:
                        try:
                            recette_data = content_res.json()
                            recette_data['chemin_json'] = f['path']
                            data_recettes.append(recette_data)
                        except:
                            continue
            st.session_state.toutes_recettes = data_recettes
