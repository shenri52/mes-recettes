import streamlit as st
import requests
import json
import time
import datetime
import base64
from collections import Counter

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
    conf = config_github()
    url = f"https://raw.githubusercontent.com/{conf['owner']}/{conf['repo']}/main/data/index_recettes.json?t={int(time.time())}"
    res = requests.get(url)
    return res.json() if res.status_code == 200 else []

def afficher():
    def sauvegarder_github(chemin, donnees):
        conf = config_github()
        url = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/{chemin}"
        res_get = requests.get(url, headers=conf['headers'])
        sha = res_get.json().get('sha') if res_get.status_code == 200 else None
        contenu = base64.b64encode(json.dumps(donnees, indent=4, ensure_ascii=False).encode('utf-8')).decode('utf-8')
        payload = {"message": "MAJ Stats", "content": contenu}
        if sha: payload["sha"] = sha
        return requests.put(url, json=payload, headers=conf['headers']).status_code in [200, 201]

    def actualiser():
        conf = config_github()
        with st.spinner("Actualisation..."):
            res_tree = requests.get(f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/git/trees/main?recursive=1", headers=conf['headers'])
            index = charger_index()
            if res_tree.status_code == 200:
                tree = res_tree.json().get('tree', [])
                stats_c = {"Recettes (JSON)": {"nb": 0, "poids": 0}, "Photos (Images)": {"nb": 0, "poids": 0}, "Système": {"nb": 0, "poids": 0}}
                for item in tree:
                    if item.get('type') == 'blob':
                        p = item['path'].lower()
                        k = "Recettes (JSON)" if p.endswith('.json') else "Photos (Images)" if p.endswith(('.png','.jpg','.jpeg','.webp')) else "Système"
                        stats_c[k]["nb"] += 1
                        stats_c[k]["poids"] += item.get('size', 0)
                
                poids_mo = round(sum(d["poids"] for d in stats_c.values()) / (1024*1024), 2)
                data = {
                    "derniere_maj": datetime.datetime.now().strftime("%d/%m/%Y à %H:%M"),
                    "poids_total_mo": poids_mo,
                    "total_recettes": len(index),
                    "details_categories": [{"Catégorie": k, "Nombre": v} for k, v in Counter(r.get('categorie','?') for r in index).items()],
                    "details_appareils": [{"Appareil": k, "Nombre": v} for k, v in Counter(r.get('appareil','?') for r in index).items()],
                    "details_stockage": [{"Type": k, "Nombre": v["nb"], "Mo": round(v["poids"]/(1024*1024), 2)} for k, v in stats_c.items()]
                }
                if sauvegarder_github("data/data_stockage.json", data): return data
        return None

    # --- INTERFACE ---
    conf = config_github()
    url = f"https://raw.githubusercontent.com/{conf['owner']}/{conf['repo']}/main/data/data_stockage.json?t={int(time.time())}"
    res = requests.get(url)
    data_s = res.json() if res.status_code == 200 else None

    # Bouton et Date en haut
    if st.button("🔄 Actualiser les données", use_container_width=True):
        if actualiser(): st.rerun()

    if data_s:
        st.caption(f"🕒 Dernière actualisation : **{data_s.get('derniere_maj')}**")
        st.divider()

        st.subheader("🍳 Recettes")
        st.info(f"**Nombre total de recettes :** {data_s.get('total_recettes')}")
        c1, c2 = st.columns(2)
        c1.dataframe(data_s.get('details_categories'), hide_index=True, use_container_width=True)
        c2.dataframe(data_s.get('details_appareils'), hide_index=True, use_container_width=True)
        
        st.subheader("💾 Stockage")
        st.info(f"**Poids total :** {data_s.get('poids_total_mo')} Mo")
        st.dataframe(data_s.get('details_stockage'), hide_index=True, use_container_width=True)
    else:
        st.warning("⚠️ Aucune donnée. Veuillez cliquer sur Actualiser.")
