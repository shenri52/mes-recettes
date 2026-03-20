import streamlit as st
import json

from utils import envoyer_donnees_github, charger_json_github 

def afficher():
    st.markdown("""<style>
            .block-container { padding-top: 1rem !important; max-width: 800px !important; }
            header { visibility: hidden; }
            .stButton>button { width: 100%; border-radius: 3px; font-size: 14px; height: 2.8em; }
    
            /* RÉDUIRE L'ESPACE ENTRE LES ONGLETS */
            .stTabs [data-baseweb="tab-list"] { gap: 2px !important; } 
    
            /* LARGEUR ET STYLE DES ONGLETS */
            .stTabs [data-baseweb="tab"] { 
                background-color: #f0f2f6; 
                border: 1px solid #ddd; 
                border-radius: 3px 3px 0 0; 
                padding: 3px 6px !important; /* Augmente 20px pour plus de largeur */
                height: 30px;
            }
    
            /* TEXTE NOIR ET GRAS */
            .stTabs [data-baseweb="tab"] p { 
                color: black !important; 
                font-weight: bold !important; 
            }
    
            /* BLEU CLAIR ACTIF */
            .stTabs [aria-selected="true"] { background-color: #87CEEB !important; }
        </style>""", unsafe_allow_html=True)

    if "courses_data" not in st.session_state:
        st.session_state.courses_data = charger_json_github("data/index_courses.json")
        if not st.session_state.courses_data:
            st.session_state.courses_data = {str(i): {"panier": []} for i in range(12)}

    data = st.session_state.courses_data
  
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
                                json_a_envoyer = json.dumps(data, indent=4, ensure_ascii=False)
                                if envoyer_donnees_github("data/index_courses.json", json_a_envoyer, f"🛒 Check {p['nom']}"):
                                    st.rerun()

if __name__ == "__main__":
    afficher()
