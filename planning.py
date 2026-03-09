import streamlit as st
import datetime
import json
import requests
import time
import base64

# --- UTILS TECHNIQUES ---
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

# --- LOGIQUE PLANNING ---
def afficher():
    st.header("Planning")

    # 1. Chargement des ressources (Optimisé via Session State)
    if 'index_complet' not in st.session_state:
        st.session_state.index_complet = charger_donnees("data/index_recettes.json")
    
    if 'planning_data' not in st.session_state:
        st.session_state.planning_data = charger_donnees("data/planning.json")

    index = st.session_state.index_complet
    # On trie les noms pour la liste déroulante
    liste_noms = sorted([r['nom'] for r in index])
    options_repas = ["---"] + liste_noms

    # 2. Calcul des dates (Samedi à Vendredi)
    aujourdhui = datetime.date.today()
    # On recule jusqu'au samedi précédent (0=Lun, 5=Sam)
    ecart_samedi = (aujourdhui.weekday() - 5) % 7
    samedi_actuel = aujourdhui - datetime.timedelta(days=ecart_samedi)
    
    # Historique : on commence le samedi d'avant (-1 semaine)
    date_depart = samedi_actuel - datetime.timedelta(weeks=1)

    # 3. Interface par onglets pour la lisibilité
    onglets = st.tabs(["Semaine Passée", "Semaine En cours", "Semaine +1", "Semaine +2", "Semaine +3"])
    
    nouvel_etat_planning = st.session_state.planning_data.copy()

    for i, onglet in enumerate(onglets):
        with onglet:
            # Debut de la semaine affichée
            debut_sem = date_depart + datetime.timedelta(weeks=i)
            
            for j in range(7):
                date_j = debut_sem + datetime.timedelta(days=j)
                date_str = date_j.isoformat() # Clé pour le JSON
                
                # Mise en évidence du jour actuel
                label_jour = f"{date_j.strftime('%A %d %b')}"
                if date_j == aujourdhui:
                    label_jour = f"👉 {label_jour.upper()} (AUJOURD'HUI)"

                with st.expander(label_jour):
                    # Initialisation si la date n'existe pas dans le JSON
                    if date_str not in nouvel_etat_planning:
                        nouvel_etat_planning[date_str] = {
                            "midi": {"plat": "---", "entree": "---", "dessert": "---"},
                            "soir": {"plat": "---", "entree": "---", "dessert": "---"}
                        }

                    for repas in ["midi", "soir"]:
                        st.write(f"**{repas.capitalize()}**")
                        col1, col2, col3 = st.columns(3)
                        
                        # Récupération des valeurs actuelles
                        val_p = nouvel_etat_planning[date_str][repas].get("plat", "---")
                        val_e = nouvel_etat_planning[date_str][repas].get("entree", "---")
                        val_d = nouvel_etat_planning[date_str][repas].get("dessert", "---")

                        # On s'assure que la valeur existe dans les options (gestion des erreurs)
                        idx_p = options_repas.index(val_p) if val_p in options_repas else 0
                        idx_e = options_repas.index(val_e) if val_e in options_repas else 0
                        idx_d = options_repas.index(val_d) if val_d in options_repas else 0

                        # Saisie
                        with col1:
                            p = st.selectbox("Plat", options_repas, index=idx_p, key=f"p_{date_str}_{repas}")
                        with col2:
                            e = st.selectbox("Entrée", options_repas, index=idx_e, key=f"e_{date_str}_{repas}")
                        with col3:
                            d = st.selectbox("Dessert", options_repas, index=idx_d, key=f"d_{date_str}_{repas}")
                        
                        # Mise à jour locale du dictionnaire
                        nouvel_etat_planning[date_str][repas] = {"plat": p, "entree": e, "dessert": d}

    # 4. Sauvegarde
    st.write("---")
    if st.button("Enregistrer les modifications", use_container_width=True):
        # Nettoyage automatique : on ne garde que ce qui a moins de 10 jours de retard
        date_limite = aujourdhui - datetime.timedelta(days=10)
        planning_nettoye = {k: v for k, v in nouvel_etat_planning.items() if k >= date_limite.isoformat()}
        
        if sauvegarder_github("data/planning.json", planning_nettoye):
            st.session_state.planning_data = planning_nettoye
            st.success("Planning mis à jour sur GitHub !")
            time.sleep(1)
            st.rerun()
