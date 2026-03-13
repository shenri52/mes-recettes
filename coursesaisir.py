import streamlit as st
import json
import requests
import base64
import time

def afficher():
    # --- STYLE CSS OPTIMISÉ MOBILE (FORCE LIGNES) ---
    st.markdown("""
        <style>
        .block-container { padding: 0.5rem !important; max-width: 100% !important; }
        header { visibility: hidden; } 
        
        /* FORCE LES COLONNES À RESTER EN LIGNE SUR MOBILE */
        [data-testid="column"] {
            width: calc(33% - 1rem) !important;
            flex: 1 1 calc(33% - 1rem) !important;
            min-width: 0px !important;
        }

        /* Ajustement spécifique pour les formulaires */
        .stButton>button { 
            width: 100%; border-radius: 8px; height: 3em; 
            font-size: 15px !important;
        }
        
        div[data-testid="stTextInput"] input { 
            font-size: 16px !important; 
            padding: 5px !important;
        }

        .label-mini { 
            text-align: center; margin-top: 10px; 
            font-size: 11px; color: #666; white-space: nowrap;
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

    for i in range(0, 12, 2):
        cols = st.columns(2)
        for j in range(2):
            idx_actuelle = str(i + j)
            case = st.session_state.data_a5[idx_actuelle]
            with cols[j]:
                st.caption(f"📍 Zone {int(idx_actuelle)+1}")
                with st.container(border=True):
                    key_hist = f"hist_{idx_actuelle}_{st.session_state.reset_count}"
                    choix = st.selectbox("Histo", ["---"] + case["catalogue"], key=key_hist, label_visibility="collapsed")
                    
                    with st.form(key=f"form_{idx_actuelle}_{st.session_state.reset_count}", clear_on_submit=True):
                        nom_initial = "" if choix == "---" else choix
                        nom = st.text_input("Produit", value=nom_initial, placeholder="Nom", label_visibility="collapsed")
                        
                        # Ici on définit les colonnes pour la ligne Quantité/Zone
                        col_q, col_txt, col_z = st.columns([1, 0.8, 1])
                        qte_f = col_q.text_input("Qté", placeholder="1", label_visibility="collapsed")
                        col_txt.markdown("<p class='label-mini'>ZONE</p>", unsafe_allow_html=True)
                        n_zone = col_z.text_input("Z", value=str(int(idx_actuelle)+1), label_visibility="collapsed")
                        
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
                        if st.button(f"🗑️ {p['nom']} ({p['qte']})", key=f"btn_{idx_actuelle}_{p_idx}"):
                            case["panier"].pop(p_idx)
                            save_github_data(FILE_PATH, st.session_state.data_a5, st.session_state.sha_a5)
                            st.rerun()

    st.divider()
    if st.button("🗑️ VIDER TOUT LE PANIER", use_container_width=True):
        for k in range(12): 
            st.session_state.data_a5[str(k)]["panier"] = []
        save_github_data(FILE_PATH, st.session_state.data_a5, st.session_state.sha_a5)
        st.rerun()
