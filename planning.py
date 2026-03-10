import streamlit as st
import datetime
import json
import requests
import time
import base64

# --- FONCTIONS TECHNIQUES ---
def config_github():
    return {
        "token": st.secrets["GITHUB_TOKEN"],
        "owner": st.secrets["REPO_OWNER"],
        "repo": st.secrets["REPO_NAME"],
        "headers": {"Authorization": f"token {st.secrets['GITHUB_TOKEN']}", "Accept": "application/vnd.github.v3+json"}
    }

def charger_donnees(chemin):
    conf = config_github()
    url = f"https://raw.githubusercontent.com/{conf['owner']}/{conf['repo']}/main/{chemin}?t={int(time.time())}"
    res = requests.get(url)
    if res.status_code == 200:
        return res.json()
    return [] if "plats_rapides" in chemin else {}

def sauvegarder_github(chemin, contenu_dict_ou_liste):
    conf = config_github()
    url = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/{chemin}"
    res_get = requests.get(url, headers=conf['headers'])
    sha = res_get.json().get('sha') if res_get.status_code == 200 else None
    contenu_json = json.dumps(contenu_dict_ou_liste, indent=4, ensure_ascii=False)
    contenu_b64 = base64.b64encode(contenu_json.encode('utf-8')).decode('utf-8')
    data = {"message": f"MAJ {chemin}", "content": contenu_b64, "branch": "main"}
    if sha: data["sha"] = sha
    return requests.put(url, headers=conf['headers'], json=data).status_code in [200, 201]

# --- INTERFACE PLANNING ---
def afficher():
    st.header("📅 Mon planning")
    
    if 'index_complet' not in st.session_state: st.session_state.index_complet = charger_donnees("data/index_recettes.json")
    if 'planning_data' not in st.session_state: st.session_state.planning_data = charger_donnees("data/planning.json")
    if 'plats_rapides' not in st.session_state: st.session_state.plats_rapides = charger_donnees("data/plats_rapides.json")
    if 'offset_semaine' not in st.session_state: st.session_state.offset_semaine = 0

    noms_recettes = [r['nom'] for r in st.session_state.index_complet]
    options = ["---"] + sorted(noms_recettes + st.session_state.plats_rapides)

    # 1. Navigation
    aujourdhui = datetime.date.today()
    debut = (aujourdhui - datetime.timedelta(days=(aujourdhui.weekday() - 4) % 7)) + datetime.timedelta(weeks=st.session_state.offset_semaine)
    fin = debut + datetime.timedelta(days=6)
    date_range_str = f"{debut.strftime('%d/%m/%y')} au {fin.strftime('%d/%m/%y')}"

    c1, c2, c3 = st.columns([1, 3, 1])
    with c1:
        if st.button("⬅️", key="prev_sem", use_container_width=True): 
            st.session_state.offset_semaine -= 1
            st.rerun()
    with c2:
        if st.button(f"Du {date_range_str}", key="reset_sem", use_container_width=True):
            st.session_state.offset_semaine = 0
            st.rerun()
    with c3:
        if st.button("➡️", key="next_sem", use_container_width=True):
            st.session_state.offset_semaine += 1
            st.rerun()

    # 2. Tableau
    jours = ["Vendredi", "Samedi", "Dimanche", "Lundi", "Mardi", "Mercredi", "Jeudi"]
    temp = st.session_state.planning_data.copy()
    
    st.divider()

    for i, nom in enumerate(jours):
        d_j = debut + datetime.timedelta(days=i)
        d_str = d_j.isoformat()
        
        if d_str not in temp: temp[d_str] = {"midi": [], "soir": []}

        col_d, col_m, col_s = st.columns([1.2, 2, 2])
        
        is_today = (d_j == aujourdhui)
        bg = "#e1f5fe" if is_today else "transparent"
        
        col_d.markdown(f"<div style='background:{bg}; padding:10px; border-radius:5px; border:1px solid #ddd;'><b>{nom}</b><br>{d_j.strftime('%d/%m')}</div>", unsafe_allow_html=True)

        for rep, col in zip(["midi", "soir"], [col_m, col_s]):
            with col:
                plats = temp[d_str].get(rep, [])
                if isinstance(plats, dict): plats = []
                
                for idx, p_nom in enumerate(plats):
                    if st.button(f"🗑️ {p_nom}", key=f"del_{d_str}{rep}{idx}", use_container_width=True):
                        plats.pop(idx)
                        temp[d_str][rep] = plats
                        st.session_state.planning_data.update(temp)
                        st.rerun()
                
                if len(plats) < 3:
                    with st.popover("➕", use_container_width=True):
                        choix = st.selectbox("Ajouter", options, key=f"sel_{d_str}{rep}{len(plats)}")
                        if choix != "---":
                            plats.append(choix)
                            temp[d_str][rep] = plats
                            st.session_state.planning_data.update(temp)
                            st.rerun()

    # 3. Plats Rapides
    st.divider()
    st.subheader("🍴 Plats rapides")
    col_add_txt, col_add_btn = st.columns([3, 1])
    with col_add_txt:
        nouveau_plat = st.text_input("Nom du plat", placeholder="Ex: Pâtes pesto", key="new_plat_input", label_visibility="collapsed")
    with col_add_btn:
        if st.button("➕", key="btn_add_rapide", use_container_width=True) and nouveau_plat:
            if nouveau_plat not in st.session_state.plats_rapides:
                st.session_state.plats_rapides.append(nouveau_plat)
                sauvegarder_github("data/plats_rapides.json", st.session_state.plats_rapides)
                st.rerun()

    # 4. Enregistrement
    st.divider()
    if st.button("💾 Enregistrer Planning", use_container_width=True):
        st.session_state.planning_data.update(temp)
        limite = (aujourdhui - datetime.timedelta(days=10)).isoformat()
        final = {k: v for k, v in st.session_state.planning_data.items() if k >= limite}
        if sauvegarder_github("data/planning.json", final):
            st.session_state.planning_data = final
            st.success("Enregistré ! 💾")
            time.sleep(1)
            st.rerun()
