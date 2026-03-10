import streamlit as st
import json
import requests
import base64

def afficher():
    # --- STYLE CSS (Remis à l'original) ---
    st.markdown("""
        <style>
        .block-container { padding-top: 1rem !important; max-width: 800px !important; margin: 4rem; }
        header { visibility: hidden;} 
        .stButton>button { 
            width: 100%; border-radius: 6px; padding: 5px; height: 2.8em; 
            font-size: 14px;
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
    def get_data():
        url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
        headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            res = r.json()
            content = json.loads(base64.b64decode(res['content']).decode('utf-8'))
            return content, res['sha']
        return {str(i): {"panier": [], "catalogue": []} for i in range(12)}, None

    def save_data(data, sha):
        url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        content_encoded = base64.b64encode(json.dumps(data, indent=2).encode('utf-8')).decode('utf-8')
        payload = {"message": "🔄 Sync A5", "content": content_encoded, "sha": sha, "branch": BRANCH}
        requests.put(url, json=payload, headers=headers)

    # Initialisation si vide
    if "data_a5" not in st.session_state:
        st.session_state.data_a5, st.session_state.sha_a5 = get_data()

    # --- GRILLE PRINCIPALE (2 COLONNES) ---
    for i in range(0, 12, 2):
        cols = st.columns(2)
        for j in range(2):
            idx = str(i + j)
            if idx in st.session_state.data_a5:
                case = st.session_state.data_a5[idx]
                with cols[j]:
                    with st.container(border=True):
                        # --- AFFICHAGE INTERNE : 2 INGRÉDIENTS CÔTE À CÔTE ---
                        panier = case["panier"]
                        for p_idx in range(0, len(panier), 2):
                            sub_cols = st.columns(2)
                            for k in range(2):
                                if p_idx + k < len(panier):
                                    p = panier[p_idx + k]
                                    is_checked = p.get("checked", False)
                                    
                                    # Formatage du label (Barré si coché)
                                    txt = f"{p['nom']} ({p['qte']})"
                                    label = f"~~{txt}~~" if is_checked else txt
                                    
                                    if sub_cols[k].button(label, key=f"vis_{idx}_{p_idx+k}"):
                                        p["checked"] = not is_checked
                                        save_data(st.session_state.data_a5, st.session_state.sha_a5)
                                        st.rerun()

    # --- NAVIGATION ET CONTRÔLES ---
    if st.button("🔄 Rafraîchir", use_container_width=True):
        st.session_state.data_a5, st.session_state.sha_a5 = get_data()
        st.rerun()

    st.write(" ")
