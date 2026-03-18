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
        """Scan complet du dépôt GitHub et enregistrement du résultat."""
        conf = config_github()
        with st.spinner("Analyse du dépôt en cours... 🔍"):
            url_tree = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/git/trees/main?recursive=1"
            res = requests.get(url_tree, headers=conf['headers'])
            
            if res.status_code == 200:
                tree = res.json().get('tree', [])
                p_json = sum(i.get('size', 0) for i in tree if i['path'].lower().endswith('.json'))
                p_img = sum(i.get('size', 0) for i in tree if i['path'].lower().endswith(('.png', '.jpg', '.jpeg', '.webp')))
                
                stats_neuves = {
                    "derniere_maj": datetime.datetime.now().strftime("%d/%m/%Y à %H:%M"),
                    "poids_total_mo": round((p_json + p_img) / (1024 * 1024), 2),
                    "details": [
                        {"Type": "Recettes (JSON)", "Mo": round(p_json/(1024*1024), 2)},
                        {"Type": "Photos (Images)", "Mo": round(p_img/(1024*1024), 2)}
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
        c_info, c_btn = st.columns([3, 1])
        with c_info:
            st.info(f"**Poids total du dépôt :** {data_s['poids_total_mo']} Mo")
            st.caption(f"🕒 Dernière actualisation : **{data_s['derniere_maj']}**")
        with c_btn:
            st.write("") 
            if st.button("🔄 Actualiser"):
                if actualiser_donnees_stockage():
                    st.success("Mise à jour réussie !")
                    time.sleep(1)
                    st.rerun()
        
        st.write("**Répartition :**")
        st.table(data_s['details'])
        
    else:
        st.warning("⚠️ Aucun relevé de stockage trouvé.")
        if st.button("🚀 Créer le premier relevé"):
            if actualiser_donnees_stockage():
                st.success("Premier relevé créé !")
                time.sleep(1)
                st.rerun()
