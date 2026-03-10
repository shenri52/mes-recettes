import streamlit as st
import json
import requests
import base64
import datetime
from collections import Counter

def afficher():
    # --- STYLE CSS ---
    st.markdown("""
        <style>
        .block-container { padding-top: 1rem !important; max-width: 800px !important; margin: auto; }
        header { visibility: hidden;} 
        .stButton>button { 
            width: 100%; border-radius: 6px; padding: 5px; height: 2.8em; 
            font-size: 14px;
        }
        div.stButton > button:has(div[p=" "]), 
        div.stButton > button:empty,
        div.stButton > button[disabled] {
            background-color: transparent !important;
            border-color: transparent !important;
            color: transparent !important;
            box-shadow: none !important;
        }
        [data-testid="stVerticalBlock"] { gap: 0.3rem !important; }
        /* Style pour mettre en évidence la zone déjà connue */
        .stButton>button.known-zone { background-color: #0288d1 !important; color: white !important; }
        </style>
    """, unsafe_allow_html=True)

    # --- RÉCUPÉRATION SECRETS ---
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
        url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{path}"
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
        return requests.put(url, json=payload, headers=headers).status_code in [200, 201]

    # Initialisation data A5 et Index Produits
    if "data_a5" not in st.session_state:
        st.session_state.data_a5, st.session_state.sha_a5 = get_github_data(FILE_PATH)
        if st.session_state.data_a5 is None:
            st.session_state.data_a5 = {str(i): {"panier": [], "catalogue": []} for i in range(12)}
    
    if "index_zones" not in st.session_state:
        st.session_state.index_zones, st.session_state.sha_index = get_github_data(INDEX_PRODUITS_PATH)
        if st.session_state.index_zones is None: st.session_state.index_zones = {}

    if "offset_semaine" not in st.session_state: st.session_state.offset_semaine = 0

    # --- ZONE DE TRANSIT (ÉTAPE 1 + ÉTAPE 2) ---
    st.subheader("📦 Zone de Transit")
    
    c1, c2, c3 = st.columns([1, 2, 1])
    if c1.button("⬅️", key="prev_t"): st.session_state.offset_semaine -= 1; st.rerun()
    if c3.button("➡️", key="next_t"): st.session_state.offset_semaine += 1; st.rerun()
    
    aujourdhui = datetime.date.today()
    debut = (aujourdhui - datetime.timedelta(days=(aujourdhui.weekday() - 4) % 7)) + datetime.timedelta(weeks=st.session_state.offset_semaine)
    c2.markdown(f"<p style='text-align:center;'>Semaine du <b>{debut.strftime('%d/%m')}</b></p>", unsafe_allow_html=True)

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
    
    with st.container(border=True):
        if not counts:
            st.info("Aucun ingrédient.")
        else:
            for ing, qte in sorted(counts.items()):
                # On vérifie si l'ingrédient est déjà dans l'une des zones A5 pour ne pas l'afficher
                deja_present = False
                for z in st.session_state.data_a5.values():
                    if any(item['nom'] == ing for item in z["panier"]):
                        deja_present = True; break
                
                if not deja_present:
                    col_nom, col_z1, col_z2, col_z3, col_z4 = st.columns([2.5, 1, 1, 1, 1])
                    col_nom.write(f"**{ing}** ({qte})")
                    
                    # Zone connue ?
                    zone_pref = st.session_state.index_zones.get(ing)

                    for i, col_z in enumerate([col_z1, col_z2, col_z3, col_z4]):
                        z_id = str(i)
                        btn_label = f"[{i+1}]"
                        # Si c'est la zone connue, on pourrait changer le style (via CSS ou icône ici)
                        final_label = f"⭐ {i+1}" if zone_pref == z_id else f"{i+1}"
                        
                        if col_z.button(final_label, key=f"tr_{ing}_{z_id}"):
                            # 1. Ajouter au panier de la zone
                            st.session_state.data_a5[z_id]["panier"].append({"nom": ing, "qte": str(qte), "checked": False})
                            # 2. Sauvegarder A5
                            save_github_data(FILE_PATH, st.session_state.data_a5, st.session_state.sha_a5)
                            # 3. Mettre à jour l'index des zones
                            st.session_state.index_zones[ing] = z_id
                            save_github_data(INDEX_PRODUITS_PATH, st.session_state.index_zones, st.session_state.sha_index)
                            st.rerun()

    st.divider()

    # --- GRILLE PRINCIPALE A5 (INCHANGÉE) ---
    max_produits = 0
    for val in st.session_state.data_a5.values():
        max_produits = max(max_produits, len(val["panier"]))
    max_lignes = (max_produits + 1) // 2

    for i in range(0, 12, 2):
        cols = st.columns(2)
        for j in range(2):
            idx = str(i + j)
            if idx in st.session_state.data_a5:
                case = st.session_state.data_a5[idx]
                with cols[j]:
                    st.caption(f"Zone {int(idx)+1}")
                    with st.container(border=True):
                        panier = case["panier"]
                        for row_idx in range(max_lignes):
                            sub_cols = st.columns(2)
                            for k in range(2):
                                p_idx = (row_idx * 2) + k
                                if p_idx < len(panier):
                                    p = panier[p_idx]
                                    is_checked = p.get("checked", False)
                                    txt = f"{p['nom']} ({p['qte']})"
                                    label = f"~~{txt}~~" if is_checked else txt
                                    if sub_cols[k].button(label, key=f"vis_{idx}_{p_idx}"):
                                        p["checked"] = not is_checked
                                        save_github_data(FILE_PATH, st.session_state.data_a5, st.session_state.sha_a5)
                                        st.rerun()
                                else:
                                    sub_cols[k].button(" ", key=f"ghost_{idx}_{p_idx}", disabled=True)

    if st.button("🔄 Rafraîchir", use_container_width=True):
        st.session_state.data_a5, st.session_state.sha_a5 = get_github_data(FILE_PATH)
        st.session_state.index_zones, st.session_state.sha_index = get_github_data(INDEX_PRODUITS_PATH)
        st.rerun()
