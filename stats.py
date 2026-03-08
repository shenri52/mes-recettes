import streamlit as st
import requests
import json
import time

# --- CONFIGURATION TECHNIQUE (Récupération des secrets) ---
def config_github():
    return {
        "token": st.secrets["GITHUB_TOKEN"],
        "owner": st.secrets["REPO_OWNER"],
        "repo": st.secrets["REPO_NAME"],
        "headers": {
            "Authorization": f"token {st.secrets['GITHUB_TOKEN']}",
            "Accept": "application/vnd.github.v3+json"
        }
    }

# --- CHARGEMENT DE L'INDEX ---
def charger_index():
    conf = config_github()
    url = f"https://raw.githubusercontent.com/{conf['owner']}/{conf['repo']}/main/data/index_recettes.json?t={int(time.time())}"
    res = requests.get(url)
    if res.status_code == 200:
        return res.json()
    return []

# --- FONCTION PILOTE APPELÉE PAR APP.PY ---
def afficher():
    st.header("📊 Statistiques de la cuisine")
    index = charger_index()
    
    if not index:
        st.warning("Aucune donnée disponible pour établir des statistiques.")
        return

    # --- 1. CHIFFRES CLÉS ---
    total_recettes = len(index)
    st.metric("Nombre total de recettes", total_recettes)
    
    st.divider()

    # --- 2. RÉPARTITION PAR CATÉGORIE ET APPAREIL ---
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📁 Par Catégorie")
        stats_cat = {}
        for r in index:
            cat = r.get('categorie', 'Non classé')
            stats_cat[cat] = stats_cat.get(cat, 0) + 1
        st.bar_chart(stats_cat)

    with col2:
        st.subheader("🛠️ Par Appareil")
        stats_app = {}
        for r in index:
            app = r.get('appareil', 'Aucun')
            stats_app[app] = stats_app.get(app, 0) + 1
        st.bar_chart(stats_app)

    st.divider()

    # --- 3. POIDS ET TYPES DE FICHIERS ---
    st.subheader("💾 Stockage et Fichiers")
    conf = config_github()
    
    # Appel récursif pour scanner tout le dépôt
    url_tree = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/git/trees/main?recursive=1"
    res = requests.get(url_tree, headers=conf['headers'])
    
    if res.status_code == 200:
        tree = res.json().get('tree', [])
        
        poids_total = 0
        compte_fichiers = {"JSON (Recettes)": 0, "Images (Photos)": 0, "Système/Autres": 0}
        
        for item in tree:
            size = item.get('size', 0)
            poids_total += size
            
            ext = item['path'].lower()
            if ext.endswith('.json'):
                compte_fichiers["JSON (Recettes)"] += 1
            elif ext.endswith(('.png', '.jpg', '.jpeg', '.webp')):
                compte_fichiers["Images (Photos)"] += 1
            else:
                compte_fichiers["Système/Autres"] += 1

        st.info(f"**Poids total du dépôt :** {poids_total / 1024 / 1024:.2f} Mo")
        st.write("**Détail des fichiers présents :**")
        st.table({"Type": compte_fichiers.keys(), "Nombre": compte_fichiers.values()})

    # --- 4. ANALYSE DES AJOUTS (Saisie vs Import) ---
    st.divider()
    st.subheader("📥 Méthode d'ajout (Estimation)")
    
    # On estime qu'une recette avec moins de 2 ingrédients est un import photo/scan
    saisie = 0
    import_photo = 0
    
    for r in index:
        # On vérifie si les ingrédients sont détaillés ou non
        if len(r.get('ingredients', [])) <= 1:
            import_photo += 1
        else:
            saisie += 1
            
    c_s1, c_s2 = st.columns(2)
    c_s1.metric("✍️ Saisies manuelles", saisie)
    c_s2.metric("📸 Imports / Photos", import_photo)
    
    st.progress(saisie / total_recettes if total_recettes > 0 else 0, text="Ratio Saisie vs Import")
