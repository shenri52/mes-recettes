import streamlit as st
import requests
import json
import base64

def config_github():
    return {
        "token": st.secrets["GITHUB_TOKEN"],
        "owner": st.secrets["REPO_OWNER"],
        "repo": st.secrets["REPO_NAME"],
        "headers": {"Authorization": f"token {st.secrets['GITHUB_TOKEN']}", "Accept": "application/vnd.github.v3+json"}
    }

def charger_fichiers(dossier):
    conf = config_github()
    url = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/{dossier}"
    res = requests.get(url, headers=conf['headers'])
    return res.json() if res.status_code == 200 else []

def supprimer_fichier_github(chemin):
    conf = config_github()
    url = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/{chemin}"
    get_res = requests.get(url, headers=conf['headers'])
    if get_res.status_code == 200:
        sha = get_res.json()['sha']
        requests.delete(url, headers=conf['headers'], json={"message": "Suppression", "sha": sha, "branch": "main"})
        return True
    return False

def afficher():
    st.header("📚 Mes recettes")

    if st.button("🔄 Actualiser la liste"):
        if 'toutes_recettes' in st.session_state: del st.session_state.toutes_recettes
        st.rerun()

    if 'toutes_recettes' not in st.session_state:
        with st.spinner("Chargement..."):
            fichiers = charger_fichiers("data/recettes")
            data_recettes = []
            for f in fichiers:
                if f['name'].endswith('.json'):
                    res = requests.get(f['download_url'])
                    if res.status_code == 200:
                        d = res.json()
                        d['chemin_json'] = f['path']
                        data_recettes.append(d)
            st.session_state.toutes_recettes = data_recettes

    col_s, col_a, col_i = st.columns([2, 1, 1])
    recherche = col_s.text_input("🔍 Rechercher", "").lower()
    filtre_app = col_a.selectbox("Appareil", ["Tous"] + list(set(r.get('appareil', 'Aucun') for r in st.session_state.toutes_recettes)))
    
    tous_ings = sorted(list(set(i.get('Ingrédient') for r in st.session_state.toutes_recettes for i in r.get('ingredients', []))))
    filtre_ing = col_i.selectbox("Ingrédient", ["Tous"] + tous_ings)

    recettes_f = [r for r in st.session_state.toutes_recettes if recherche in r['nom'].lower() 
                  and (filtre_app == "Tous" or r.get('appareil') == filtre_app)
                  and (filtre_ing == "Tous" or any(i.get('Ingrédient') == filtre_ing for i in r.get('ingredients', [])))]

    for idx, rec in enumerate(recettes_f):
        with st.expander(f"{rec.get('appareil', '🍳')} - {rec['nom']}"):
            c1, c2 = st.columns([1, 1])
            with c1:
                st.subheader("Ingrédients")
                for i in rec.get('ingredients', []): st.write(f"• {i['Quantité']} {i['Ingrédient']}")
                st.subheader("Préparation")
                st.write(rec.get('etapes', ""))
                if st.button(f"🗑️ Supprimer", key=f"del_{idx}"):
                    supprimer_fichier_github(rec['chemin_json'])
                    for img in rec.get('images', []): supprimer_fichier_github(img)
                    if rec.get('image'): supprimer_fichier_github(rec.get('image'))
                    del st.session_state.toutes_recettes
                    st.rerun()
            with c2:
                st.subheader("Médias")
                médias = rec.get('images', [])
                if not médias and rec.get('image'): médias = [rec.get('image')]
                
                for i, m in enumerate(médias):
                    res_m = requests.get(f"https://api.github.com/repos/{st.secrets['REPO_OWNER']}/{st.secrets['REPO_NAME']}/contents/{m}", headers=config_github()['headers'])
                    if res_m.status_code == 200:
                        data = base64.b64decode(res_m.json()['content'])
                        if m.lower().endswith('.pdf'):
                            st.download_button(f"📄 PDF {i+1}", data, file_name=m.split('/')[-1], key=f"pdf_{idx}_{i}")
                        else:
                            st.image(data, use_container_width=True)
