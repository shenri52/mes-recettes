import streamlit as st
import json
import requests
import base64
import time

def afficher():
    # --- STYLE CSS ---
    st.markdown("""
        <style>
        .block-container { padding-top: 1rem !important; max-width: 800px !important; margin: auto; }
        header { visibility: hidden; } 
        .stButton>button { 
            width: 100%; border-radius: 6px; padding: 2px; height: 2.2em; 
            font-size: 13px; text-align: left; padding-left: 10px;
        }
        /* Style pour le bouton barré */
        .stButton>button p { text-decoration: inherit; } 
        </style>
    """, unsafe_allow_html=True)

    # --- CONFIG GITHUB ---
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
        payload = {"message": "🛒 MàJ Panier", "content": content_encoded, "branch": BRANCH}
        if sha: payload["sha"] = sha
        r = requests.put(url, json=payload, headers=headers)
        if r.status_code in [200, 201]:
            st.session_state.sha_a5 = r.json()['content']['sha']
            return True
        return False

    # --- INITIALISATION ---
    if "data_a5" not in st.session_state:
        st.session_state.data_a5, st.session_state.sha_a5 = get_github_data(FILE_PATH)
        if st.session_state.data_a5 is None:
            st.session_state.data_a5 = {str(i): {"panier": []} for i in range(12)}

    st.subheader("🛒 Mes Courses par Zone")

    # --- GRILLE DES 12 ZONES ---
    for i in range(0, 12, 2):
        cols = st.columns(2)
        for j in range(2):
            idx = str(i + j)
            if idx in st.session_state.data_a5:
                case = st.session_state.data_a5[idx]
                with cols[j]:
                    st.caption(f"📍 Zone {int(idx)+1}")
                    with st.container(border=True):
                        # Affichage des produits existants
                        for p_idx, p in enumerate(case.get("panier", [])):
                            is_checked = p.get("checked", False)
                            # On barre le texte si coché
                            label = f"~~{p['nom']} ({p['qte']})~~" if is_checked else f"{p['nom']} ({p['qte']})"
                            
                            # CLIC SUR LE PRODUIT = BARRAGE + SAVE
                            if st.button(label, key=f"p_{idx}_{p_idx}"):
                                p["checked"] = not is_checked
                                save_github_data(FILE_PATH, st.session_state.data_a5, st.session_state.sha_a5)
                                st.rerun()

    st.divider()

    # --- ACTIONS GLOBALES ---
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔄 Rafraîchir", use_container_width=True):
            st.session_state.data_a5, st.session_state.sha_a5 = get_github_data(FILE_PATH)
            st.rerun()
    with c2:
        if st.button("🗑️ Vider tout", use_container_width=True):
            for k in range(12): st.session_state.data_a5[str(k)]["panier"] = []
            save_github_data(FILE_PATH, st.session_state.data_a5, st.session_state.sha_a5)
            st.rerun()
