import streamlit as st
import requests
import json
import base64
import time
import io
from PIL import Image

# --- FONCTIONS TECHNIQUES AUTONOMES ---
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

def envoyer_image_vers_github(chemin, contenu_octets, message):
    conf = config_github()
    url = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/{chemin}"
    res_get = requests.get(f"{url}?t={int(time.time())}", headers=conf['headers'])
    sha = res_get.json().get('sha') if res_get.status_code == 200 else None
    contenu_b64 = base64.b64encode(contenu_octets).decode('utf-8')
    data = {"message": message, "content": contenu_b64, "branch": "main"}
    if sha: data["sha"] = sha
    res = requests.put(url, headers=conf['headers'], json=data)
    return res.status_code in [200, 201]

def charger_index_local():
    conf = config_github()
    url = f"https://raw.githubusercontent.com/{conf['owner']}/{conf['repo']}/main/data/index_recettes.json?t={int(time.time())}"
    res = requests.get(url)
    return res.json() if res.status_code == 200 else []

# --- INTERFACE DE RÉPARATION ---
def afficher():
    st.header("🛠️ Diagnostic et réparation")
    st.divider()

    if "bouton_analyse_clique" not in st.session_state:
        if "a_reparer" in st.session_state: del st.session_state.a_reparer
        if "index_a_sauvegarder" in st.session_state: del st.session_state.index_a_sauvegarder

    # --- SECTION 1 : RÉPARER L'INDEX ---
    if st.button("🔍 Réparer l'index des recettes", use_container_width=True):
        st.session_state.bouton_analyse_clique = True
        conf = config_github()
        url_tree = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/git/trees/main?recursive=1&t={int(time.time())}"
        res = requests.get(url_tree, headers=conf['headers'])
        
        if res.status_code == 200:
            tree = res.json().get('tree', [])
            fichiers_exclus = ['data/index_recettes.json', 'data/index_produits_zones.json', 'data/planning.json', 'data/plats_rapides.json']
            fichiers_physiques = [item['path'] for item in tree if item['path'].startswith('data/') and item['path'].endswith('.json') and item['path'] not in fichiers_exclus]
            index_actuel = charger_index_local()
            chemins_index = [r['chemin'] for r in index_actuel]
            manquantes = [f for f in fichiers_physiques if f not in chemins_index]
            
            col1, col2 = st.columns(2)
            col1.metric("Fichiers dans /data", len(fichiers_physiques))
            col2.metric("Recettes dans l'index", len(index_actuel))

            if manquantes:
                st.warning(f"⚠️ {len(manquantes)} fichier(s) trouvé(s) hors index :")
                for m in manquantes: st.code(m)
                st.session_state.a_reparer = manquantes
            else:
                st.success("✅ Index parfaitement synchronisé.")
        else:
            st.error("Impossible d'accéder à GitHub.")

    if "a_reparer" in st.session_state and st.session_state.a_reparer:
        if st.button("🚀 Appliquer la réparation", use_container_width=True):
            with st.spinner("Synchronisation..."):
                index_actuel = charger_index_local()
                nouvelles = []
                for chemin in st.session_state.a_reparer:
                    res_rec = requests.get(f"https://raw.githubusercontent.com/{config_github()['owner']}/{config_github()['repo']}/main/{chemin}")
                    if res_rec.status_code == 200:
                        data = res_rec.json()
                        nouvelles.append({"nom": data.get("nom", "Sans nom"), "categorie": data.get("categorie", "Non classé"), "appareil": data.get("appareil", "Aucun"), "ingredients": [i.get("Ingrédient") for i in data.get("ingredients", [])], "chemin": chemin})
                index_final = sorted(index_actuel + nouvelles, key=lambda x: x['nom'].lower())
                if envoyer_vers_github("data/index_recettes.json", json.dumps(index_final, indent=4, ensure_ascii=False), "🛠️ Réparation index"):
                    st.success("✅ Terminé !")
                    del st.session_state.a_reparer
                    time.sleep(1)
                    st.rerun()

    # --- SECTION 2 : NETTOYAGE INGRÉDIENTS ---
    if st.button("🧹 Réparer le nom des ingrédients", use_container_width=True):
        index_actuel = charger_index_local()
        erreurs, index_nettoye, fichiers_a_modifier = [], [], []
        for recette in index_actuel:
            res_rec = requests.get(f"https://raw.githubusercontent.com/{config_github()['owner']}/{config_github()['repo']}/main/{recette['chemin']}?t={int(time.time())}")
            if res_rec.status_code == 200:
                data_c = res_rec.json()
                liste_i = data_c.get("ingredients", [])
                a_mod, nouveaux_i, noms_idx = False, [], []
                for item in liste_i:
                    nom_b = item.get("Ingrédient", "")
                    if nom_b:
                        nom_n = " ".join(nom_b.split())
                        nouveaux_i.append({"Ingrédient": nom_n, "Quantité": item.get("Quantité", "")})
                        noms_idx.append(nom_n)
                        if nom_n != nom_b: a_mod = True
                if a_mod:
                    erreurs.append(recette["nom"])
                    data_c["ingredients"] = nouveaux_i
                    fichiers_a_modifier.append({"chemin": recette["chemin"], "contenu": data_c})
                r_n = recette.copy()
                r_n["ingredients"] = noms_idx
                index_nettoye.append(r_n)
        if erreurs:
            st.warning(f"⚠️ {len(erreurs)} recette(s) à nettoyer.")
            st.session_state.index_a_sauvegarder = index_nettoye
            st.session_state.fichiers_a_sauvegarder = fichiers_a_modifier
        else:
            st.success("✅ Tout est propre !")

    if "index_a_sauvegarder" in st.session_state:
        if st.button("🚀 Lancer le nettoyage global", use_container_width=True):
            with st.spinner("Mise à jour..."):
                for f in st.session_state.fichiers_a_sauvegarder:
                    envoyer_vers_github(f['chemin'], json.dumps(f['contenu'], indent=4, ensure_ascii=False), "🧹 Nettoyage")
                envoyer_vers_github("data/index_recettes.json", json.dumps(st.session_state.index_a_sauvegarder, indent=4, ensure_ascii=False), "🧹 Nettoyage Index")
                del st.session_state.index_a_sauvegarder
                st.rerun()

    # --- SECTION 3 : IMAGES ---
    if st.button("🖼️ Optimisation des Images", use_container_width=True):
        conf = config_github()
        res = requests.get(f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/git/trees/main?recursive=1", headers=conf['headers'])
        if res.status_code == 200:
            lourdes = [i for i in res.json().get('tree', []) if i['path'].lower().endswith(('.jpg', '.jpeg', '.png')) and i.get('size', 0) > 500 * 1024]
            if lourdes: st.session_state.images_a_compresser = lourdes
            else: st.success("Images légères ✅")

    if "images_a_compresser" in st.session_state:
        if st.button("⚡ Compresser maintenant", use_container_width=True):
            barre = st.progress(0)
            for idx, img in enumerate(st.session_state.images_a_compresser):
                r = requests.get(f"https://raw.githubusercontent.com/{config_github()['owner']}/{config_github()['repo']}/main/{img['path']}")
                if r.status_code == 200:
                    img_p = Image.open(io.BytesIO(r.content)).convert("RGB")
                    buf = io.BytesIO()
                    img_p.save(buf, format="JPEG", quality=75, optimize=True)
                    envoyer_image_vers_github(img['path'], buf.getvalue(), "📸 Opti")
                barre.progress((idx + 1) / len(st.session_state.images_a_compresser))
            del st.session_state.images_a_compresser
            st.rerun()

    st.divider()

    # --- SECTION 4 : GESTION PRODUITS ---
    def maintenance_produits():
        st.subheader("🛒 Modification des noms et zone des courses")
        idx_z = st.session_state.get("index_zones", {})
        tous_p = sorted(list(idx_z.keys()))
        if not tous_p:
            st.info("Ouvrez la page 'Courses' pour charger le catalogue.")
            return
        
        sel = st.selectbox("Produit à corriger", ["---"] + tous_p)
        if sel != "---":
            z_act = int(idx_z.get(sel, 0)) + 1
            with st.form("form_maint"):
                c1, c2 = st.columns([2, 1])
                n_nom = c1.text_input("Nom", value=sel)
                n_zone = c2.text_input("Zone", value=str(z_act))
                b_s = st.form_submit_button("💾 ENREGISTRER", use_container_width=True)
                b_d = st.form_submit_button("🗑️ SUPPRIMER", use_container_width=True)
                
                if b_s:
                    f_nom = n_nom.strip().capitalize()
                    try: d_idx = str(int("".join(filter(str.isdigit, n_zone))) - 1)
                    except: d_idx = str(z_act - 1)
                    
                    if sel in st.session_state.index_zones: del st.session_state.index_zones[sel]
                    st.session_state.index_zones[f_nom] = d_idx
                    
                    for k in range(12):
                        if sel in st.session_state.data_a5[str(k)]["catalogue"]: st.session_state.data_a5[str(k)]["catalogue"].remove(sel)
                        for p in st.session_state.data_a5[str(k)]["panier"]:
                            if p["nom"].lower() == sel.lower(): p["nom"] = f_nom
                    if f_nom not in st.session_state.data_a5[d_idx]["catalogue"]:
                        st.session_state.data_a5[d_idx]["catalogue"].append(f_nom)
                        st.session_state.data_a5[d_idx]["catalogue"].sort()
                    
                    envoyer_vers_github("data/index_produits_zones.json", json.dumps(st.session_state.index_zones, indent=2, ensure_ascii=False), "🛠️ Maint Index")
                    envoyer_vers_github("courses/data_a5.json", json.dumps(st.session_state.data_a5, indent=2, ensure_ascii=False), "🛠️ Maint Data")
                    st.success("Mis à jour ! 🚀")
                    time.sleep(1)
                    st.rerun()

                if b_d:
                    if sel in st.session_state.index_zones: del st.session_state.index_zones[sel]
                    for k in range(12):
                        if sel in st.session_state.data_a5[str(k)]["catalogue"]: st.session_state.data_a5[str(k)]["catalogue"].remove(sel)
                    envoyer_vers_github("data/index_produits_zones.json", json.dumps(st.session_state.index_zones, indent=2, ensure_ascii=False), "🗑️ Del")
                    envoyer_vers_github("courses/data_a5.json", json.dumps(st.session_state.data_a5, indent=2, ensure_ascii=False), "🗑️ Del")
                    st.rerun()

    maintenance_produits()

if __name__ == "__main__":
    afficher()
