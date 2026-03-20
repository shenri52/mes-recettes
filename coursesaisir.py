import streamlit as st
import json
import time 

from utils import envoyer_donnees_github, charger_json_github

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
            border-radius: 4px 3px 0 0;
            padding: 4px 6px !important;
            height: 30px;
            font-size: 11px;
            border: 2px solid #ddd;
        }
        /* Onglet sélectionné */
        .stTabs [aria-selected="true"] {
            background-color: #87CEEB !important; /* Bleu */
            color: white !important;
            border-color: #0056b3;
        }
        
        /* TEXTE NOIR ET GRAS */
        .stTabs [data-baseweb="tab"] p { 
            color: black !important; 
            font-weight: bold !important; 
        }
        </style>
    """, unsafe_allow_html=True)

    FILE_PATH = "data/index_courses.json"
    INDEX_PRODUITS_PATH = "data/index_produits_zones.json"

    # Chargement du panier (index_courses)
    if "index_courses" not in st.session_state:
        data_load = charger_json_github("data/index_courses.json")
        # On transforme la liste [] de utils en dictionnaire de base 
        if not data_load or isinstance(data_load, list):
            st.session_state.index_courses = {str(i): {"panier": [], "catalogue": []} for i in range(12)}
        else:
            st.session_state.index_courses = data_load

    # Chargement de l'index des zones
    if "index_zones" not in st.session_state:
        zones_load = charger_json_github("data/index_produits_zones.json")
        # On transforme la liste [] de utils en dictionnaire vide {} 
        st.session_state.index_zones = zones_load if isinstance(zones_load, dict) else {}

    if "reset_count" not in st.session_state:
        st.session_state.reset_count = 0

    st.subheader("📝 Préparer les courses")

    # --- LES 12 ONGLETS (Retour à Z1, Z2... avec style bouton) ---
    onglets = st.tabs([f"{i+1}" for i in range(12)])

    for i in range(12):
        with onglets[i]: 
            idx_actuelle = str(i)
            case = st.session_state.index_courses[idx_actuelle]
            
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
                            
                            # 1. Gestion du catalogue (déplacement si nécessaire)
                            if dest_idx != idx_actuelle and final_nom in case["catalogue"]:
                                case["catalogue"].remove(final_nom)

                            # 2. Mise à jour de l'index des zones
                            st.session_state.index_zones[final_nom] = dest_idx
                            
                            # 3. Logique d'ajout au panier (L'OUBLI EST ICI ⬇️)
                            cible = st.session_state.index_courses[dest_idx]
                            trouve = False
                            for p in cible["panier"]:
                                if p["nom"].lower() == final_nom.lower():
                                    p["qte"] = qte_f.strip() or "1"
                                    trouve = True
                                    break
                            if not trouve:
                                cible["panier"].append({"nom": final_nom, "qte": qte_f.strip() or "1", "checked": False})
                            
                            # 4. Ajout au catalogue de la zone cible
                            if final_nom not in cible["catalogue"]:
                                cible["catalogue"].append(final_nom)
                                cible["catalogue"].sort()

                            # 5. SAUVEGARDE DOUBLE (Zones + Panier) 🚀
                            envoyer_donnees_github("data/index_produits_zones.json", json.dumps(st.session_state.index_zones, indent=4, ensure_ascii=False), "🔄 MAJ Zones")
                            envoyer_donnees_github("data/index_courses.json", json.dumps(st.session_state.index_courses, indent=4, ensure_ascii=False), "🔄 MAJ Panier")
                            
                            st.rerun()
                          
                  for p_idx, p in enumerate(case["panier"]):
                      if st.button(f"{p['nom']} ({p['qte']})", key=f"btn_{idx_actuelle}_{p_idx}"):
                          case["panier"].pop(p_idx)
                          envoyer_donnees_github("data/index_courses.json", json.dumps(st.session_state.index_courses, indent=4, ensure_ascii=False), "🗑️ Suppr article")
                          st.rerun()

    if st.button("🗑️ Vider tout le panier", use_container_width=True):
        for k in range(12): 
            st.session_state.index_courses[str(k)]["panier"] = []
        envoyer_donnees_github("data/index_courses.json", json.dumps(st.session_state.index_courses, indent=4, ensure_ascii=False), "🧹 Vidage panier")
        st.rerun()
