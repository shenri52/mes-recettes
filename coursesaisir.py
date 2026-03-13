import streamlit as st
import json
import requests
import base64
import time

def afficher():
    # --- STYLE CSS (Pour transformer le texte en "vrais" onglets) ---
    st.markdown("""
        <style>
        .block-container { padding-top: 1rem !important; max-width: 800px !important; margin: auto; }
        header { visibility: hidden; } 
        
        /* Style des boutons de produits */
        .stButton>button { 
            width: 100%; border-radius: 6px; padding: 5px; height: 2.8em; 
            font-size: 14px;
        }
        
        /* Transformation du texte souligné en onglets visuels */
        .stTabs [data-baseweb="tab-list"] {
            gap: 2px;
            border-bottom: none;
        }
        .stTabs [data-baseweb="tab"] {
            background-color: #f0f2f6; /* Fond gris clair */
            border-radius: 4px 4px 0 0;
            padding: 5px 12px !important;
            height: 35px;
            font-size: 12px;
            border: 1px solid #ddd;
        }
        /* Onglet sélectionné */
        .stTabs [aria-selected="true"] {
            background-color: #007bff !important; /* Bleu */
            color: white !important;
            border-color: #0056b3;
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

    if "reset_count" not in st.session_state:
        st.session_state.reset_count = 0

    st.subheader("📝 Préparer les courses")

    # --- LES 12 ONGLETS (Retour à Z1, Z2... avec style bouton) ---
    onglets = st.tabs([f"Z{i+1}" for i in range(12)])

    for i in range(12):
        with onglets[i]: 
            idx_actuelle = str(i)
            case = st.session_state.data_a5[idx_actuelle]
            
            with st.container(border=True):
                key_hist = f"hist_{idx_actuelle}_{st.session_state.reset_count}"
                choix = st.selectbox("Histo", ["---"] + case["catalogue"], key=key_hist, label_visibility="collapsed")
                
                with st.form(key=f"form_{idx_actuelle}_{st.session_state.reset_count}", clear_on_submit=True):
                    nom_initial = "" if choix == "---" else choix
                    nom = st.text_input("Nom", value=nom_initial, placeholder="Produit", label_visibility="collapsed")
                    
                    col_q, col_txt, col_z = st.columns([1, 0.6, 1])
                    qte_f = col_q.text_input("Qté", placeholder="Qté", label_visibility="collapsed")
                    col_txt.markdown("<p style='text-align:center; padding-top:5px;'>Zone :</p>", unsafe_allow_html=True)
                    n_zone = col_z.text_input("Zone", value=str(i+1), label_visibility="collapsed")
                    
                    if st.form_submit_button("➕ AJOUTER", use_container_width=True):
                        final_nom = nom.strip().capitalize()
                        try:
                            num_extrait = "".join(filter(str.isdigit, n_zone))
                            dest_idx = str(int(num_extrait) - 1)
                            if not (0 <= int(dest_idx) <= 11): dest_idx = idx_actuelle
                        except:
                            dest_idx = idx_actuelle

                        if final_nom:
                            st.session_state.reset_count += 1
                            if dest_idx != idx_actuelle and final_nom in case["catalogue"]:
                                case["catalogue"].remove(final_nom)

                            st.session_state.index_zones[final_nom] = dest_idx
                            save_github_data(INDEX_PRODUITS_PATH, st.session_state.index_zones, st.session_state.sha_index)
                            
                            cible = st.session_state.data_a5[dest_idx]
                            trouve = False
                            for p in cible["panier"]:
                                if p["nom"].lower() == final_nom.lower():
                                    p["qte"] = qte_f.strip() or "1"
                                    trouve = True
                                    break
                            if not trouve:
                                cible["panier"].append({"nom": final_nom, "qte": qte_f.strip() or "1", "checked": False})
                            
                            if final_nom not in cible["catalogue"]:
                                cible["catalogue"].append(final_nom)
                                cible["catalogue"].sort()
                            
                            save_github_data(FILE_PATH, st.session_state.data_a5, st.session_state.sha_a5)
                            st.rerun()
                                    
                for p_idx, p in enumerate(case["panier"]):
                    if st.button(f"{p['nom']} ({p['qte']})", key=f"btn_{idx_actuelle}_{p_idx}"):
                        case["panier"].pop(p_idx)
                        save_github_data(FILE_PATH, st.session_state.data_a5, st.session_state.sha_a5)
                        st.rerun()

    if st.button("🗑️ Vider tout le panier", use_container_width=True):
        for k in range(12): 
            st.session_state.data_a5[str(k)]["panier"] = []
        save_github_data(FILE_PATH, st.session_state.data_a5, st.session_state.sha_a5)
        st.rerun()

    st.write("---")
