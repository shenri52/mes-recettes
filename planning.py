import streamlit as st
import datetime
import json
import requests
import time
import base64
from collections import Counter

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
    return res.json() if res.status_code == 200 else {}

def sauvegarder_github(chemin, contenu_dict):
    conf = config_github()
    url = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/{chemin}"
    res_get = requests.get(url, headers=conf['headers'])
    sha = res_get.json().get('sha') if res_get.status_code == 200 else None
    contenu_json = json.dumps(contenu_dict, indent=4, ensure_ascii=False)
    contenu_b64 = base64.b64encode(contenu_json.encode('utf-8')).decode('utf-8')
    data = {"message": "MAJ Planning", "content": contenu_b64, "branch": "main", "sha": sha} if sha else {"message": "MAJ Planning", "content": contenu_b64, "branch": "main"}
    return requests.put(url, headers=conf['headers'], json=data).status_code in [200, 201]

# --- INTERFACE PLANNING ---
def afficher():
    st.header("📅 Mon planning")
    
    if 'index_complet' not in st.session_state: st.session_state.index_complet = charger_donnees("data/index_recettes.json")
    if 'planning_data' not in st.session_state: st.session_state.planning_data = charger_donnees("data/planning.json")
    if 'offset_semaine' not in st.session_state: st.session_state.offset_semaine = 0

    options = ["---"] + sorted([r['nom'] for r in st.session_state.index_complet])

    # 1. Navigation Compacte
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
    
    st.write("") 
    c_head_label, c_head_m, c_head_s = st.columns([1.2, 2, 2])
    with c_head_m: st.markdown("<p style='text-align:center; font-weight:bold; margin-bottom:0;'>Midi</p>", unsafe_allow_html=True)
    with c_head_s: st.markdown("<p style='text-align:center; font-weight:bold; margin-bottom:0;'>Soir</p>", unsafe_allow_html=True)
    st.divider()

    for i, nom in enumerate(jours):
        d_j = debut + datetime.timedelta(days=i)
        d_str = d_j.isoformat()
        
        if d_str not in temp: 
            temp[d_str] = {"midi": [], "soir": []}

        col_d, col_m, col_s = st.columns([1.2, 2, 2])
        
        is_today = (d_j == aujourdhui)
        bg = "#e1f5fe" if is_today else "transparent"
        border = "2px solid #0288d1" if is_today else "1px solid #ddd"
        text_color = "#000000" if is_today else "inherit"
        
        col_d.markdown(f"""
            <div style='background:{bg}; color:{text_color}; padding:10px; border-radius:5px; border:{border}; min-height:102px; display:flex; flex-direction:column; justify-content:center;'>
                <small style='color:{text_color}; font-weight:normal;'>{nom}</small><br><b style='color:{text_color}; font-size:1.1em;'>{d_j.strftime('%d/%m/%y')}</b>
            </div>
        """, unsafe_allow_html=True)

        for rep, col in zip(["midi", "soir"], [col_m, col_s]):
            with col:
                # Récupération de la liste des plats (initialisation si besoin)
                plats = temp[d_str].get(rep, [])
                if isinstance(plats, dict): plats = [] # Migration ancienne structure
                
                # Affichage des plats existants
                for idx, p_nom in enumerate(plats):
                    if st.button(p_nom, key=f"del_{d_str}{rep}{idx}", use_container_width=True, help="Cliquer pour supprimer"):
                        plats.pop(idx)
                        temp[d_str][rep] = plats
                        st.session_state.planning_data.update(temp)
                        st.rerun()
                
                # Bouton d'ajout (max 3 plats)
                if len(plats) < 3:
                    with st.popover("➕ Ajouter", use_container_width=True):
                        choix = st.selectbox("Choisir", options, key=f"sel_{d_str}{rep}")
                        if choix != "---":
                            plats.append(choix)
                            temp[d_str][rep] = plats
                            st.session_state.planning_data.update(temp)
                            st.rerun()

    # 3. Actions
    st.divider()
    
    b1, b2 = st.columns(2)
    
    if b1.button("💾 Enregistrer", use_container_width=True):
        st.session_state.planning_data.update(temp)
        final = {k: v for k, v in st.session_state.planning_data.items() if k >= (aujourdhui - datetime.timedelta(days=10)).isoformat()}
        if sauvegarder_github("data/planning.json", final):
            st.session_state.planning_data = final
            st.success("Enregistré 💾")
            time.sleep(1)
            st.rerun()

    if b2.button("🛒 Liste des courses", use_container_width=True):
        liste_ingredients = []
        for i in range(7):
            d_str = (debut + datetime.timedelta(days=i)).isoformat()
            if d_str in temp:
                for rep in ["midi", "soir"]:
                    plats_rep = temp[d_str].get(rep, [])
                    for nom_recette in plats_rep:
                        if nom_recette and nom_recette != "---":
                            recette_data = next((rec for rec in st.session_state.index_complet if rec['nom'] == nom_recette), None)
                            if recette_data and 'ingredients' in recette_data:
                                liste_ingredients.extend([ing.strip().capitalize() for ing in recette_data['ingredients']])
        
        if liste_ingredients:
            st.subheader("🛒 Liste des courses")
            counts = Counter(liste_ingredients)
            for ing in sorted(counts.keys()):
                suffixe = f" ({counts[ing]})" if counts[ing] > 1 else ""
                st.write(f"- {ing}{suffixe}")

    st.divider()
