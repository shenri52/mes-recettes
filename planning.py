import streamlit as st
import datetime
import json
import requests
import time
import base64

# --- FONCTIONS TECHNIQUES ---
def config_github():
    """Centralise la configuration pour éviter les répétitions."""
    return {
        "owner": st.secrets["REPO_OWNER"],
        "repo": st.secrets["REPO_NAME"],
        "headers": {
            "Authorization": f"token {st.secrets['GITHUB_TOKEN']}",
            "Accept": "application/vnd.github.v3+json"
        }
    }

def charger_donnees(chemin):
    """Charge les données avec un paramètre anti-cache (?t=) pour avoir le réel en direct."""
    conf = config_github()
    # Le timestamp force GitHub à donner la version la plus récente
    url = f"https://raw.githubusercontent.com/{conf['owner']}/{conf['repo']}/main/{chemin}?t={int(time.time())}"
    try:
        res = requests.get(url)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    # Retourne une liste vide pour les plats rapides, sinon un dictionnaire vide
    return [] if "plats_rapides" in chemin else {}

def sauvegarder_github(chemin, contenu_dict_ou_liste):
    """Sauvegarde les données proprement en gérant le SHA (versioning) de GitHub."""
    conf = config_github()
    url = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/{chemin}"
    
    # 1. Récupération du SHA actuel pour avoir le droit de modifier le fichier
    res_get = requests.get(url, headers=conf['headers'])
    sha = res_get.json().get('sha') if res_get.status_code == 200 else None
    
    # 2. Préparation du contenu
    contenu_json = json.dumps(contenu_dict_ou_liste, indent=4, ensure_ascii=False)
    contenu_b64 = base64.b64encode(contenu_json.encode('utf-8')).decode('utf-8')
    
    # 3. Envoi de la mise à jour
    payload = {
        "message": f"MAJ automatique : {chemin}",
        "content": contenu_b64,
        "branch": "main"
    }
    if sha: payload["sha"] = sha
    
    r = requests.put(url, headers=conf['headers'], json=payload)
    return r.status_code in [200, 201]
   
# --- APERÇU FICHE RECETTE ---
@st.dialog("Fiche Recette 📖", width="large")
def ouvrir_fiche(nom_plat):
    info = next((r for r in st.session_state.index_complet if r['nom'].upper() == nom_plat.upper()), None)
    
    if info:
        url_full = f"https://raw.githubusercontent.com/{config_github()['owner']}/{config_github()['repo']}/main/{info['chemin']}"
        res = requests.get(url_full)
        if res.status_code == 200:
            recette = res.json()
            tab1, tab2 = st.tabs(["📝 Détails", "📸 Captures"])
            
            with tab1:
                st.subheader(recette.get('nom', '').upper())
                st.write(f"**Appareil :** {recette.get('appareil', 'Aucun')}")
                st.write("**Ingrédients :**")
                for i in recette.get('ingredients', []):
                    st.write(f"- {i.get('Quantité', '')} {i.get('Ingrédient', '')}")
                
            with tab2:
                images = recette.get('images', [])
                if images:
                    if "img_idx" not in st.session_state: st.session_state.img_idx = 0
                    img_url = f"https://raw.githubusercontent.com/{config_github()['owner']}/{config_github()['repo']}/main/{images[st.session_state.img_idx].strip('/')}"
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
    # 1. On crée une petite fonction de nettoyage (callback)
    def ajouter_et_nettoyer():
        nouveau = st.session_state["input_nouveau_plat"]
        if nouveau and nouveau not in st.session_state.plats_rapides:
            st.session_state.plats_rapides.append(nouveau)
            if sauvegarder_github("data/plats_rapides.json", st.session_state.plats_rapides):
                # C'est ici qu'on vide le champ SANS erreur
                st.session_state["input_nouveau_plat"] = ""
                st.toast(f"'{nouveau}' ajouté ! ✅") # Petit message discret
            
    # Bouton retour seul
    if st.button("⬅️ Retour à l'accueil", use_container_width=True):
        st.session_state.page = 'accueil'
        st.rerun()
        
    st.header("📅 Mon planning")
    
    if 'index_complet' not in st.session_state: st.session_state.index_complet = charger_donnees("data/index_recettes.json")
    if 'planning_data' not in st.session_state: st.session_state.planning_data = charger_donnees("data/planning.json")
    if 'plats_rapides' not in st.session_state: st.session_state.plats_rapides = charger_donnees("data/plats_rapides.json")
    if 'offset_semaine' not in st.session_state: st.session_state.offset_semaine = 0

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
    
    st.divider()

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
                            plats.pop(idx)
                            temp[d_str][rep] = plats
                            st.session_state.planning_data.update(temp)
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
        # On enregistre la totalité des données sans filtre de date
        if sauvegarder_github("data/planning.json", st.session_state.planning_data):
            st.success("Planning enregistré ! 💾")
            time.sleep(1)
            st.rerun()
            
    st.divider()
    
    st.subheader("🍴 Plats rapides")
    plats_rapides = sorted(st.session_state.plats_rapides)
    if plats_rapides:
        plat_sel = st.selectbox("Gérer mes plats", ["---"] + plats_rapides, key="sel_rapide_manage")
        if plat_sel != "---":
            if c_del.button("🗑️ Supprimer", use_container_width=True):
                st.session_state.plats_rapides.remove(plat_sel)
                sauvegarder_github("data/plats_rapides.json", st.session_state.plats_rapides)
                st.rerun()
   
    # 2. Le champ de saisie reste le même
    st.text_input("Ajouter un plat rapide", placeholder="Nom du plat...", key="input_nouveau_plat")
    
    # 3. Le bouton appelle la fonction ci-dessus
    if st.button("➕", use_container_width=True, on_click=ajouter_et_nettoyer):
        st.rerun()
