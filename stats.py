import streamlit as st
import requests
import time
from datetime import datetime
from collections import Counter

# Importation des fonctions centralisées
from utils import get_github_config, charger_json_github, sauvegarder_json_github, scanner_depot_complet

def afficher():
    # --- FONCTIONS INTERNES DÉDIÉES AUX STATS ---
    def actualiser_donnees_stockage():
        """Scan complet du dépôt avec catégories détaillées et arrondis précis."""
        conf = get_github_config()
        with st.spinner("Analyse du dépôt en cours... 🔍"):
            tree = scanner_depot_complet()
            
            # On vérifie si le scan a réussi
            if tree:
                stats_comptage = {
                    "Recettes (JSON)": {"nb": 0, "poids": 0},
                    "Photos (Images)": {"nb": 0, "poids": 0},
                    "Fichiers Système & Apps": {"nb": 0, "poids": 0}
                }
                
                for item in tree:
                    if item.get('type') == 'blob':
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
                
                stats_neuves = {
                    "derniere_maj": datetime.now().strftime("%d/%m/%Y à %H:%M"),
                    "poids_total_mo": round(poids_total / (1024 * 1024), 2),
                    "details": [
                        {
                            "Type": k, 
                            "Nombre": v["nb"], 
                            "Mo": round(v["poids"] / (1024 * 1024), 2)
                        } for k, v in stats_comptage.items()
                    ]
                }
                
                if sauvegarder_json_github("data/data_stockage.json", stats_neuves, "📊 MAJ Stockage"):
                    return stats_neuves
        return None
    
    # --- DÉBUT DE L'AFFICHAGE ---
    st.header("📊 Statistiques")
    st.divider()
    
    # Utilisation de la fonction centralisée
    index = charger_json_github("data/index_recettes.json")
    
    if not index:
        st.warning("Aucune donnée disponible pour établir des statistiques.")
        return

    st.info(f"**Nombre total de recettes :** {len(index)}")
    
    # --- SECTION RÉPARTITION PAR CATÉGORIE & APPAREIL ---
    col1, col2 = st.columns(2)
    
    with col1:
        stats_cat = Counter(r.get('categorie', 'Non classé') for r in index)
        tab_cat = [{"Catégorie": k, "Nombre": v} for k, v in sorted(stats_cat.items())]
        
        st.dataframe(
            tab_cat,
            column_config={
                "Catégorie": st.column_config.TextColumn("Catégorie"),
                "Nombre": st.column_config.NumberColumn("Nombre", format="%d")
            },
            hide_index=True,
            use_container_width=True
        )

    with col2:
        stats_app = Counter(r.get('appareil', 'Aucun') for r in index)
        tab_app = [{"Appareil": k, "Nombre": v} for k, v in sorted(stats_app.items())]
        
        st.dataframe(
            tab_app,
            column_config={
                "Appareil": st.column_config.TextColumn("Appareil"),
                "Nombre": st.column_config.NumberColumn("Nombre", format="%d")
            },
            hide_index=True,
            use_container_width=True
        )

    st.divider()

    # --- SECTION STOCKAGE ---
    st.subheader("💾 Stockage")
    
    # Utilisation de la fonction centralisée
    data_s = charger_json_github("data/data_stockage.json")
    
    if data_s:
        col_info, col_btn = st.columns([3, 1])
        with col_info:
            st.info(f"**Poids total du dépôt :** {data_s['poids_total_mo']} Mo")
            st.caption(f"🕒 Dernière actualisation : **{data_s['derniere_maj']}**")
        
        with col_btn:
            st.write("") 
            if st.button("🔄 Actualiser"):
                if actualiser_donnees_stockage():
                    st.success("Mise à jour réussie !")
                    time.sleep(1)
                    st.rerun()
        
        details_data = [
            {
                "Type": d.get("Type"),
                "Nombre": int(d.get("Nombre", 0)),
                "Mo": float(d.get("Mo", 0))
            } for d in data_s['details']
        ]
              
        st.dataframe(
            details_data,
            column_config={
                "Type": st.column_config.TextColumn("Type"),
                "Nombre": st.column_config.NumberColumn("Nombre", format="%d"),
                "Mo": st.column_config.NumberColumn("Taille (Mo)", format="%.2f")
            },
            hide_index=True,
            use_container_width=True
        )        
    else:
        st.warning("⚠️ Aucun relevé de stockage trouvé.")
        if st.button("🚀 Créer le premier relevé"):
            if actualiser_donnees_stockage():
                st.success("Premier relevé créé !")
                time.sleep(1)
                st.rerun()
