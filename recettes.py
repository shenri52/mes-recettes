import streamlit as st
import requests
import json
import base64
import time

def config_github():
    return {
        "token": st.secrets["GITHUB_TOKEN"],
        "owner": st.secrets["REPO_OWNER"],
        "repo": st.secrets["REPO_NAME"],
        "headers": {
            "Authorization": f"token {st.secrets['GITHUB_TOKEN']}",
            "Accept": "application/vnd.github.v3+json"
        }
    }

def envoyer_vers_github(chemin, contenu, message):
    conf = config_github()
    url = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/{chemin}"
    res_get = requests.get(f"{url}?t={int(time.time())}", headers=conf['headers'])
    sha = res_get.json().get('sha') if res_get.status_code == 200 else None
    contenu_b64 = base64.b64encode(contenu.encode('utf-8')).decode('utf-8')
    data = {"message": message, "content": contenu_b64, "branch": "main"}
    if sha: data["sha"] = sha
    res = requests.put(url, headers=conf['headers'], json=data)
    return res.status_code in [200, 201]

def supprimer_fichier_github(chemin):
    if not chemin: return
    conf = config_github()
    url = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/{chemin.strip('/')}"
    get_res = requests.get(f"{url}?t={int(time.time())}", headers=conf['headers'])
    if get_res.status_code == 200:
        sha = get_res.json()['sha']
        requests.delete(url, headers=conf['headers'], json={"message": "Suppression", "sha": sha, "branch": "main"})
        return True
    return False

def afficher():
    st.header("📚 Mes recettes")
    conf = config_github()
    
    url_dossier = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/data/recettes?t={int(time.time())}"
    res_dossier = requests.get(url_dossier, headers=conf['headers'])
    
    if res_dossier.status_code == 200:
        fichiers_github = res_dossier.json()
        jsons_uniques = [f for f in fichiers_github if f['name'].endswith('.json')]
        
        # Pour garder les filtres fonctionnels, on utilise les noms de fichiers pour l'instant
        col_search, col_app, col_ing = st.columns([2, 1, 1])
        recherche = col_search.text_input("🔍 Rechercher un plat", "").lower()
        
        # Listes pour les filtres (basées sur les noms de fichiers pour la rapidité)
        filtre_app = col_app.selectbox("Appareil", ["Tous", "Cookeo", "Thermomix", "Ninja", "Aucun"])
        filtre_ing = col_ing.selectbox("Ingrédient", ["Tous"]) # L'indexation complète nécessiterait un pré-chargement

        st.divider()

        for idx, f in enumerate(jsons_uniques):
            nom_affiche = f['name'].replace('.json', '').replace('_', ' ').upper()
            
            if recherche and recherche not in nom_affiche.lower():
                continue

            with st.expander(f"📖 {nom_affiche}"):
                # --- CHARGEMENT AU CLIC ---
                raw_url = f"https://raw.githubusercontent.com/{conf['owner']}/{conf['repo']}/main/{f['path']}?v={f['sha']}"
                res_file = requests.get(raw_url)
                
                if res_file.status_code == 200:
                    rec = res_file.json()
                    rec['chemin_json'] = f['path']
                    
                    m_edit = f"edit_{idx}"
                    if m_edit not in st.session_state: st.session_state[m_edit] = False

                    if st.session_state[m_edit]:
                        # --- MODE MODIFICATION ---
                        with st.form(key=f"f_edit_{idx}"):
                            e_nom = st.text_input("Nom", value=rec.get('nom', ''))
                            c1, c2, c3 = st.columns(3)
                            with c1:
                                e_app = st.selectbox("Appareil", ["Aucun", "Cookeo", "Thermomix", "Ninja"], 
                                               index=["Aucun", "Cookeo", "Thermomix", "Ninja"].index(rec.get('appareil', 'Aucun')))
                            with c2:
                                e_prep = st.text_input("Temps prépa.", value=rec.get('temps_preparation', ''))
                            with c3:
                                e_cuis = st.text_input("Temps cuisson", value=rec.get('temps_cuisson', ''))
                            
                            ing_txt = "\n".join([f"{i.get('Quantité', '')} | {i.get('Ingrédient', '')}" for i in rec.get('ingredients', [])])
                            e_ings = st.text_area("Ingrédients (Qté | Nom)", value=ing_txt)
                            e_etapes = st.text_area("Préparation", value=rec.get('etapes', ''), height=150)
                            
                            cs, cc = st.columns(2)
                            if cs.form_submit_button("✅ Enregistrer", use_container_width=True):
                                new_ings = []
                                for l in e_ings.strip().split('\n'):
                                    if not l.strip(): continue 
                                    if "|" in l:
                                        parties = l.split("|", 1)
                                        new_ings.append({"Ingrédient": parties[1].strip(), "Quantité": parties[0].strip()})
                                    else:
                                        new_ings.append({"Ingrédient": l.strip(), "Quantité": ""})
                                
                                data_mod = {
                                    "nom": e_nom, "appareil": e_app, 
                                    "temps_preparation": e_prep, "temps_cuisson": e_cuis,
                                    "ingredients": new_ings, "etapes": e_etapes, "images": rec.get('images', [])
                                }
                                if envoyer_vers_github(rec['chemin_json'], json.dumps(data_mod, indent=4, ensure_ascii=False), f"Modif: {e_nom}"):
                                    st.session_state[m_edit] = False
                                    st.rerun()
                            if cc.form_submit_button("❌ Annuler", use_container_width=True):
                                st.session_state[m_edit] = False
                                st.rerun()
                    else:
                        # --- MODE LECTURE ---
                        t_prep = rec.get('temps_preparation', '')
                        t_cuis = rec.get('temps_cuisson', '')
                        if t_prep or t_cuis:
                            cols_t = st.columns(2)
                            if t_prep: cols_t[0].markdown(f"⏱️ **Préparation :** {t_prep}")
                            if t_cuis: cols_t[1].markdown(f"🔥 **Cuisson :** {t_cuis}")
                            st.write("")

                        c_txt, c_img = st.columns([1, 1])
                        with c_txt:
                            st.subheader("🍴 Détails")
                            st.write(f"**Appareil :** {rec.get('appareil', 'Aucun')}")
                            st.write("**Ingrédients :**")
                            for i in rec.get('ingredients', []):
                                st.write(f"- {i.get('Quantité', '')} {i.get('Ingrédient', '')}")
                            st.write(f"**Étapes :**\n{rec.get('etapes', '')}")
                        
                        with c_img:
                            st.subheader("🖼️ Galerie")
                            medias = rec.get('images', [])
                            if medias:
                                kn = f"img_idx_{idx}"
                                if kn not in st.session_state: st.session_state[kn] = 0
                                cur = st.session_state[kn] % len(medias)
                                
                                if len(medias) > 1:
                                    cp, c_gal, cn = st.columns([1, 1, 1])
                                    if cp.button("⬅️", key=f"prev_{idx}"): 
                                        st.session_state[kn] -= 1
                                        st.rerun()
                                    c_gal.write(f"{cur+1}/{len(medias)}")
                                    if cn.button("➡️", key=f"next_{idx}"): 
                                        st.session_state[kn] += 1
                                        st.rerun()
                                
                                img_path = medias[cur].strip("/")
                                full_url = f"https://raw.githubusercontent.com/{conf['owner']}/{conf['repo']}/main/{img_path if img_path.startswith('data/') else 'data/'+img_path}?t={int(time.time())}"
                                st.image(full_url, use_container_width=True)
                            else: st.info("Pas d'image.")

                        st.divider()
                        b1, b2 = st.columns(2)
                        if b1.button(f"🗑️ Supprimer la recette", key=f"del_btn_{idx}", use_container_width=True):
                            if supprimer_fichier_github(rec['chemin_json']):
                                st.rerun()
                        if b2.button(f"✍️ Modifier la recette", key=f"edit_btn_{idx}", use_container_width=True):
                            st.session_state[m_edit] = True
                            st.rerun()

if __name__ == "__main__":
    afficher()
