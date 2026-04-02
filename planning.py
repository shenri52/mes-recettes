import streamlit as st
import datetime, json, requests, time
from utils import config_github, envoyer_vers_github, charger_donnees, ouvrir_fiche

# --- INTERFACE PLANNING ---
def afficher():

    def ajouter_et_nettoyer():
        nouveau = st.session_state["input_nouveau_plat"]
        if nouveau and nouveau not in st.session_state.plats_rapides:
            st.session_state.plats_rapides.append(nouveau)
            if envoyer_vers_github("data/plats_rapides.json", json.dumps(st.session_state.plats_rapides, indent=4, ensure_ascii=False), "Ajout plat rapide"):
                st.session_state["input_nouveau_plat"] = ""
                st.toast(f"'{nouveau}' ajouté ! ✅")
                st.rerun()
                
    # Bouton retour
    def aller_accueil():
        st.session_state.page = 'accueil'

    # Bouton retour simplifié
    st.button("⬅️ Retour à l'accueil", use_container_width=True, on_click=aller_accueil)
    
    for key, default in {
        'index_complet': charger_donnees("data/index_recettes.json"),
        'planning_data': charger_donnees("data/planning.json"),
        'plats_rapides': charger_donnees("data/plats_rapides.json"),
        'offset_semaine': 0
    }.items():
        if key not in st.session_state: st.session_state[key] = default

    noms_recettes = [r['nom'] for r in st.session_state.index_complet]
    options = ["---"] + sorted(noms_recettes + st.session_state.plats_rapides)

    aujourdhui = datetime.date.today()
    debut = (aujourdhui - datetime.timedelta(days=(aujourdhui.weekday() - 4) % 7)) + datetime.timedelta(weeks=st.session_state.offset_semaine)
    fin = debut + datetime.timedelta(days=6)
    date_range_str = f"{debut.strftime('%d/%m/%y')} au {fin.strftime('%d/%m/%y')}"

    # Navigation semaines
    c1, c2, c3 = st.columns([1, 3, 1])
    with c1:
        if st.button("⬅️", key="prev_sem", use_container_width=True): 
            st.session_state.offset_semaine -= 1
            st.rerun()
    with c2:
        if st.button(f"Du {date_range_str}", key="reset_sem", use_container_width=True):
            st.session_state.offset_semaine = 0
            st.rerun()
    with c3:
        if st.button("➡️", key="next_sem", use_container_width=True):
            st.session_state.offset_semaine += 1
            st.rerun()

    jours = ["Vendredi", "Samedi", "Dimanche", "Lundi", "Mardi", "Mercredi", "Jeudi"]
    temp = st.session_state.planning_data.copy()

    for i, nom in enumerate(jours):
        d_j = debut + datetime.timedelta(days=i)
        d_str = d_j.isoformat()
        
        if d_str not in temp: 
            temp[d_str] = {"midi": [], "soir": []}

        is_today = (d_j == aujourdhui)
        bg_jour = "#e1f5fe" if is_today else "#f8f9fa"
        border_jour = "2px solid #0288d1" if is_today else "1px solid #eee"
        
        st.markdown(f"""
            <div style='
                background:{bg_jour}; 
                padding:10px; 
                border-radius:10px 10px 0 0; 
                border:{border_jour}; 
                border-bottom:none;
                display: flex; 
                justify-content: space-between; 
                align-items: center;
            '>
                <span style='color:#555; font-size:0.9em; font-weight: bold; text-transform: uppercase;'>{nom}</span>
                <span style='font-size:1.0em; font-weight: bold; color: #333;'>{d_j.strftime('%d/%m/%y')}</span>
            </div>
        """, unsafe_allow_html=True)

        col_m, col_s = st.columns(2)
        
        for rep, col in zip(["midi", "soir"], [col_m, col_s]):
            with col:
                bg_rep = "#ffe0b2" if rep == "midi" else "#c5cae9"
                txt_rep = "#e65100" if rep == "midi" else "#1a237e"
                st.markdown(f"""
                    <div style='background:{bg_rep}; color:{txt_rep}; padding:2px; border-radius:5px; font-size:0.7em; font-weight:bold; margin-bottom:5px; text-transform:uppercase; text-align:center;'>
                        {rep}
                    </div>
                """, unsafe_allow_html=True)

                plats = temp[d_str].get(rep, [])
                if isinstance(plats, dict): plats = [] 
                
                for idx, p_nom in enumerate(plats):
                    est_recette = any(r['nom'].upper() == p_nom.upper() for r in st.session_state.index_complet)
                    icon = "📖" if est_recette else "⚡"
                    
                    c_txt, c_eye = st.columns([4, 1])
                    with c_txt:
                        if st.button(f"{icon} {p_nom}", key=f"del_{d_str}{rep}{idx}", use_container_width=True):
                            temp[d_str][rep].pop(idx) 
                            st.rerun()
                    with c_eye:
                        if est_recette:
                            if st.button("👁️", key=f"view_{d_str}{rep}{idx}", use_container_width=True):
                                st.session_state.img_idx = 0
                                ouvrir_fiche(p_nom)
                
                if len(plats) < 3:
                    with st.popover("➕", use_container_width=True):
                        choix = st.selectbox("Choisir", options, index=0, key=f"sel_{d_str}{rep}{len(plats)}")
                        if choix != "---":
                            plats.append(choix)
                            temp[d_str][rep] = plats
                            st.session_state.planning_data.update(temp)
                            st.rerun()
        
        st.markdown("<div style='margin-bottom:15px;'></div>", unsafe_allow_html=True)
        
    st.divider()
       
    if st.button("💾 Enregistrer", use_container_width=True):
        st.session_state.planning_data.update(temp)
        # On enregistre avec json.dumps pour éviter l'erreur d'encodage
        if envoyer_vers_github("data/planning.json", json.dumps(st.session_state.planning_data, indent=4, ensure_ascii=False), "MAJ Planning"):
            st.success("Planning enregistré ! 💾")
            time.sleep(1)
            st.rerun()
    
    st.subheader("🍴 Plats rapides")
    plats_rapides = sorted(st.session_state.plats_rapides)
    if plats_rapides:
        plat_sel = st.selectbox("Gérer mes plats", ["---"] + plats_rapides, key="sel_rapide_manage")
        if plat_sel != "---":
            c_ren, c_del = st.columns(2)
            if c_del.button("🗑️ Supprimer", use_container_width=True):
                st.session_state.plats_rapides.remove(plat_sel)
                envoyer_vers_github("data/plats_rapides.json", json.dumps(st.session_state.plats_rapides, indent=4, ensure_ascii=False), "Suppression plat rapide")
                st.rerun()
  
    st.text_input("Ajouter un plat rapide", placeholder="Nom du plat...", key="input_nouveau_plat")
    st.button("➕", use_container_width=True, on_click=ajouter_et_nettoyer)
