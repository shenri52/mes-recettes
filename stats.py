import streamlit as st
import time
from utils import charger_json_github, actualiser_toutes_les_stats

def afficher():
    # --- DONNÉES ---
    data_s = charger_json_github("data/data_stockage.json")
    stats_r = charger_json_github("data/stats_recettes.json")

    # On extrait la date (si le fichier existe)
    derniere_maj = data_s.get('derniere_maj', 'Inconnue') if data_s else "Aucune"
    
    # 1. ACTUALISATION
    if st.button("🔄 Actualiser les données", use_container_width=True):
        with st.spinner("Synchronisation globale en cours... ⏳"):
            if actualiser_toutes_les_stats():
                st.success("Toutes les statistiques sont à jour !")
                time.sleep(0.5)
                st.rerun()
                
    st.caption(f"🕒 Dernière synchronisation : **{derniere_maj}**")

    # --- SECTION RECETTES ---
    st.header("📊 Statistiques")
    st.divider()
    
    if stats_r:
        st.info(f"**Nombre total de recettes :** {stats_r['total_recettes']}")
        
        col1, col2 = st.columns(2)
        with col1:
            tab_cat = [{"Catégorie": k, "Nombre": v} for k, v in stats_r['categories'].items()]
            st.dataframe(tab_cat, use_container_width=True, hide_index=True)

        with col2:
            tab_app = [{"Appareil": k, "Nombre": v} for k, v in stats_r['appareils'].items()]
            st.dataframe(tab_app, use_container_width=True, hide_index=True)
    else:
        st.warning("⚠️ Aucun résumé de recettes trouvé. Cliquez sur le bouton d'actualisation en haut.")

    st.divider()

    # --- SECTION STOCKAGE ---
    st.subheader("💾 Stockage")
    
    if data_s:
        st.info(f"**Poids total du dépôt :** {data_s['poids_total_mo']} Mo")
        
        # On affiche les détails (poids par type de fichier)
        st.dataframe(
            data_s['details'], 
            column_config={
                "Type": st.column_config.TextColumn("Type"),
                "Nombre": st.column_config.NumberColumn("Fichiers", format="%d"),
                "Mo": st.column_config.NumberColumn("Taille (Mo)", format="%.2f")
            },
            use_container_width=True, 
            hide_index=True
        )
    else:
        st.warning("⚠️ Aucun relevé de stockage trouvé.")
