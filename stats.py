    import streamlit as st
import requests
import json
import time
import datetime
import base64
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
    # --- FONCTIONS INTERNES (BIEN INDENTÉES) ---
    def sauvegarder_fichier_github(chemin_fichier, donnees):
        """Gère la création ET la mise à jour avec le SHA (sécurité)."""
        conf = config_github()
        url = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/{chemin_fichier}"
        
        res_get = requests.get(url, headers=conf['headers'])
        sha = res_get.json().get('sha') if res_get.status_code == 200 else None
    
        contenu_json = json.dumps(donnees, indent=4, ensure_ascii=False)
        contenu_base64 = base64.b64encode(contenu_json.encode('utf-8')).decode('utf-8')
    
        payload = {"message": "📊 MAJ Stockage", "content": contenu_base64}
        if sha: 
            payload["sha"] = sha
    
        res_put = requests.put(url, json=payload, headers=conf['headers'])
        return res_put.status_code in [200, 201]
    
    def actualiser_donnees_stockage():
        """Scan complet du dépôt avec catégories détaillées et arrondis précis."""
        conf = config_github()
        with st.spinner("Analyse du dépôt en cours... 🔍"):
            url_tree = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/git/trees/main?recursive=1"
            res = requests.get(url_tree, headers=conf['headers'])
            
            if res.status_code == 200:
                tree = res.json().get('tree', [])
                
                # Initialisation des compteurs
                stats_comptage = {
                    "Recettes (JSON)": {"nb": 0, "poids": 0},
                    "Photos (Images)": {"nb": 0, "poids": 0},
                    "Fichiers Système & Apps": {"nb": 0, "poids": 0}
                }
                
                for item in tree:
                    if item.get('type') == 'blob':  # On ne compte que les fichiers, pas les dossiers
                        size = item.get('size', 0)
                        path = item['path'].lower()
                        
                        if path.endswith('.json'):
                            key = "Recettes (JSON)"
                        elif path.endswith(('.png', '.jpg', '.jpeg', '.webp')):
                            key = "Photos (Images)"
                        else:
                            key = "Fichiers Système & Apps"
                        
                        stats_comptage[key]["nb"] += 1
                        stats_comptage[key]["poids"] += size
                
                poids_total = sum(d["poids"] for d in stats_comptage.values())
                
                # Construction du dictionnaire final
                stats_neuves = {
                    "derniere_maj": datetime.datetime.now().strftime("%d/%m/%Y à %H:%M"),
                    # Arrondi à 2 chiffres : round(valeur, 2)
                    "poids_total_mo": round(poids_total / (1024 * 1024), 2),
                    "details": [
                        {
                            "Type": k, 
                            "Nombre": v["nb"], 
                            "Mo": round(v["poids"] / (1024 * 1024), 2)
                        } for k, v in stats_comptage.items()
                    ]
                }
                
                if sauvegarder_fichier_github("data/data_stockage.json", stats_neuves):
                    return stats_neuves
        return None
    
    # --- DÉBUT DE L'AFFICHAGE ---
    st.header("📊 Statistiques")
    st.divider()
    
    index = charger_index()
    if not index:
        st.warning("Aucune donnée disponible pour établir des statistiques.")
        return

    st.info(f"📊 **Nombre total de recettes :** {len(index)}")
    
    col1, col2 = st.columns(2)
    
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

    st.divider()

    # --- SECTION STOCKAGE (CORRIGÉE) ---
    st.subheader("💾 Stockage")
    
    conf = config_github()
    url_s = f"https://raw.githubusercontent.com/{conf['owner']}/{conf['repo']}/main/data/data_stockage.json?t={int(time.time())}"
    res_s = requests.get(url_s)
    data_s = res_s.json() if res_s.status_code == 200 else None
    
    if data_s:
        col_info, col_btn = st.columns([3, 1])
        with col_info:
            st.info(f"**Poids total du dépôt :** {data_s['poids_total_mo']} Mo")
            st.caption(f"🕒 Dernière actualisation : **{data_s['derniere_maj']}**")
        
        # Le bouton actualiser utilisera la nouvelle fonction avec les 3 catégories
        with col_btn:
            st.write("") 
            if st.button("🔄 Actualiser"):
                if actualiser_donnees_stockage():
                    st.success("Mise à jour réussie !")
                    time.sleep(1)
                    st.rerun()
        
        st.write("**Répartition par type de ressources :**")

        # --- SECTION RÉPARTITION (ALIGNEE & PROPRE) ---
        # 1. On s'assure que les données sont numériques pour l'alignement automatique
        details_data = [
            {
                "Type": d.get("Type"),
                "Nombre": int(d.get("Nombre", 0)),
                "Mo": float(d.get("Mo", 0))
            } for d in data_s['details']
        ]
        
        st.write("**Répartition par type de ressources :**")
        
        # 2. Affichage avec configuration de colonnes
        st.dataframe(
            details_data,
            column_config={
                "Type": st.column_config.TextColumn("Type"),
                "Nombre": st.column_config.NumberColumn("Nombre", format="%d"),
                "Mo": st.column_config.NumberColumn(
                    "Taille (Mo)", 
                    format="%.2f", # Force 2 décimales
                )
            },
            hide_index=True, # Enlève la colonne 0, 1, 2 à gauche
            use_container_width=True # Prend toute la largeur
        )        
    else:
        st.warning("⚠️ Aucun relevé de stockage trouvé.")
        if st.button("🚀 Créer le premier relevé"):
            if actualiser_donnees_stockage():
                st.success("Premier relevé créé !")
                time.sleep(1)
                st.rerun()
    st.divider()
