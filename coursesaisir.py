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
            width: 100%; border-radius: 6px; padding: 5px; height: 2.8em; 
            font-size: 14px;
        }
        div[data-testid="stTextInput"] input { padding: 5px; height: 2.2em; }
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

    # --- INITIALISATION ---
    if "data_a5" not in st.session_state:
        st.session_state.data_a5, st.session_state.sha_a5 = get_github_data(FILE_PATH)
        if st.session_state.data_a5 is None:
            st.session_state.data_a5 = {str(i): {"panier": [], "catalogue": []} for i in range(12)}

    if "index_zones" not in st.session_state:
        st.session_state.index_zones, st.session_state.sha_index = get_github_data(INDEX_PRODUITS_PATH)
        if st.session_state.index_zones is None: st.session_state.index_zones = {}

    st.subheader("📝 Préparer les courses")

    # --- AFFICHAGE DES 12 ZONES ---
    for i in range(0, 12, 2):
        cols = st.columns(2)
        for j in range(2):
            idx = str(i + j)
            case = st.session_state.data_a5[idx]
            with cols[j]:
                st.caption(f"Zone {int(idx)+1}")
                with st.container(border=True):
                    # Formulaire d'ajout : rien ne se passe avant le clic sur "+"
                    with st.form(key=f"form_{idx}", clear_on_submit=True):
                        choix = st.selectbox("Histo", ["-- Nouveau --"] + case["catalogue"], label_visibility="collapsed")
                        nom = st.text_input("Nom", placeholder="Produit", label_visibility="collapsed")
                        qte_f = st.text_input("Qté", placeholder="Qté", label_visibility="collapsed")
                        
                        # Transformation du bouton en "+"
                        if st.form_submit_button("+", use_container_width=True):
                            final_nom = nom.strip().capitalize() if choix == "-- Nouveau --" else choix
                            if final_nom:
                                st.session_state.index_zones[final_nom] = idx
                                save_github_data(INDEX_PRODUITS_PATH, st.session_state.index_zones, st.session_state.sha_index)
                                
                                trouve = False
                                for p in case["panier"]:
                                    if p["nom"].lower() == final_nom.lower():
                                        p["qte"] = qte_f.strip() or "1"
                                        trouve = True
                                        break
                                if not trouve:
                                    case["panier"].append({"nom": final_nom, "qte": qte_f.strip() or "1", "checked": False})
                                
                                if final_nom not in case["catalogue"]:
                                    case["catalogue"].append(final_nom)
                                    case["catalogue"].sort()
                                
                                save_github_data(FILE_PATH, st.session_state.data_a5, st.session_state.sha_a5)
                                st.rerun()
                                    
                    # Liste des produits cliquables pour suppression
                    for p_idx, p in enumerate(case["panier"]):
                        if st.button(f"{p['nom']} ({p['qte']})", key=f"btn_{idx}_{p_idx}"):
                            case["panier"].pop(p_idx)
                            save_github_data(FILE_PATH, st.session_state.data_a5, st.session_state.sha_a5)
                            st.rerun()

    st.divider()
    if st.button("🗑️ Vider tout le panier", use_container_width=True):
        for k in range(12): 
            st.session_state.data_a5[str(k)]["panier"] = []
        save_github_data(FILE_PATH, st.session_state.data_a5, st.session_state.sha_a5)
        st.rerun()
