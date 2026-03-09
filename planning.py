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
        "headers": {
            "Authorization": f"token {st.secrets['GITHUB_TOKEN']}",
            "Accept": "application/vnd.github.v3+json"
        }
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
    data = {"message": "MAJ Planning", "content": contenu_b64, "branch": "main"}
    if sha: data["sha"] = sha
    res = requests.put(url, headers=conf['headers'], json=data)
    return res.status_code in [200, 201]

# --- INTERFACE PLANNING ---
def afficher():
    st.header("Planning")

    if 'index_complet' not in st.session_state:
        st.session_state.index_complet = charger_donnees("data/index_recettes.json")
    if 'planning_data' not in st.session_state:
        st.session_state.planning_data = charger_donnees("data/planning.json")
    
    if 'offset_semaine' not in st.session_state:
        st.session_state.offset_semaine = 0

    options_repas = ["---"] + sorted([r['nom'] for r in st.session_state.index_complet])

    # 1. Barre de Navigation
    col_prev, col_today, col_next = st.columns([1, 1, 1])
    
    with col_prev:
        if st.button("Semaine precedente", use_container_width=True):
            st.session_state.offset_semaine -= 1
            st.rerun()
    with col_today:
        if st.button("Aujourd'hui", use_container_width=True):
            st.session_state.offset_semaine = 0
            st.rerun()
    with col_next:
        if st.button("Semaine suivante", use_container_width=True):
            st.session_state.offset_semaine += 1
            st.rerun()

    # 2. Calcul des dates (Vendredi a Jeudi)
    aujourdhui = datetime.date.today()
    ecart_vendredi = (aujourdhui.weekday() - 4) % 7
    vendredi_base = aujourdhui - datetime.timedelta(days=ecart_vendredi)
    debut_semaine = vendredi_base + datetime.timedelta(weeks=st.session_state.offset_semaine)
    fin_semaine = debut_semaine + datetime.timedelta(days=6)

    st.markdown(f"<h3 style='text-align: center;'>Du {debut_semaine.strftime('%d/%m/%y')} au {fin_semaine.strftime('%d/%m/%y')}</h3>", unsafe_allow_html=True)

    # 3. Affichage en Tableau
    jours_noms = ["Vendredi", "Samedi", "Dimanche", "Lundi", "Mardi", "Mercredi", "Jeudi"]
    temp_planning = st.session_state.planning_data.copy()

    c_label, c_midi, c_soir = st.columns([1.2, 2, 2])
    with c_midi: st.markdown("**Midi**")
    with c_soir: st.markdown("**Soir**")
    st.divider()

    for i, nom in enumerate(jours_noms):
        date_j = debut_semaine + datetime.timedelta(days=i)
        date_str = date_j.isoformat()
        
        if date_str not in temp_planning:
            temp_planning[date_str] = {
                "midi": {"plat": "---", "complement": "---"},
                "soir": {"plat": "---", "complement": "---"}
            }

        col_date, col_m, col_s = st.columns([1.2, 2, 2])
        
        with col_date:
            bg = "#e1f5fe" if date_j == aujourdhui else "transparent"
            st.markdown(f"""
                <div style="background-color: {bg}; padding: 10px; border-radius: 5px; border: 1px solid #ddd; height: 90px; display: flex; flex-direction: column; justify-content: center;">
                    <small style="line-height: 1.2;">{nom}</small><br><b style="font-size: 1.1em;">{date_j.strftime('%d/%m/%y')}</b>
                </div>
            """, unsafe_allow_html=True)

        for repas, col_repas in zip(["midi", "soir"], [col_m, col_s]):
            with col_repas:
                r_data = temp_planning[date_str][repas]
                # On gere l'ancien format (entree/dessert) s'il existe pour eviter les bugs
                val_plat = r_data.get("plat", "---")
                val_comp = r_data.get("complement", r_data.get("entree", "---"))
                
                p_idx = options_repas.index(val_plat) if val_plat in options_repas else 0
                c_idx = options_repas.index(val_comp) if val_comp in options_repas else 0

                p = st.selectbox("Plat", options_repas, index=p_idx, key=f"p_{date_str}_{repas}", label_visibility="collapsed")
                
                with st.popover("Ajouter un plat", use_container_width=True):
                    comp = st.selectbox("Recette", options_repas, index=c_idx, key=f"c_{date_str}_{repas}")
                
                temp_planning[date_str][repas] = {"plat": p, "complement": comp}
        st.write("") 

    # 4. Sauvegarde
    st.divider()
    if st.button("Enregistrer les modifications", use_container_width=True):
        st.session_state.planning_data.update(temp_planning)
        seuil = (aujourdhui - datetime.timedelta(days=10)).isoformat()
        final_data = {k: v for k, v in st.session_state.planning_data.items() if k >= seuil}
        
        if sauvegarder_github("data/planning.json", final_data):
            st.session_state.planning_data = final_data
            st.success("Enregistrement reussi")
            time.sleep(1)
            st.rerun()
