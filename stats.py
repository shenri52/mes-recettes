import streamlit as st
import requests
import json
import time
import datetime
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
    def sauvegarder_fichier_github(chemin_fichier, donnees):
        """Gère la création ET la mise à jour avec le SHA (sécurité)."""
        conf = config_github()
        url = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/{chemin_fichier}"
        
        # 1. On vérifie si le fichier existe pour récupérer son SHA (l'empreinte actuelle)
        res_get = requests.get(url, headers=conf['headers'])
        sha = res_get.json().get('sha') if res_get.status_code == 200 else None
    
        # 2. Préparation du contenu (JSON -> Base64)
        contenu_json = json.dumps(donnees, indent=4, ensure_ascii=False)
        contenu_base64 = base64.b64encode(contenu_json.encode('utf-8')).decode('utf-8')
    
        # 3. Envoi (PUT crée si pas de SHA, met à jour si SHA présent)
        payload = {"message": "📊 MAJ Stockage", "content": contenu_base64}
        if sha: payload["sha"] = sha
    
        res_put = requests.put(url, json=payload, headers=conf['headers'])
        return res_put.status_code in [200, 201]
    
    def actualiser_donnees_stockage():
        """Scan complet du dépôt GitHub et enregistrement du résultat."""
        conf = config_github()
        with st.spinner("Analyse du dépôt en cours... 🔍"):
            # On demande l'arbre (tree) complet à GitHub
            url_tree = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/git/trees/main?recursive=1"
            res = requests.get(url_tree, headers=conf['headers'])
            
            if res.status_code == 200:
                tree = res.json().get('tree', [])
                # Calcul précis du poids (en octets) par type de fichier
                p_json = sum(i.get('size', 0) for i in tree if i['path'].lower().endswith('.json'))
                p_img = sum(i.get('size', 0) for i in tree if i['path'].lower().endswith(('.png', '.jpg', '.jpeg', '.webp')))
                
                # Création du dictionnaire de stats avec la date du jour
                stats = {
                    "derniere_maj": datetime.datetime.now().strftime("%d/%m/%Y à %H:%M"),
                    "poids_total_mo": round((p_json + p_img) / (1024 * 1024), 2),
                    "details": [
                        {"Type": "Recettes (JSON)", "Mo": round(p_json/(1024*1024), 2)},
                        {"Type": "Photos (Images)", "Mo": round(p_img/(1024*1024), 2)}
                    ]
                }
                # On tente de sauvegarder ce bilan dans data/data_stockage.json
                if sauvegarder_fichier_github("data/data_stockage.json", stats):
                    return stats
        return None
    
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
    
    # 1. Tentative de lecture du fichier pré-calculé
    conf = config_github()
    url_s = f"https://raw.githubusercontent.com/{conf['owner']}/{conf['repo']}/main/data/data_stockage.json?t={int(time.time())}"
    res_s = requests.get(url_s)
    data_s = res_s.json() if res_s.status_code == 200 else None

    # 2. Si le fichier existe, on l'affiche simplement (très rapide)
    if data_s:
        col_info, col_btn = st.columns([3, 1])
        with col_info:
            st.info(f"**Poids total du dépôt :** {data_s['poids_total_mo']} Mo")
            st.caption(f"🕒 Dernière actualisation : **{data_s['derniere_maj']}**")
        with col_btn:
            st.write("") # Calage
            if st.button("🔄 Actualiser"):
                if actualiser_donnees_stockage():
                    st.success("Données mises à jour !")
                    time.sleep(1)
                    st.rerun()
        
        st.write("**Répartition :**")
        st.table(data_s['details'])
        
    else:
        # 3. Si le fichier n'existe pas encore (première utilisation)
        st.warning("⚠️ Aucun relevé de stockage trouvé.")
        if st.button("🚀 Créer le premier relevé"):
            if actualiser_donnees_stockage():
                st.rerun()
    st.divider()
