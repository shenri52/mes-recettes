import streamlit as st
import json
import requests
import base64

def afficher():
    # --- STYLE CSS ---
    st.markdown("""
        <style>
        .block-container { padding-top: 1rem !important; max-width: 800px !important; margin: 4rem; }
        header { visibility: hidden; } 
        .stButton>button { 
            width: 100%; border-radius: 6px; padding: 5px; height: 2.8em; 
            border: 1px solid #ddd; font-size: 14px;
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

    if "data_a5" not in st.session_state:
        st.session_state.data_a5, st.session_state.sha_a5 = get_data()

    # --- GRILLE DES 12 CASES (EXPANDERS) ---
    for i in range(0, 12, 2):
        cols = st.columns(2)
        for j in range(2):
            idx = str(i + j)
            if idx in st.session_state.data_a5:
                case = st.session_state.data_a5[idx]
                with cols[j]:
                    # Utilisation de l'Expander pour le côté "carré déroulant"
                    with st.expander(f"**Rayon {int(idx)+1}**", expanded=False):
                        
                        # Formulaire pour l'ajout avec Reset automatique
                        with st.form(key=f"form_{idx}", clear_on_submit=True):
                            choix = st.selectbox("Histo", ["-- Nouveau --"] + case["catalogue"], label_visibility="collapsed")
                            nom = st.text_input("Nom", placeholder="Produit", label_visibility="collapsed")
                            qte = st.text_input("Qté", placeholder="Qté", label_visibility="collapsed")
                            
                            if st.form_submit_button("Ajouter", use_container_width=True):
                                final_nom = nom.strip() if choix == "-- Nouveau --" else choix
                                if final_nom:
                                    case["panier"].append({"nom": final_nom, "qte": qte.strip() or "1"})
                                    if final_nom not in case["catalogue"]:
                                        case["catalogue"].append(final_nom)
                                        case["catalogue"].sort()
                                    save_data(st.session_state.data_a5, st.session_state.sha_a5)
                                    st.rerun()

                        st.divider()

                        # Affichage de la liste actuelle dans le rayon
                        for p_idx, p in enumerate(case["panier"]):
                            if st.button(f"{p['nom']} ({p['qte']})", key=f"btn_{idx}_{p_idx}"):
                                case["panier"].pop(p_idx)
                                save_data(st.session_state.data_a5, st.session_state.sha_a5)
                                st.rerun()

    st.divider()

    # --- BOUTONS DE NAVIGATION ---
    c_ref, c_res = st.columns(2)
    with c_ref:
        if st.button("🔄 Rafraîchir", use_container_width=True):
            st.session_state.data_a5, st.session_state.sha_a5 = get_data()
            st.rerun()
    with c_res:
        if st.button("🗑️ Vider le panier", use_container_width=True):
            for k in range(12): st.session_state.data_a5[str(k)]["panier"] = []
            save_data(st.session_state.data_a5, st.session_state.sha_a5)
            st.rerun()
