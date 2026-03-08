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
    st.header("📊 Statistiques")
    index = charger_index()
    
    if not index:
        st.warning("Aucune donnée disponible pour établir des statistiques.")
        return

    # --- 1. CHIFFRES CLÉS ---
    total_recettes = len(index)
    st.info(f"📊 **Nombre total de recettes :** {total_recettes}")
    
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
    
    url_tree = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/git/trees/main?recursive=1"
    res = requests.get(url_tree, headers=conf['headers'])
    
    if res.status_code == 200:
        tree = res.json().get('tree', [])
        
        poids_total = 0
        # Initialisation des compteurs (Nombre et Poids)
        stats_fichiers = {
            "JSON (Recettes)": {"nombre": 0, "poids": 0},
            "Images (Photos)": {"nombre": 0, "poids": 0},
            "Système/Autres": {"nombre": 0, "poids": 0}
        }
        
        for item in tree:
            size = item.get('size', 0)
            poids_total += size
            ext = item['path'].lower()
            
            if ext.endswith('.json'):
                key = "JSON (Recettes)"
            elif ext.endswith(('.png', '.jpg', '.jpeg', '.webp')):
                key = "Images (Photos)"
            else:
                key = "Système/Autres"
            
            stats_fichiers[key]["nombre"] += 1
            stats_fichiers[key]["poids"] += size

        st.info(f"**Poids total du dépôt :** {poids_total / 1024 / 1024:.2f} Mo")
        
        # Préparation du tableau avec les colonnes demandées et arrondi inclu
        donnees_tableau = []
        for type_f, info in stats_fichiers.items():
            donnees_tableau.append({
                "Type de fichier": type_f,
                "Nombre": info["nombre"],
                "Poids (Mo)": round(info["poids"] / 1024 / 1024, 2)
            })
            
        st.write("**Détail des ressources :**")
        st.table(donnees_tableau)
