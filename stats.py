def afficher_statistiques():
    index = charger_index()
    st.header("📊 Statistiques")
    
    if not index:
        st.warning("Aucune donnée disponible pour établir des statistiques.")
        return

    # --- 1. CHIFFRES CLÉS ---
    total_recettes = len(index)
    st.metric("Nombre total de recettes", total_recettes)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📁 Par Catégorie")
        stats_cat = {}
        for r in index:
            cat = r.get('categorie', 'Non classé')
            stats_cat[cat] = stats_cat.get(cat, 0) + 1
        
        # Affichage sous forme de table pour la clarté
        st.table({"Catégorie": stats_cat.keys(), "Nombre": stats_cat.values()})

    with col2:
        st.subheader("🛠️ Par Appareil")
        stats_app = {}
        for r in index:
            app = r.get('appareil', 'Aucun')
            stats_app[app] = stats_app.get(app, 0) + 1
        st.table({"Appareil": stats_app.keys(), "Nombre": stats_app.values()})

    st.divider()

    # --- 2. POIDS ET TYPES DE FICHIERS (Appel API GitHub) ---
    st.subheader("💾 Stockage et Fichiers")
    conf = config_github()
    
    # On récupère l'arborescence complète pour calculer le poids
    url_tree = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/git/trees/main?recursive=1"
    res = requests.get(url_tree, headers=conf['headers'])
    
    if res.status_code == 200:
        tree = res.json().get('tree', [])
        
        poids_total = 0
        detail_poids = {"JSON (Recettes)": 0, "Images": 0, "Autres": 0}
        compte_fichiers = {"JSON": 0, "Images": 0, "Autres": 0}
        
        for item in tree:
            size = item.get('size', 0)
            poids_total += size
            
            if item['path'].endswith('.json'):
                detail_poids["JSON (Recettes)"] += size
                compte_fichiers["JSON"] += 1
            elif item['path'].lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                detail_poids["Images"] += size
                compte_fichiers["Images"] += 1
            else:
                detail_poids["Autres"] += size
                compte_fichiers["Autres"] += 1

        # Affichage du poids total converti en Mo
        st.info(f"**Poids total du dépôt :** {poids_total / 1024 / 1024:.2f} Mo")

        c_p1, c_p2 = st.columns(2)
        with c_p1:
            st.write("**Répartition du poids (Ko) :**")
            poids_ko = {k: f"{v/1024:.1f} Ko" for k, v in detail_poids.items()}
            st.json(poids_ko)
        
        with c_p2:
            st.write("**Nombre de fichiers :**")
            st.bar_chart(compte_fichiers)

    # --- 3. ANALYSE DES AJOUTS ---
    st.divider()
    st.subheader("📥 Méthode d'ajout")
    # On déduit l'import photo si la liste d'images n'est pas vide et les étapes sont courtes
    # Note : GitHub ne stocke pas nativement "l'origine", on se base sur le contenu
    stats_ajout = {"Saisie Manuelle": 0, "Import Photo / Scan": 0}
    
    for r in index:
        # Si on a des images mais très peu de texte dans les étapes, c'est probablement un scan
        # (Logique à affiner selon tes habitudes)
        if len(r.get('ingredients', [])) < 2:
            stats_ajout["Import Photo / Scan"] += 1
        else:
            stats_ajout["Saisie Manuelle"] += 1
            
    st.write("Estimation basée sur la structure des données :")
    st.progress(stats_ajout["Saisie Manuelle"] / total_recettes, 
                text=f"Saisie : {stats_ajout['Saisie Manuelle']}")
    st.progress(stats_ajout["Import Photo / Scan"] / total_recettes, 
                text=f"Imports/Photos : {stats_ajout['Import Photo / Scan']}")
