import streamlit as st
import datetime
import json
import requests
import time
import base64

# --- FONCTIONS TECHNIQUES ---
def config_github():
    return {
        "token": st.secrets["GITHUB_TOKEN"],
        "owner": st.secrets["REPO_OWNER"],
        "repo": st.secrets["REPO_NAME"],
        "headers": {"Authorization": f"token {st.secrets['GITHUB_TOKEN']}", "Accept": "application/vnd.github.v3+json"}
    }

def charger_donnees(chemin):
    conf = config_github()
    url = f"https://raw.githubusercontent.com/{conf['owner']}/{conf['repo']}/main/{chemin}?t={int(time.time())}"
    res = requests.get(url)
    if res.status_code == 200:
        return res.json()
    return [] if "plats_rapides" in chemin else {}

def sauvegarder_github(chemin, contenu_dict_ou_liste):
    conf = config_github()
    url = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/{chemin}"
    res_get = requests.get(url, headers=conf['headers'])
    sha = res_get.json().get('sha') if res_get.status_code == 200 else None
    contenu_json = json.dumps(contenu_dict_ou_liste, indent=4, ensure_ascii=False)
    contenu_b64 = base64.b64encode(contenu_json.encode('utf-8')).decode('utf-8')
    data = {"message": f"MAJ {chemin}", "content": contenu_b64, "branch": "main"}
    if sha: data["sha"] = sha
    return requests.put(url, headers=conf['headers'], json=data).status_code in [200, 201]

# --- NOUVELLE FONCTION : APERÇU RECETTE AMÉLIORÉ ---
@st.dialog("Fiche Recette 📖")
def ouvrir_fiche(nom_plat):
    recette = next((r for r in st.session_state.index_complet if r['nom'] == nom_plat), None)
    
    if recette:
        st.subheader(recette['nom'])
        
        # 1. Affichage des Ingrédients et Quantités
        if 'ingredients' in recette:
            st.write("**Ingrédients :**")
            for ing in recette['ingredients']:
                # Gestion dynamique : affiche quantité si présente, sinon juste l'ingrédient
                qte = recette.get('quantites', {}).get(ing, "")
                txt = f"- {ing} : **{qte}**" if qte else f"- {ing}"
                st.write(txt)
        
        # 2. Affichage des Instructions
        if 'instructions' in recette and recette['instructions']:
            st.write("**Préparation :**")
            st.info(recette['instructions'])
        
        # 3. Affichage des Captures d'écran (Images)
        st.write("**Captures d'écran :**")
        conf = config_github()
        # On tente de charger l'image depuis le dossier captures/Nom_du_plat.png
        img_url = f"https://raw.githubusercontent.com/{conf['owner']}/{conf['repo']}/main/captures/{nom_plat.replace(' ', '%20')}.png"
        
        # Vérification si l'image existe
        res = requests.head(img_url)
        if res.status_code == 200:
            st.image(img_url, use_container_width=True)
        else:
            st.caption("Aucune capture d'écran disponible pour ce plat.")
    else:
        st.error("Détails de la recette introuvables.")

# --- INTERFACE PLANNING ---
def afficher():
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
    
    st.write("") 
    c_head_label, c_head_m, c_head_s = st.columns([1.2, 2, 2])
    with c_head_m: st.markdown("<p style='text-align:center; font-weight:bold; margin-bottom:0;'>Midi</p>", unsafe_allow_html=True)
    with c_head_s: st.markdown("<p style='text-align:center; font-weight:bold; margin-bottom:0;'>Soir</p>", unsafe_allow_html=True)
    st.divider()

    for i, nom in enumerate(jours):
        d_j = debut + datetime.timedelta(days=i)
        d_str = d_j.isoformat()
        
        if d_str not in temp: 
            temp[d_str] = {"midi": [], "soir": []}

        col_d, col_m, col_s = st.columns([1.2, 2, 2])
        
        is_today = (d_j == aujourdhui)
        bg = "#e1f5fe" if is_today else "transparent"
        border = "2px solid #0288d1" if is_today else "1px solid #ddd"
        text_color = "#01579b" if is_today else "inherit"
        
        col_d.markdown(f"""
            <div style='background:{bg}; color:{text_color}; padding:10px; border-radius:5px; border:{border}; min-height:102px; display:flex; flex-direction:column; justify-content:center;'>
                <small style='font-weight:normal;'>{nom}</small><br><b style='font-size:1.1em;'>{d_j.strftime('%d/%m/%y')}</b>
            </div>
        """, unsafe_allow_html=True)

        for rep, col in zip(["midi", "soir"], [col_m, col_s]):
            with col:
                plats = temp[d_str].get(rep, [])
                if isinstance(plats, dict): plats = [] 
                
                for idx, p_nom in enumerate(plats):
                    est_recette = any(r['nom'] == p_nom for r in st.session_state.index_complet)
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
                                ouvrir_fiche(p_nom)
                
                if len(plats) < 3:
                    with st.popover("➕ Ajouter", use_container_width=True):
                        choix = st.selectbox("Choisir", options, index=0, key=f"sel_{d_str}{rep}{len(plats)}")
                        if choix != "---":
                            plats.append(choix)
                            temp[d_str][rep] = plats
                            st.session_state.planning_data.update(temp)
                            st.rerun()

    st.divider()
    st.subheader("🍴 Mes plats rapides (sans recette)")
    
    plats_rapides = sorted(st.session_state.plats_rapides)
    if plats_rapides:
        col_sel, col_ren, col_btn_ren, col_btn_del = st.columns([1.5, 1.5, 1, 1])
        with col_sel:
            plat_sel = st.selectbox("Plats enregistrés", ["---"] + plats_rapides, key="sel_rapide_manage", label_visibility="collapsed")
        
        if plat_sel != "---":
            with col_ren:
                nouveau_nom = st.text_input("Nouveau nom", value=plat_sel, key="rename_plat", label_visibility="collapsed")
            with col_btn_ren:
                if st.button("📝 OK", key="btn_rename", use_container_width=True):
                    if nouveau_nom and nouveau_nom != plat_sel:
                        st.session_state.plats_rapides.remove(plat_sel)
                        st.session_state.plats_rapides.append(nouveau_nom)
                        sauvegarder_github("data/plats_rapides.json", st.session_state.plats_rapides)
                        st.rerun()
            with col_btn_del:
                if st.button("🗑️ Suppr", key="btn_del_rapide", use_container_width=True):
                    st.session_state.plats_rapides.remove(plat_sel)
                    sauvegarder_github("data/plats_rapides.json", st.session_state.plats_rapides)
                    st.rerun()

    col_add_txt, col_add_btn = st.columns([3, 1])
    with col_add_txt:
        nouveau_plat = st.text_input("Nom du nouveau plat", placeholder="Ajouter un plat...", key="input_new_plat", label_visibility="collapsed")
    with col_add_btn:
        if st.button("➕ Ajouter", key="btn_add_rapide", use_container_width=True) and nouveau_plat:
            if nouveau_plat not in st.session_state.plats_rapides:
                st.session_state.plats_rapides.append(nouveau_plat)
                sauvegarder_github("data/plats_rapides.json", st.session_state.plats_rapides)
                st.rerun()

    st.divider()
    
    if st.button("💾 Enregistrer Planning", use_container_width=True):
        st.session_state.planning_data.update(temp)
        final = {k: v for k, v in st.session_state.planning_data.items() if k >= (aujourdhui - datetime.timedelta(days=10)).isoformat()}
        if sauvegarder_github("data/planning.json", final):
            st.session_state.planning_data = final
            st.success("Planning enregistré 💾")
            time.sleep(1)
            st.rerun()
