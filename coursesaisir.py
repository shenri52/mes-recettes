import streamlit as st
import json
import requests
import base64
import datetime
from collections import Counter
import time

def afficher():
    # --- STYLE CSS (REPRIS DE TA VERSION) ---
    st.markdown("""
        <style>
        .block-container { padding-top: 1rem !important; max-width: 800px !important; margin: auto; }
        header { visibility: hidden; } 
        .stButton>button { 
            width: 100%; border-radius: 6px; padding: 5px; height: 2.8em; 
            font-size: 14px;
        }
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

    # Initialisation de la session
    if "data_a5" not in st.session_state:
        st.session_state.data_a5, st.session_state.sha_a5 = get_github_data(FILE_PATH)
        if st.session_state.data_a5 is None:
            st.session_state.data_a5 = {str(i): {"panier": [], "catalogue": []} for i in range(12)}

    if "index_zones" not in st.session_state:
        st.session_state.index_zones, st.session_state.sha_index = get_github_data(INDEX_PRODUITS_PATH)
        if st.session_state.index_zones is None: st.session_state.index_zones = {}

    if "offset_semaine" not in st.session_state: st.session_state.offset_semaine = 0
    if "exclus_transit" not in st.session_state: st.session_state.exclus_transit = []

    # --- LOGIQUE DE CALCUL DU PLANNING (DYNAMIQUE) ---
    aujourdhui = datetime.date.today()
    debut = (aujourdhui - datetime.timedelta(days=(aujourdhui.weekday() - 4) % 7)) + datetime.timedelta(weeks=st.session_state.offset_semaine)
    
    planning, _ = get_github_data("data/planning.json")
    index_recettes, _ = get_github_data("data/index_recettes.json")
    liste_brute = []
    if planning and index_recettes:
        for d_offset in range(7):
            d_str = (debut + datetime.timedelta(days=d_offset)).isoformat()
            if d_str in planning:
                for rep in ["midi", "soir"]:
                    for nom_r in planning[d_str].get(rep, []):
                        recette = next((r for r in index_recettes if r['nom'] == nom_r), None)
                        if recette and 'ingredients' in recette:
                            liste_brute.extend([ing.strip().capitalize() for ing in recette['ingredients']])
    counts = Counter(liste_brute)

    # --- ZONE DE TRANSIT ---
    st.subheader("📝 Préparer les courses")
    
    c1, c2, c3 = st.columns([1, 2, 1])
    if c1.button("⬅️", key="prev_t"): 
        st.session_state.offset_semaine -= 1
        st.session_state.exclus_transit = []
        st.rerun()
    if c3.button("➡️", key="next_t"): 
        st.session_state.offset_semaine += 1
        st.session_state.exclus_transit = []
        st.rerun()
    
    c2.markdown(f"<p style='text-align:center;'>Semaine du <b>{debut.strftime('%d/%m')}</b></p>", unsafe_allow_html=True)

    # BOUTON ACTUALISER (SYNCHRONISATION ACTIVE)
    if st.button("🚀 Actualiser / Classer la liste", use_container_width=True):
        if counts:
            for ing, qte in counts.items():
                zone_dest = st.session_state.index_zones.get(ing)
                if zone_dest:
                    trouve = False
                    for item in st.session_state.data_a5[str(zone_dest)]["panier"]:
                        if item['nom'] == ing:
                            item['qte'] = str(qte)
                            trouve = True
                            break
                    if not trouve:
                        st.session_state.data_a5[str(zone_dest)]["panier"].append({"nom": ing, "qte": str(qte), "checked": False})
            
            save_github_data(FILE_PATH, st.session_state.data_a5, st.session_state.sha_a5)
            st.rerun()

    # AFFICHAGE DE LA LISTE DE TRANSIT
    with st.container(border=True):
        items_transit = sorted(counts.items())
        visible_count = 0
        for ing, qte in items_transit:
            dans_panier = any(any(item['nom'] == ing for item in z["panier"]) for z in st.session_state.data_a5.values())
            if ing in st.session_state.exclus_transit or dans_panier:
                continue

            visible_count += 1
            col_nom, col_sel, col_add, col_del = st.columns([2, 1.5, 0.4, 0.4])
            col_nom.write(f"**{ing}** ({qte})")
            
            zone_pref = st.session_state.index_zones.get(ing, "0")
            try:
                idx_sel = int(zone_pref)
            except:
                idx_sel = 0

            options_zones = [str(i) for i in range(12)]
            zone_dest = col_sel.selectbox("Zone", options_zones, index=idx_sel, key=f"sel_{ing}", label_visibility="collapsed", format_func=lambda x: f"Zone {int(x)+1}")
            
            if col_add.button("➕", key=f"btn_add_{ing}"):
                st.session_state.data_a5[zone_dest]["panier"].append({"nom": ing, "qte": str(qte), "checked": False})
                st.session_state.index_zones[ing] = zone_dest
                save_github_data(FILE_PATH, st.session_state.data_a5, st.session_state.sha_a5)
                save_github_data(INDEX_PRODUITS_PATH, st.session_state.index_zones, st.session_state.sha_index)
                st.rerun()
            
            if col_del.button("➖", key=f"btn_del_{ing}"):
                st.session_state.exclus_transit.append(ing)
                st.rerun()

        if visible_count == 0:
            st.info("Tout est classé ! ✅")

    st.divider()

    # --- GRILLE DES 12 CASES ---
    for i in range(0, 12, 2):
        cols = st.columns(2)
        for j in range(2):
            idx = str(i + j)
            case = st.session_state.data_a5[idx]
            with cols[j]:
                st.caption(f"Zone {int(idx)+1}")
                with st.container(border=True):
                    with st.form(key=f"form_{idx}", clear_on_submit=True):
                        choix = st.selectbox("Histo", ["-- Nouveau --"] + case["catalogue"], label_visibility="collapsed")
                        nom = st.text_input("Nom", placeholder="Produit", label_visibility="collapsed")
                        qte = st.text_input("Qté", placeholder="Qté", label_visibility="collapsed")
                        
                        if st.form_submit_button("Ajouter", use_container_width=True):
                            final_nom = nom.strip().capitalize() if choix == "-- Nouveau --" else choix
                            if final_nom:
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
                                save_github_data(FILE_PATH, st.session_state.data_a5, st.session_state.sha_a5)
                                st.rerun()
                                    
                    for p_idx, p in enumerate(case["panier"]):
                        if st.button(f"{p['nom']} ({p['qte']})", key=f"btn_{idx}_{p_idx}"):
                            case["panier"].pop(p_idx)
                            save_github_data(FILE_PATH, st.session_state.data_a5, st.session_state.sha_a5)
                            st.rerun()

    st.divider()
    if st.button("🗑️ Vider tout le panier", use_container_width=True):
        for k in range(12): st.session_state.data_a5[str(k)]["panier"] = []
        save_github_data(FILE_PATH, st.session_state.data_a5, st.session_state.sha_a5)
        st.rerun()
