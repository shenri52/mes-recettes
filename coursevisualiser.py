import streamlit as st
import json
import requests
import base64
import time

def afficher():
    # --- STYLE CSS (STRICTEMENT TON ORIGINAL) ---
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

    def save_github_data(path, data, sha):
        url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{path}"
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        content_encoded = base64.b64encode(json.dumps(data, indent=2, ensure_ascii=False).encode('utf-8')).decode('utf-8')
        payload = {"message": "🛒 Check/Uncheck", "content": content_encoded, "branch": BRANCH}
        if sha: payload["sha"] = sha
        r = requests.put(url, json=payload, headers=headers)
        if r.status_code in [200, 201]:
            st.session_state.sha_a5 = r.json()['content']['sha']
            return True
        return False

    # Chargement unique au démarrage
    if "data_a5" not in st.session_state:
        st.session_state.data_a5, st.session_state.sha_a5 = get_github_data(FILE_PATH)
        if st.session_state.data_a5 is None:
            st.session_state.data_a5 = {str(i): {"panier": []} for i in range(12)}

    # --- AFFICHAGE DES 12 ZONES ---
    for i in range(0, 12, 2):
        cols_zones = st.columns(2)
        for j in range(2):
            idx = str(i + j)
            if idx in st.session_state.data_a5:
                case = st.session_state.data_a5[idx]
                with cols_zones[j]:
                    st.caption(f"Zone {int(idx)+1}")
                    with st.container(border=True):
                        panier = case.get("panier", [])
                        # On parcourt le panier 2 par 2 pour l'affichage en colonnes
                        for p_idx in range(0, len(panier), 2):
                            cols_ing = st.columns(2)
                            
                            # Ingrédient 1 (colonne gauche)
                            p1 = panier[p_idx]
                            txt1 = f"{p1['nom']} ({p1['qte']})"
                            label1 = f"~~{txt1}~~" if p1.get("checked", False) else txt1
                            if cols_ing[0].button(label1, key=f"vis_{idx}_{p_idx}"):
                                p1["checked"] = not p1.get("checked", False)
                                save_github_data(FILE_PATH, st.session_state.data_a5, st.session_state.sha_a5)
                                st.rerun()
                            
                            # Ingrédient 2 (colonne droite, si existe)
                            if p_idx + 1 < len(panier):
                                p2 = panier[p_idx + 1]
                                txt2 = f"{p2['nom']} ({p2['qte']})"
                                label2 = f"~~{txt2}~~" if p2.get("checked", False) else txt2
                                if cols_ing[1].button(label2, key=f"vis_{idx}_{p_idx+1}"):
                                    p2["checked"] = not p2.get("checked", False)
                                    save_github_data(FILE_PATH, st.session_state.data_a5, st.session_state.sha_a5)
                                    st.rerun()

    st.divider()
    if st.button("🔄 Rafraîchir", use_container_width=True):
        st.session_state.data_a5, st.session_state.sha_a5 = get_github_data(FILE_PATH)
        st.rerun()
