import streamlit as st
import json
import requests
import base64
import time

def afficher():
    # --- STYLE CSS (TON ORIGINAL + STYLE ONGLETS) ---
    st.markdown("""
        <style>
        .block-container { padding-top: 1rem !important; max-width: 800px !important; margin: auto; }
        header { visibility: hidden; } 
        .stButton>button { 
            width: 100%; border-radius: 3px; padding: 2px; height: 2.8em; 
            font-size: 14px;
        }
        /* Style pour rendre les onglets plus tactiles sur mobile */
        .stTabs [data-baseweb="tab-list"] { gap: 2px; }
        .stTabs [data-baseweb="tab"] {
            background-color: #f0f2f6; border-radius: 4px 2px 0 0;
            padding: 3px 8px !important; font-size: 14px;
        }
        .stTabs [aria-selected="true"] {
            background-color: #007bff !important; color: white !important;
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

    if "data_a5" not in st.session_state:
        st.session_state.data_a5, st.session_state.sha_a5 = get_github_data(FILE_PATH)
        if st.session_state.data_a5 is None:
            st.session_state.data_a5 = {str(i): {"panier": []} for i in range(12)}

    # --- REMPLACEMENT DES COLONNES PAR DES ONGLETS ---
    onglets = st.tabs([f"{i+1}" for i in range(12)])

    for i in range(12):
        with onglets[i]:
            idx = str(i)
            if idx in st.session_state.data_a5:
                case = st.session_state.data_a5[idx]
                # On garde ton container avec bordure
                with st.container(border=True):
                    panier = case.get("panier", [])
                    if not panier:
                        st.info("Cette zone est vide 🛒")
                    
                    # --- INGRÉDIENTS SUR 2 COLONNES ---
                    for p_idx in range(0, len(panier), 2):
                        sub_cols = st.columns(2)
                        
                        # Ingrédient gauche
                        p1 = panier[p_idx]
                        label1 = f"~~{p1['nom']} ({p1['qte']})~~" if p1.get("checked") else f"{p1['nom']} ({p1['qte']})"
                        if sub_cols[0].button(label1, key=f"vis_{idx}_{p_idx}"):
                            p1["checked"] = not p1.get("checked", False)
                            save_github_data(FILE_PATH, st.session_state.data_a5, st.session_state.sha_a5)
                            st.rerun()
                        
                        # Ingrédient droit
                        if p_idx + 1 < len(panier):
                            p2 = panier[p_idx + 1]
                            label2 = f"~~{p2['nom']} ({p2['qte']})~~" if p2.get("checked") else f"{p2['nom']} ({p2['qte']})"
                            if sub_cols[1].button(label2, key=f"vis_{idx}_{p_idx+1}"):
                                p2["checked"] = not p2.get("checked", False)
                                save_github_data(FILE_PATH, st.session_state.data_a5, st.session_state.sha_a5)
                                st.rerun()

if __name__ == "__main__":
    afficher()
