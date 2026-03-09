import streamlit as st
import datetime
import json
import requests
import time
import base64

# --- FONCTIONS TECHNIQUES (SANS EMOJI) ---
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

    # 1. Chargement Unique (Session State)
    if 'index_complet' not in st.session_state:
        st.session_state.index_complet = charger_donnees("data/index_recettes.json")
    if 'planning_data' not in st.session_state:
        st.session_state.planning_data = charger_donnees("data/planning.json")
    
    # Initialisation de la semaine affichée (0 = semaine en cours)
    if 'offset_semaine' not in st.session_state:
        st.session_state.offset_semaine = 0

    options_repas = ["---"] + sorted([r['nom'] for r in st.session_state.index_complet])

    # 2. Barre de Navigation entre les semaines
    col_prev, col_titre, col_next = st.columns([1, 3, 1])
    
    with col_prev:
        if st.button("Semaine précédente", use_container_width=True):
            st.session_state.offset_semaine -= 1
            st.rerun()
    
    with col_next:
        if st.button("Semaine suivante", use_container_width=True):
            st.session_state.offset_semaine += 1
            st.rerun()

    # 3. Calcul des dates de la semaine choisie
    aujourdhui = datetime.date.today()
    ecart_samedi = (aujourdhui.weekday() - 5) % 7
    samedi_base = aujourdhui - datetime.timedelta(days=ecart_samedi)
    debut_semaine = samedi_base + datetime.timedelta(weeks=st.session_state.offset_semaine)
    fin_semaine = debut_semaine + datetime.timedelta(days=6)

    with col_titre:
        st.markdown(f"<h3 style='text-align: center;'>Du {debut_semaine.strftime('%d/%m')} au {fin_semaine.strftime('%d/%m')}</h3>", unsafe_allow_html=True)

    # 4. Affichage des 7 jours
    jours_noms = ["Samedi", "Dimanche", "Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"]
    
    # On crée un dictionnaire temporaire pour stocker les modifs de la vue actuelle
    temp_planning = st.session_state.planning_data.copy()

    for i, nom in enumerate(jours_noms):
        date_j = debut_semaine + datetime.timedelta(days=i)
        date_str = date_j.isoformat()
        
        # Style pour aujourd'hui
        titre = f"{nom} {date_j.strftime('%d %b')}"
        if date_j == aujourdhui:
            titre = f"Aujourd'hui : {titre}"

        with st.expander(titre, expanded=(date_j == aujourdhui)):
            if date_str not in temp_planning:
                temp_planning[date_str] = {
                    "midi": {"plat": "---", "entree": "---", "dessert": "---"},
                    "soir": {"plat": "---", "entree": "---", "dessert": "---"}
                }

            for repas in ["midi", "soir"]:
                st.write(f"**{repas.capitalize()}**")
                c1, c2, c3 = st.columns(3)
                
                # Récupération sécurisée des données
                r_data = temp_planning[date_str][repas]
                
                p_idx = options_repas.index(r_data["plat"]) if r_data["plat"] in options_repas else 0
                e_idx = options_repas.index(r_data["entree"]) if r_data["entree"] in options_repas else 0
                d_idx = options_repas.index(r_data["dessert"]) if r_data["dessert"] in options_repas else 0

                with c1:
                    p = st.selectbox("Plat", options_repas, index=p_idx, key=f"p_{date_str}_{repas}")
                with c2:
                    e = st.selectbox("Entree", options_repas, index=e_idx, key=f"e_{date_str}_{repas}")
                with c3:
                    d = st.selectbox("Dessert", options_repas, index=d_idx, key=f"d_{date_str}_{repas}")
                
                temp_planning[date_str][repas] = {"plat": p, "entree": e, "dessert": d}

    # 5. Sauvegarde
    st.divider()
    if st.button("Enregistrer les modifications", use_container_width=True):
        # On fusionne les modifs dans le dictionnaire global
        st.session_state.planning_data.update(temp_planning)
        
        # Nettoyage (on garde 10 jours en arrière)
        seuil = (aujourdhui - datetime.timedelta(days=10)).isoformat()
        final_data = {k: v for k, v in st.session_state.planning_data.items() if k >= seuil}
        
        if sauvegarder_github("data/planning.json", final_data):
            st.session_state.planning_data = final_data
            st.success("Enregistrement reussi")
            time.sleep(1)
            st.rerun()
