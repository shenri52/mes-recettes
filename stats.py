import streamlit as st
import requests
import json
import time
from collections import Counter

# --- CONFIGURATION TECHNIQUE ---
def config_github():
    """Récupère les identifiants GitHub depuis les secrets Streamlit."""
    return {
        "token": st.secrets["GITHUB_TOKEN"],
        "owner": st.secrets["REPO_OWNER"],
        "repo": st.secrets["REPO_NAME"],
        "headers": {
            "Authorization": f"token {st.secrets['GITHUB_TOKEN']}",
            "Accept": "application/vnd.github.v3+json"
        }
    }

def charger_index():
    """Charge l'index des recettes avec un timestamp pour éviter le cache navigateur."""
    conf = config_github()
    url = f"https://raw.githubusercontent.com/{conf['owner']}/{conf['repo']}/main/data/index_recettes.json?t={int(time.time())}"
    res = requests.get(url)
    return res.json() if res.status_code == 200 else []

def afficher():
    st.header("📊 Statistiques")
    st.divider()
    
    index = charger_index()
    if not index:
        st.warning("Aucune donnée disponible pour établir des statistiques.")
        return

    # --- 1. CHIFFRES CLÉS ---
    st.info(f"📊 **Nombre total de recettes :** {len(index)}")
    
    # --- 2. RÉPARTITION (CATÉGORIE & APPAREIL) ---
    col1, col2 = st.columns(2)
    
    # Utilisation de Counter pour compter et trier en 2 lignes au lieu de 10
    with col1:
        st.subheader("📁 Par Catégorie")
        stats_cat = Counter(r.get('categorie', 'Non classé') for r in index)
        tab_cat = [{"Catégorie": k, "Nombre": v} for k, v in sorted(stats_cat.items())]
        st.table(tab_cat)

    with col2:
        st.subheader("🔌 Par Appareil")
        stats_app = Counter(r.get('appareil', 'Aucun') for r in index)
        tab_app = [{"Appareil": k, "Nombre": v} for k, v in sorted(stats_app.items())]
        st.table(tab_app)

    # --- 3. POIDS ET STOCKAGE ---
    st.subheader("💾 Stockage")
    conf = config_github()
    # Récupération de l'arborescence complète du dépôt
    url_tree = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/git/trees/main?recursive=1"
    res = requests.get(url_tree, headers=conf['headers'])
    
    if res.status_code == 200:
        tree = res.json().get('tree', [])
        stats_fichiers = {
            "JSON (Recettes)": {"nombre": 0, "poids": 0},
            "Images (Photos)": {"nombre": 0, "poids": 0},
            "Système/Autres": {"nombre": 0, "poids": 0}
        }
        
        for item in tree:
            size = item.get('size', 0)
            path = item['path'].lower()
            
            # Classification par extension
            if path.endswith('.json'): key = "JSON (Recettes)"
            elif path.endswith(('.png', '.jpg', '.jpeg', '.webp')): key = "Images (Photos)"
            else: key = "Système/Autres"
            
            stats_fichiers[key]["nombre"] += 1
            stats_fichiers[key]["poids"] += size

        poids_total_mo = sum(f["poids"] for f in stats_fichiers.values()) / (1024 * 1024)
        st.info(f"**Poids total du dépôt :** {poids_total_mo:.2f} Mo")
        
        # Préparation du tableau final Mo par Mo
        donnees_tableau = [{
            "Type de fichier": t,
            "Nombre": i["nombre"],
            "Poids (Mo)": f"{i['poids']/(1024*1024):.2f}"
        } for t, i in stats_fichiers.items()]
            
        st.write("**Détail des ressources :**")
        st.table(donnees_tableau)

    st.divider()
