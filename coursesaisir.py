import streamlit as st
import json
import requests
import base64
import datetime
from collections import Counter
import time

def afficher():
    # --- STYLE CSS (Inchangé) ---
    st.markdown("""
        <style>
        .block-container { padding-top: 1rem !important; max-width: 800px !important; margin: auto; }
        header { visibility: hidden; } 
        .stButton>button { 
            width: 100%; border-radius: 6px; padding: 5px; height: 2.8em; 
            font-size: 14px;
        }
        .streamlit-expanderHeader { background-color: #f8f9fa; border-radius: 6px; }
        </style>
    """, unsafe_allow_html=True)

    try:
        GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
        REPO_OWNER = st.secrets["REPO_OWNER"]
        REPO_NAME = st.secrets["REPO_NAME"]
        BRANCH = st.secrets.get("BRANCH", "main")
    except KeyError:
        st.error("⚠️ Secrets GitHub manquants.")
        st.stop()

    FILE_PATH = "courses/data_a5.json"
    INDEX_PRODUITS_PATH = "data/index_produits_zones.json"

    # --- FONCTIONS DATA ---
    def get_github_data(path):
        t = int(time.time())
        url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{path}?t={t}"
        headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            res = r.json()
            content = json.loads(base64.b64decode(res['content']).decode('utf-8'))
            return content, res.get('sha')
        return None, None

    def save_github_data(path, data, sha, message="🔄 Sync"):
        url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{path}"
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        content_encoded = base64.b64encode(json.dumps(data, indent=2, ensure_ascii=False).encode('utf-8')).decode('utf-8')
        payload = {"message": message, "content": content_encoded, "branch": BRANCH}
        if sha: payload["sha"] = sha
        r = requests.put(url, json=payload, headers=headers)
        if r.status_code in [200, 201]:
            if path == FILE_PATH: st.session_state.sha_a5 = r.json()['content']['sha']
            if path == INDEX_PRODUITS_PATH: st.session_state.sha_index = r.json()['content']['sha']
            return True
        return False

    # Initialisation
    if "data_a5" not in st.session_state:
        st.session_state.data_a5, st.session_state.sha_a5 = get_github_data(FILE_PATH)
        if st.session_state.data_a5 is None:
            st.session_state.data_a5 = {str(i): {"panier": [], "catalogue": []} for i in range(12)}

    if "index_zones" not in st.session_state:
        st.session_state.index_zones, st.session_state.sha_index = get_github_data(INDEX_PRODUITS_PATH)
        if st.session_state.index_zones is None: st.session_state.index_zones = {}

    if "offset_semaine" not in st.session_state: st.session_state.offset_semaine = 0

    # --- SÉLECTEUR DE SEMAINE & ACTUALISER ---
    st.subheader("📦 Zone de Transit")
    
    c1, c2, c3 = st.columns([1, 2, 1])
    if c1.button("⬅️", key="prev_t"): 
        st.session_state.offset_semaine -= 1
        st.rerun()
    if c3.button("➡️", key="next_t"): 
        st.session_state.offset_semaine += 1
        st.rerun()
    
    aujourdhui = datetime.date.today()
    debut = (aujourdhui - datetime.timedelta(days=(aujourdhui.weekday() - 4) % 7)) + datetime.timedelta(weeks=st.session_state.offset_semaine)
    c2.markdown(f"<p style='text-align:center;'>Semaine du <b>{debut.strftime('%d/%m')}</b></p>", unsafe_allow_html=True)

    if st.button("🚀 Actualiser & Synchroniser", use_container_width=True):
        planning, _ = get_github_data("data/planning.json")
        index_recettes, _ = get_github_data("data/index_recettes.json")
        
        if planning and index_recettes:
            liste_brute = []
            for d_offset in range(7):
                d_str = (debut + datetime.timedelta(days=d_offset)).isoformat()
                if d_str in planning:
                    for rep in ["midi", "soir"]:
                        for nom_r in planning[d_str].get(rep, []):
                            recette = next((r for r in index_recettes if r['nom'] == nom_r), None)
                            if recette and 'ingredients' in recette:
                                liste_brute.extend([ing.strip().capitalize() for ing in recette['ingredients']])
            
            counts = Counter(liste_brute)
            for ing, qte in counts.items():
                # Classement Auto via l'Index
                zone_dest = st.session_state.index_zones.get(ing, "0")
                case = st.session_state.data_a5[zone_dest]
                
                trouve = False
                for p in case["panier"]:
                    if p["nom"].lower() == ing.lower():
                        p["qte"] = str(qte)
                        trouve = True
                        break
                if not trouve:
                    case["panier"].append({"nom": ing, "qte": str(qte), "checked": False})
                
                if ing not in case["catalogue"]:
                    case["catalogue"].append(ing)
                    case["catalogue"].sort()
            
            if save_github_data(FILE_PATH, st.session_state.data_a5, st.session_state.sha_a5):
                st.success("Synchronisation terminée ! ✨")
                time.sleep(0.5)
                st.rerun()

    st.divider()

    # --- GRILLE DES 12 CASES (CONTAINERS) ---
    for i in range(0, 12, 2):
        cols = st.columns(2)
        for j in range(2):
            idx = str(i + j)
            if idx in st.session_state.data_a5:
                case = st.session_state.data_a5[idx]
                with cols[j]:
                    # Ajout du numéro de Zone
                    st.caption(f"Zone {int(idx)+1}")
                    with st.container(border=True):
                        with st.form(key=f"form_{idx}", clear_on_submit=True):
                            choix = st.selectbox("Histo", ["-- Nouveau --"] + case["catalogue"], label_visibility="collapsed")
                            nom = st.text_input("Nom", placeholder="Produit", label_visibility="collapsed")
                            qte = st.text_input("Qté", placeholder="Qté", label_visibility="collapsed")
                            
                            if st.form_submit_button("Ajouter", use_container_width=True):
                                final_nom = nom.strip().capitalize() if choix == "-- Nouveau --" else choix
                                if final_nom:
                                    # Mise à jour classement auto (Index)
                                    st.session_state.index_zones[final_nom] = idx
                                    save_github_data(INDEX_PRODUITS_PATH, st.session_state.index_zones, st.session_state.sha_index)
                                    
                                    trouve = False
                                    for p in case["panier"]:
                                        if p["nom"].lower() == final_nom.lower():
                                            p["qte"] = qte.strip() or "1"
                                            trouve = True
                                            break
                                    if not trouve:
                                        case["panier"].append({"nom": final_nom, "qte": qte.strip() or "1", "checked": False})
                                    
                                    if final_nom not in case["catalogue"]:
                                        case["catalogue"].append(final_nom)
                                        case["catalogue"].sort()
                                    
                                    if save_github_data(FILE_PATH, st.session_state.data_a5, st.session_state.sha_a5):
                                        st.rerun()
                                        
                        for p_idx, p in enumerate(case["panier"]):
                            if st.button(f"{p['nom']} ({p['qte']})", key=f"btn_{idx}_{p_idx}"):
                                case["panier"].pop(p_idx)
                                if save_github_data(FILE_PATH, st.session_state.data_a5, st.session_state.sha_a5):
                                    st.rerun()

    st.divider()
    c_ref, c_res = st.columns(2)
    with c_ref:
        if st.button("🔄 Rafraîchir", use_container_width=True):
            st.session_state.data_a5, st.session_state.sha_a5 = get_github_data(FILE_PATH)
            st.session_state.index_zones, st.session_state.sha_index = get_github_data(INDEX_PRODUITS_PATH)
            st.rerun()
    with c_res:
        if st.button("🗑️ Vider la liste", use_container_width=True):
            for k in range(12): st.session_state.data_a5[str(k)]["panier"] = []
            if save_github_data(FILE_PATH, st.session_state.data_a5, st.session_state.sha_a5):
                st.rerun()
