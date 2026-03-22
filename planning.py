import streamlit as st
import datetime
import json
import time
import requests

from utils import envoyer_donnees_github, charger_json_github, get_github_config
   
# --- APERÇU FICHE RECETTE ---
@st.dialog("Fiche Recette 📖", width="large")
def ouvrir_fiche(nom_plat):
    info = next((r for r in st.session_state.index_complet if r['nom'].upper() == nom_plat.upper()), None)
    
    if info:
        conf = get_github_config()
        url_full = f"https://raw.githubusercontent.com/{conf['owner']}/{conf['repo']}/main/{info['chemin']}"
        res = requests.get(url_full)
        if res.status_code == 200:
            recette = res.json()
            tab1, tab2 = st.tabs(["📝 Détails", "📸 Captures"])
            
            with tab1:
                st.subheader(recette.get('nom', '').upper())
                
                # --- Infos clés (Emojis modifiés pour meilleure compatibilité) ---
                st.write(f"📂 **Catégorie :** {recette.get('categorie', 'Non classé')}")
                st.write(f"🔌 **Appareil :** {recette.get('appareil', 'Aucun')}")
                st.write(f"⏱️ **Temps de préparation :** {recette.get('temps_prep', '0')} min")
                st.write(f"🔥 **Temps de cuisson :** {recette.get('temps_cuisson', '0')} min")
                
                st.divider()
                
                st.markdown("### 🛒 Ingrédients")
                ingredients = recette.get('ingredients', [])
                if ingredients:
                    for i in ingredients:
                        # Nettoyage des textes pour enlever les étoiles et espaces
                        qte = str(i.get('Quantité', '')).replace('*', '').strip()
                        nom = str(i.get('Ingrédient', '')).replace('*', '').strip()
                        
                        if qte and qte.lower() != "none":
                            # Si on a une quantité, on l'affiche devant
                            st.write(f"{qte} {nom}")
                        else:
                            # Si la quantité est vide (ex: épices), on affiche juste l'ingrédient
                            st.write(f"{nom}")
                else:
                    st.write("Aucun ingrédient.")
                
                st.markdown("### 📝 Étapes")
                etapes = recette.get('etapes', '')
                if etapes:
                    st.info(etapes)
                else:
                    st.write("Pas d'instructions saisies.")
                
            with tab2:
                images = recette.get('images', [])
                if images:
                    if "img_idx" not in st.session_state: st.session_state.img_idx = 0
                    img_path = images[st.session_state.img_idx].strip('/')
                    img_url = f"https://raw.githubusercontent.com/{conf['owner']}/{conf['repo']}/main/{img_path}"
                    st.image(img_url, use_container_width=True)
                    if len(images) > 1:
                        c1, c2, c3 = st.columns([1, 2, 1])
                        if c1.button("⬅️", key="btn_prev_img"):
                            st.session_state.img_idx = (st.session_state.img_idx - 1) % len(images)
                            st.rerun()
                        c2.markdown(f"<p style='text-align:center;'>{st.session_state.img_idx + 1} / {len(images)}</p>", unsafe_allow_html=True)
                        if c3.button("➡️", key="btn_next_img"):
                            st.session_state.img_idx = (st.session_state.img_idx + 1) % len(images)
                            st.rerun()
                else:
                    st.info("Aucune photo disponible.")
        else:
            st.error("Erreur de chargement.")

# --- INTERFACE PLANNING ---
def afficher():
    if 'plats_rapides' not in st.session_state:
        st.session_state.plats_rapides = charger_json_github("data/plats_rapides.json") or []
    if 'offset_semaine' not in st.session_state:
        st.session_state.offset_semaine = 0
       
    # 1. On crée une petite fonction de nettoyage (callback)
    def ajouter_et_nettoyer():
        nouveau = st.session_state["input_nouveau_plat"]
        if nouveau and nouveau not in st.session_state.plats_rapides:
            st.session_state.plats_rapides.append(nouveau)
            if envoyer_donnees_github("data/plats_rapides.json", json.dumps(st.session_state.plats_rapides, indent=4, ensure_ascii=False), "⚡ Ajout plat rapide"):
                st.session_state["input_nouveau_plat"] = ""
                
    # Bouton retour
    def aller_accueil():
        st.session_state.page = 'accueil'

    # Bouton retour simplifié
    st.button("⬅️ Retour à l'accueil", use_container_width=True, on_click=aller_accueil)

    st.divider()
    
    if 'index_complet' not in st.session_state:
         st.session_state.index_complet = charger_json_github("data/index_recettes.json") or []
    if 'planning_data' not in st.session_state:
         st.session_state.planning_data = charger_json_github("data/planning.json") or {}

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
            <div style='background:{bg_jour}; padding:10px; border-radius:10px 10px 0 0; border:{border_jour}; border-bottom:none;'>
                <span style='color:#555; font-size:0.8em;'>{nom}</span><br>
                <b style='font-size:1.1em;'>{d_j.strftime('%d/%m/%y')}</b>
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
                            temp[d_str][rep].pop(idx) # On agit directement sur la source
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
       
        if st.button("💾 Enregistrer", use_container_width=True):
            st.session_state.planning_data.update(temp)
            if envoyer_donnees_github("data/planning.json", json.dumps(st.session_state.planning_data, indent=4, ensure_ascii=False), "📅 MAJ Planning"):
                st.success("Planning enregistré ! 💾")
    
    st.subheader("🍴 Plats rapides")
    plats_rapides = sorted(st.session_state.plats_rapides)
    if plats_rapides:
        plat_sel = st.selectbox("Gérer mes plats", ["---"] + plats_rapides, key="sel_rapide_manage")
        if plat_sel != "---":
            c_ren, c_del = st.columns(2)
            
            with c_ren:
                if st.button("📝 Renommer", use_container_width=True):
                    st.session_state.edit_mode = plat_sel 

            with c_del:
                if st.button("🗑️ Supprimer", use_container_width=True):
                    st.session_state.plats_rapides.remove(plat_sel)
                    envoyer_donnees_github("data/plats_rapides.json", json.dumps(st.session_state.plats_rapides, indent=4, ensure_ascii=False), "🗑️ Suppression")
                    st.rerun()

            # --- BLOC RENOMMER  ---
            if st.session_state.get('edit_mode') == plat_sel:
                nouveau_nom = st.text_input("Nouveau nom :", value=plat_sel, key="edit_input")
                if st.button("✅ Valider le changement", use_container_width=True):
                    idx = st.session_state.plats_rapides.index(plat_sel)
                    st.session_state.plats_rapides[idx] = nouveau_nom
                    envoyer_donnees_github("data/plats_rapides.json", json.dumps(st.session_state.plats_rapides, indent=4, ensure_ascii=False), "📝 Plat renommé")
                    st.session_state.edit_mode = None 
                    st.rerun()

    st.divider() 

    # --- BLOC AJOUT ---
    st.text_input("Ajouter un plat rapide", placeholder="Nom du plat...", key="input_nouveau_plat")
    st.button("➕ Ajouter au catalogue", use_container_width=True, on_click=ajouter_et_nettoyer)
