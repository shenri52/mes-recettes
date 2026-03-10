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
        /* Rendre les boutons fantômes (texte vide) invisibles */
        div.stButton > button:has(div[p=" "]), 
        div.stButton > button:empty,
        div.stButton > button[disabled] {
            background-color: transparent !important;
            border-color: transparent !important;
            color: transparent !important;
            box-shadow: none !important;
        }
        [data-testid="stVerticalBlock"] { gap: 0.5rem !important; }
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

    def save_data(data, sha):
        url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        content_encoded = base64.b64encode(json.dumps(data, indent=2).encode('utf-8')).decode('utf-8')
        payload = {"message": "🔄 Sync A5", "content": content_encoded, "sha": sha, "branch": BRANCH}
        requests.put(url, json=payload, headers=headers)

    # Initialisation data A5
    if "data_a5" not in st.session_state:
        st.session_state.data_a5, st.session_state.sha_a5 = get_github_data(FILE_PATH)
        if st.session_state.data_a5 is None:
            st.session_state.data_a5 = {str(i): {"panier": [], "catalogue": []} for i in range(12)}
    
    # Initialisation offset semaine pour transit
    if "offset_semaine" not in st.session_state:
        st.session_state.offset_semaine = 0

    # --- ÉTAPE 1 : ZONE DE TRANSIT (EXTRACTION PLANNING) ---
    st.subheader("📦 Zone de Transit")
    
    # Navigation semaine
    c1, c2, c3 = st.columns([1, 2, 1])
    if c1.button("⬅️", key="prev_transit"): 
        st.session_state.offset_semaine -= 1
        st.rerun()
    if c3.button("➡️", key="next_transit"): 
        st.session_state.offset_semaine += 1
        st.rerun()
    
    # Calcul des dates
    aujourdhui = datetime.date.today()
    debut = (aujourdhui - datetime.timedelta(days=(aujourdhui.weekday() - 4) % 7)) + datetime.timedelta(weeks=st.session_state.offset_semaine)
    c2.markdown(f"<p style='text-align:center; margin-top:5px;'>Semaine du <b>{debut.strftime('%d/%m')}</b></p>", unsafe_allow_html=True)

    # Chargement ingrédients depuis planning et index
    planning, _ = get_github_data("data/planning.json")
    index_recettes, _ = get_github_data("data/index_recettes.json")
    
    liste_brute = []
    if planning and index_recettes:
        # On scanne les 7 jours à partir du vendredi (début planning)
        for d_offset in range(7):
            d_str = (debut + datetime.timedelta(days=d_offset)).isoformat()
            if d_str in planning:
                for rep in ["midi", "soir"]:
                    for nom_r in planning[d_str].get(rep, []):
                        recette = next((r for r in index_recettes if r['nom'] == nom_r), None)
                        if recette and 'ingredients' in recette:
                            # On nettoie et on ajoute à la liste
                            liste_brute.extend([ing.strip().capitalize() for ing in recette['ingredients']])
    
    # Fusion des doublons avec Counter (Lait + Lait = Lait (2))
    counts = Counter(liste_brute)
    
    # Affichage Transit
    with st.container(border=True):
        if not counts:
            st.info("Aucun ingrédient dans le planning.")
        else:
            for ing, qte in sorted(counts.items()):
                col_ing, col_btn = st.columns([4, 1])
                col_ing.write(f"**{ing}** ({qte})")
                # Le bouton "+" servira à l'Etape 2 (transfert)
                col_btn.button("➕", key=f"add_tr_{ing}")

    st.divider()

    # --- CALCUL DE L'ALIGNEMENT A5 ---
    max_produits = 0
    for val in st.session_state.data_a5.values():
        max_produits = max(max_produits, len(val["panier"]))
    
    max_lignes = (max_produits + 1) // 2

    # --- GRILLE PRINCIPALE (2 COLONNES) ---
    for i in range(0, 12, 2):
        cols = st.columns(2)
        for j in range(2):
            idx = str(i + j)
            if idx in st.session_state.data_a5:
                case = st.session_state.data_a5[idx]
                with cols[j]:
                    # Container avec numéro de zone discret
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
                                        save_data(st.session_state.data_a5, st.session_state.sha_a5)
                                        st.rerun()
                                else:
                                    sub_cols[k].button(" ", key=f"ghost_{idx}_{p_idx}", disabled=True)

    # --- NAVIGATION ET CONTRÔLES ---
    if st.button("🔄 Rafraîchir", use_container_width=True):
        st.session_state.data_a5, st.session_state.sha_a5 = get_github_data(FILE_PATH)
        st.rerun()

    st.write(" ")
