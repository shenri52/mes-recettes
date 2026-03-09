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
    st.header("Planning")

    for k, f in [('index_complet', 'data/index_recettes.json'), ('planning_data', 'data/planning.json')]:
        if k not in st.session_state: st.session_state[k] = charger_donnees(f)
    
    if 'offset_semaine' not in st.session_state: st.session_state.offset_semaine = 0

    options = ["---"] + sorted([r['nom'] for r in st.session_state.index_complet])

    # 1. Navigation
    c1, c2, c3 = st.columns([1, 1, 1])
    if c1.button("Précédente", use_container_width=True): st.session_state.offset_semaine -= 1; st.rerun()
    if c2.button("Aujourd'hui", use_container_width=True): st.session_state.offset_semaine = 0; st.rerun()
    if c3.button("Suivante", use_container_width=True): st.session_state.offset_semaine += 1; st.rerun()

    # 2. Dates
    aujourdhui = datetime.date.today()
    debut = (aujourdhui - datetime.timedelta(days=(aujourdhui.weekday() - 4) % 7)) + datetime.timedelta(weeks=st.session_state.offset_semaine)
    st.markdown(f"<h3 style='text-align: center;'>Du {debut.strftime('%d/%m/%y')} au {(debut + datetime.timedelta(days=6)).strftime('%d/%m/%y')}</h3>", unsafe_allow_html=True)

    # 3. Tableau
    jours = ["Vendredi", "Samedi", "Dimanche", "Lundi", "Mardi", "Mercredi", "Jeudi"]
    temp = st.session_state.planning_data.copy()
    
    cols_h = st.columns([1.2, 2, 2])
    cols_h[1].markdown("**Midi**")
    cols_h[2].markdown("**Soir**")
    st.divider()

    for i, nom in enumerate(jours):
        d_j = debut + datetime.timedelta(days=i)
        d_str = d_j.isoformat()
        if d_str not in temp: temp[d_str] = {"midi": {"plat": "---", "comp": "---"}, "soir": {"plat": "---", "comp": "---"}}

        col_d, col_m, col_s = st.columns([1.2, 2, 2])
        bg = "#e1f5fe" if d_j == aujourdhui else "transparent"
        
        col_d.markdown(f"<div style='background:{bg};padding:10px;border-radius:5px;border:1px solid #ddd;height:95px;display:flex;flex-direction:column;justify-content:center;'><small>{nom}</small><br><b>{d_j.strftime('%d/%m/%y')}</b></div>", unsafe_allow_html=True)

        for rep, col in zip(["midi", "soir"], [col_m, col_s]):
            with col:
                r = temp[d_str].get(rep, {"plat": "---", "comp": "---"})
                p = st.selectbox("P", options, index=options.index(r.get("plat", "---")) if r.get("plat") in options else 0, key=f"p{d_str}{rep}", label_visibility="collapsed")
                with st.popover("Ajouter"):
                    c = st.selectbox("R", options, index=options.index(r.get("comp", "---")) if r.get("comp") in options else 0, key=f"c{d_str}{rep}", label_visibility="collapsed")
                temp[d_str][rep] = {"plat": p, "comp": c}

    # 4. Actions (Sauvegarde et Courses)
    st.divider()
    b1, b2 = st.columns(2)
    
    if b1.button("Enregistrer le planning", use_container_width=True):
        st.session_state.planning_data.update(temp)
        final = {k: v for k, v in st.session_state.planning_data.items() if k >= (aujourdhui - datetime.timedelta(days=10)).isoformat()}
        if sauvegarder_github("data/planning.json", final):
            st.session_state.planning_data = final
            st.success("Enregistré 💾"); time.sleep(1); st.rerun()

    if b2.button("Générer la liste de courses", use_container_width=True):
        liste_ingredients = []
        # Parcourir les 7 jours de la semaine affichée
        for i in range(7):
            d_str = (debut + datetime.timedelta(days=i)).isoformat()
            if d_str in temp:
                for rep in ["midi", "soir"]:
                    for type_p in ["plat", "comp"]:
                        nom_recette = temp[d_str][rep].get(type_p)
                        if nom_recette and nom_recette != "---":
                            # Chercher les ingrédients de cette recette
                            recette_data = next((r for r in st.session_state.index_complet if r['nom'] == nom_recette), None)
                            if recette_data and 'ingredients' in recette_data:
                                # On nettoie et on ajoute à la liste
                                liste_ingredients.extend([ing.strip().capitalize() for ing in recette_data['ingredients']])
        
        if liste_ingredients:
            st.subheader("🛒 Liste de courses")
            # Compter les occurrences
            counts = Counter(liste_ingredients)
            # Affichage trié par nom
            for ing in sorted(counts.keys()):
                suffixe = f" ({counts[ing]})" if counts[ing] > 1 else ""
                st.write(f"- {ing}{suffixe}")
        else:
            st.warning("Aucun plat sélectionné pour cette semaine.")
