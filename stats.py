import streamlit as st
import requests
import json
import time
import datetime
import base64
from collections import Counter

# --- CONFIGURATION TECHNIQUE ---
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

def charger_index():
    """Charge l'index des recettes uniquement lors de l'actualisation globale."""
    conf = config_github()
    url = f"https://raw.githubusercontent.com/{conf['owner']}/{conf['repo']}/main/data/index_recettes.json?t={int(time.time())}"
    res = requests.get(url)
    return res.json() if res.status_code == 200 else []

def afficher():
    def sauvegarder_fichier_github(chemin_fichier, donnees):
        conf = config_github()
        url = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/{chemin_fichier}"
        res_get = requests.get(url, headers=conf['headers'])
        sha = res_get.json().get('sha') if res_get.status_code == 200 else None
        contenu_json = json.dumps(donnees, indent=4, ensure_ascii=False)
        contenu_base64 = base64.b64encode(contenu_json.encode('utf-8')).decode('utf-8')
        payload = {"message": "📊 MAJ Statistiques & Stockage", "content": contenu_base64}
        if sha: payload["sha"] = sha
        res_put = requests.put(url, json=payload, headers=conf['headers'])
        return res_put.status_code in [200, 201]
    
    def actualiser_donnees_stockage():
        """Met à jour le fichier data_stockage.json avec les stats des recettes ET des fichiers."""
        conf = config_github()
        with st.spinner("Analyse globale des données en cours... 🔍"):
            url_tree = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/git/trees/main?recursive=1"
            res_tree = requests.get(url_tree, headers=conf['headers'])
            
            # Récupération de l'index pour compiler les statistiques des recettes
            index = charger_index()
            stats_cat = Counter(r.get('categorie', 'Non classé') for r in index)
            stats_app = Counter(r.get('appareil', 'Aucun') for r in index)
            
            if res_tree.status_code == 200:
                tree = res_tree.json().get('tree', [])
                
                stats_comptage = {
                    "Recettes (JSON)": {"nb": 0, "poids": 0},
                    "Photos (Images)": {"nb": 0, "poids": 0},
                    "Fichiers Système & Apps": {"nb": 0, "poids": 0}
                }
                
                for item in tree:
                    if item.get('type') == 'blob':
                        size = item.get('size', 0)
                        path = item['path'].lower()
                        if path.endswith('.json'): key = "Recettes (JSON)"
                        elif path.endswith(('.png', '.jpg', '.jpeg', '.webp')): key = "Photos (Images)"
                        else: key = "Fichiers Système & Apps"
                        stats_comptage[key]["nb"] += 1
                        stats_comptage[key]["poids"] += size
                
                poids_total = sum(d["poids"] for d in stats_comptage.values())
                
                # Le fichier final contient TOUTES les statistiques
                stats_neuves = {
                    "derniere_maj": datetime.datetime.now().strftime("%d/%m/%Y à %H:%M"),
                    "poids_total_mo": round(poids_total / (1024 * 1024), 2),
                    "total_recettes": len(index),
                    "details_categories": [{"Catégorie": k, "Nombre": v} for k, v in sorted(stats_cat.items())],
                    "details_appareils": [{"Appareil": k, "Nombre": v} for k, v in sorted(stats_app.items())],
                    "details_stockage": [
                        {"Type": k, "Nombre": v["nb"], "Mo": round(v["poids"] / (1024 * 1024), 2)} 
                        for k, v in stats_comptage.items()
                    ]
                }
                
                if sauvegarder_fichier_github("data/data_stockage.json", stats_neuves):
                    return stats_neuves
        return None
    
    # --- DÉBUT DE L'AFFICHAGE ---
    
    conf = config_github()
    url_s = f"https://raw.githubusercontent.com/{conf['owner']}/{conf['repo']}/main/data/data_stockage.json?t={int(time.time())}"
    res_s = requests.get(url_s)
    data_s = res_s.json() if res_s.status_code == 200 else None
    
    # --- SECTION EN-TÊTE : ACTUALISATION TOUT EN HAUT ---
    st.button("🔄 Actualiser", use_container_width=True):
    st.caption(f"🕒 Dernière actualisation : **{data_s.get('derniere_maj', 'Inconnue')}**")

    # --- LECTURE EXCLUSIVE DEPUIS LE FICHIER DATA_STOCKAGE ---
    if data_s:
        # --- SECTION RÉPARTITION PAR CATÉGORIE & APPAREIL ---
        st.info(f"**Nombre total de recettes :** {data_s.get('total_recettes', 0)}")
        col1, col2 = st.columns(2)
        
        with col1:
            st.dataframe(
                data_s.get('details_categories', []),
                column_config={
                    "Catégorie": st.column_config.TextColumn("Catégorie"),
                    "Nombre": st.column_config.NumberColumn("Nombre", format="%d")
                },
                hide_index=True,
                use_container_width=True
            )

        with col2:
            st.dataframe(
                data_s.get('details_appareils', []),
                column_config={
                    "Appareil": st.column_config.TextColumn("Appareil"),
                    "Nombre": st.column_config.NumberColumn("Nombre", format="%d")
                },
                hide_index=True,
                use_container_width=True
            )

        # --- SECTION STOCKAGE ---
        st.info(f"**Poids total du dépôt :** {data_s.get('poids_total_mo', 0)} Mo")
        
        details_stockage = [
            {
                "Type": d.get("Type"),
                "Nombre": int(d.get("Nombre", 0)),
                "Mo": float(d.get("Mo", 0))
            } for d in data_s.get('details_stockage', [])
        ]
              
        st.dataframe(
            details_stockage,
            column_config={
                "Type": st.column_config.TextColumn("Type"),
                "Nombre": st.column_config.NumberColumn("Nombre", format="%d"),
                "Mo": st.column_config.NumberColumn("Taille (Mo)", format="%.2f")
            },
            hide_index=True,
            use_container_width=True
        )        
    else:
        st.warning("⚠️ Cliquez sur 'Actualiser' pour créer le premier relevé complet (Recettes + Stockage).")
