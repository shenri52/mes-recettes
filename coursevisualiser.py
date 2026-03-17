import streamlit as st
import json, requests, base64, time

def config():
    return {"headers": {"Authorization": f"token {st.secrets['GITHUB_TOKEN']}"},
            "url": f"https://api.github.com/repos/{st.secrets['REPO_OWNER']}/{st.secrets['REPO_NAME']}/contents/courses/index_courses.json"}

def get_data():
    conf = config()
    # On ajoute ?t= + l'heure en secondes pour "casser" le cache
    t = int(time.time())
    r = requests.get(f"{conf['url']}?t={t}", headers=conf['headers'])
    if r.status_code == 200:
        res = r.json()
        return json.loads(base64.b64decode(res['content'])), res.get('sha')
    return {str(i): {"panier": []} for i in range(12)}, None

def save_data(data, sha):
    conf = config()
    payload = {"message": "🛒 Update", "content": base64.b64encode(json.dumps(data, indent=2, ensure_ascii=False).encode()).decode(), "sha": sha}
    r = requests.put(conf['url'], json=payload, headers=conf['headers'])
    if r.ok: st.session_state.sha_a5 = r.json()['content']['sha']
    return r.ok

def afficher():
    st.markdown("""<style>
        .block-container { padding-top: 1rem !important; max-width: 800px !important; }
        header { visibility: hidden; }
        .stButton>button { width: 100%; border: 1px solid #ddd; border-radius: 4px 3px 0 0; padding: 4px 6px !important; font-size: 14px; height: 2.8em; gap: 2px;}
        .stTabs [data-baseweb="tab"] { background-color: #f0f2f6; border: 2px solid #ddd; height: 35px; color: black !important; }
        .stTabs [aria-selected="true"] { background-color: #87CEEB !important; color: white !important; }
        .stTabs [data-baseweb="tab"] p { color: black !important; font-weight: bold; } /* Force le texte en noir */
    </style>""", unsafe_allow_html=True)

    if "index_courses" not in st.session_state:
        st.session_state.index_courses, st.session_state.sha_a5 = get_data()

    data = st.session_state.index_courses
    # --- FILTRE : On ne garde que les zones qui ont des produits ---
    zones_actives = [i for i in range(12) if data.get(str(i), {}).get("panier")]

    if not zones_actives:
        st.info("Tous les paniers sont vides.")
        return

    # Création des onglets uniquement pour les zones avec produits
    tabs = st.tabs([f"{i+1}" for i in zones_actives])

    for idx_tab, zone_idx in enumerate(zones_actives):
        with tabs[idx_tab]:
            case = data[str(zone_idx)]
            with st.container(border=True):
                panier = case["panier"]
                for p_idx in range(0, len(panier), 2):
                    cols = st.columns(2)
                    for j in range(2):
                        if p_idx + j < len(panier):
                            p = panier[p_idx + j]
                            lab = f"~~{p['nom']} ({p['qte']})~~" if p.get("checked") else f"{p['nom']} ({p['qte']})"
                            if cols[j].button(lab, key=f"btn_{zone_idx}_{p_idx+j}"):
                                p["checked"] = not p.get("checked", False)
                                if save_data(data, st.session_state.sha_a5): st.rerun()

if __name__ == "__main__":
    afficher()
