import streamlit as st
import requests, json, base64, time, io
from PIL import Image

# --- LOGIQUE DE COMMUNICATION GITHUB ---
def config_github():
    """Centralise les paramètres de connexion au dépôt."""
    return {
        "headers": {
            "Authorization": f"token {st.secrets['GITHUB_TOKEN']}",
            "Accept": "application/vnd.github.v3+json"
        },
        "base_url": f"https://api.github.com/repos/{st.secrets['REPO_OWNER']}/{st.secrets['REPO_NAME']}/contents/"
    }

def envoyer_donnees(chemin, contenu, message, est_image=False):
    """Fonction universelle pour envoyer texte ou images vers GitHub."""
    conf = config_github()
    url = f"{conf['base_url']}{chemin}"
    
    # 1. Récupération du SHA (obligatoire pour écraser un fichier existant)
    res_get = requests.get(f"{url}?t={int(time.time())}", headers=conf['headers'])
    sha = res_get.json().get('sha') if res_get.status_code == 200 else None
    
    # 2. Encodage selon le type de fichier
    if est_image:
        contenu_b64 = base64.b64encode(contenu).decode('utf-8')
    else:
        contenu_b64 = base64.b64encode(contenu.encode('utf-8')).decode('utf-8')
        
    payload = {"message": message, "content": contenu_b64, "branch": "main"}
    if sha: payload["sha"] = sha
    
    return requests.put(url, headers=conf['headers'], json=payload).status_code in [200, 201]

def charger_index_local():
    """Récupère l'index des recettes en contournant le cache."""
    url = f"https://raw.githubusercontent.com/{st.secrets['REPO_OWNER']}/{st.secrets['REPO_NAME']}/main/data/index_recettes.json?t={int(time.time())}"
    res = requests.get(url)
    return res.json() if res.status_code == 200 else []

# --- INTERFACE DE MAINTENANCE ---
def afficher():
    st.header("🛠️ Réparation et optimisation")
    st.divider()

    # Nettoyage automatique des états temporaires au chargement
    if "bouton_analyse_clique" not in st.session_state:
        for key in ["a_reparer", "index_a_sauvegarder"]:
            if key in st.session_state: 
                del st.session_state[key]

    # --- SECTION 1 : SYNCHRONISATION INDEX ---
    if st.button("🔍 Réparer l'index des recettes", use_container_width=True):
        st.session_state.bouton_analyse_clique = True
        conf = config_github()
        url_tree = f"https://api.github.com/repos/{st.secrets['REPO_OWNER']}/{st.secrets['REPO_NAME']}/git/trees/main?recursive=1"
        res = requests.get(url_tree, headers=conf['headers'])
        
        if res.status_code == 200:
            tree = res.json().get('tree', [])
            exclus = ['data/index_recettes.json', 'data/index_produits_zones.json', 'data/planning.json', 'data/plats_rapides.json']
            
            physiques = [i['path'] for i in tree if i['path'].startswith('data/') and i['path'].endswith('.json') and i['path'] not in exclus]
            index_actuel = charger_index_local()
            chemins_index = {r['chemin'] for r in index_actuel}
            manquantes = [f for f in physiques if f not in chemins_index]

            st.columns(2)[0].metric("Fichiers /data", len(physiques))
            st.columns(2)[1].metric("Index", len(index_actuel))

            if manquantes:
                st.warning(f"⚠️ {len(manquantes)} fichiers hors index.")
                st.session_state.a_reparer = manquantes
            else:
                st.success("✅ Index à jour.")

    if st.session_state.get("a_reparer"):
        if st.button("🚀 Intégrer les fichiers manquants", use_container_width=True):
            with st.spinner("Analyse des contenus..."):
                index_actuel = charger_index_local()
                nouvelles = []
                for chemin in st.session_state.a_reparer:
                    r = requests.get(f"https://raw.githubusercontent.com/{st.secrets['REPO_OWNER']}/{st.secrets['REPO_NAME']}/main/{chemin}")
                    if r.status_code == 200:
                        d = r.json()
                        nouvelles.append({
                            "nom": d.get("nom", "Sans nom"), 
                            "categorie": d.get("categorie", "Non classé"),
                            "appareil": d.get("appareil", "Aucun"),
                            "ingredients": [i.get("Ingrédient") for i in d.get("ingredients", [])],
                            "chemin": chemin
                        })
                index_final = sorted(index_actuel + nouvelles, key=lambda x: x['nom'].lower())
                if envoyer_donnees("data/index_recettes.json", json.dumps(index_final, indent=4, ensure_ascii=False), "🛠️ Réparation"):
                    st.success("✅ Index réparé !")
                    del st.session_state.a_reparer
                    st.rerun()

# --- SECTION 2 : NETTOYAGE INGRÉDIENTS ---
    if st.button("🧹 Réparer le nom des ingrédients", use_container_width=True):
        index_actuel = charger_index_local()
        erreurs, index_nettoye, fichiers_maj = [], [], []
        
        for recette in index_actuel:
            r = requests.get(f"https://raw.githubusercontent.com/{st.secrets['REPO_OWNER']}/{st.secrets['REPO_NAME']}/main/{recette['chemin']}?t={int(time.time())}")
            if r.status_code == 200:
                data = r.json()
                i_clean, noms_i, modif = [], [], False
                details_erreurs = [] # Pour stocker les changements précis
                
                for item in data.get("ingredients", []):
                    n_orig = item.get("Ingrédient", "")
                    # Nettoyage
                    n_propre = " ".join(n_orig.split()).capitalize() 
                    i_clean.append({"Ingrédient": n_propre, "Quantité": item.get("Quantité", "")})
                    noms_i.append(n_propre)
                    
                    if n_propre != n_orig:
                        modif = True
                        details_erreurs.append(f"  ❌ `{n_orig}` ➡️ ✅ `{n_propre}`")
                
                if modif:
                    erreurs.append({
                        "nom": recette["nom"], 
                        "chemin": recette["chemin"],
                        "details": details_erreurs
                    })
                    data["ingredients"] = i_clean
                    fichiers_maj.append({"chemin": recette["chemin"], "contenu": data})
                
                recette_copie = recette.copy()
                recette_copie["ingredients"] = noms_i
                index_nettoye.append(recette_copie)

        if erreurs:
            st.session_state.index_a_sauvegarder = index_nettoye
            st.session_state.fichiers_a_sauvegarder = fichiers_maj
            
            st.warning(f"⚠️ {len(erreurs)} recette(s) à corriger :")
            
            for err in erreurs:
                # Affichage du nom de la recette en gras
                st.markdown(f"**📍 {err['nom']}**")
                # Affichage de chaque ingrédient corrigé en dessous
                for d in err['details']:
                    st.write(d)
                st.divider()
        else:
            st.success("✅ Tous les ingrédients sont déjà parfaitement propres !")

    if st.session_state.get("index_a_sauvegarder"):
        if st.button("🚀 Appliquer le nettoyage", use_container_width=True):
            for f in st.session_state.fichiers_a_sauvegarder:
                envoyer_donnees(f['chemin'], json.dumps(f['contenu'], indent=4, ensure_ascii=False), "🧹 Nettoyage")
            envoyer_donnees("data/index_recettes.json", json.dumps(st.session_state.index_a_sauvegarder, indent=4, ensure_ascii=False), "🧹 Nettoyage Index")
            del st.session_state.index_a_sauvegarder
            st.rerun()

# --- SECTION 3 : OPTIMISATION IMAGES ---
    if st.button("🖼️ Optimiser le poids des images", use_container_width=True):
        conf = config_github()
        res = requests.get(f"https://api.github.com/repos/{st.secrets['REPO_OWNER']}/{st.secrets['REPO_NAME']}/git/trees/main?recursive=1", headers=conf['headers'])
        if res.status_code == 200:
            tree = res.json().get('tree', [])
            
            # FILTRAGE STRICT (Identique à l'origine)
            lourdes = [i for i in tree if i['path'].lower().endswith(('.jpg', '.jpeg', '.png')) and i.get('size', 0) > 500 * 1024]
            
            if lourdes:
                st.session_state.images_a_compresser = lourdes
                st.warning(f"⚠️ {len(lourdes)} image(s) lourde(s) trouvée(s) :")
                
                # RÉTABLISSEMENT DE L'AFFICHAGE D'ORIGINE
                for img in lourdes:
                    st.code(img['path'])
                    st.write(f"Taille : {img['size'] / 1024:.0f} Ko")
                    st.divider() # Petit trait de séparation entre chaque image
            else:
                st.success("Toutes les images sont légères. ✅")

    if st.session_state.get("images_a_compresser"):
        if st.button("⚡ Compresser les images", use_container_width=True):
            barre = st.progress(0)
            for idx, img in enumerate(st.session_state.images_a_compresser):
                r = requests.get(f"https://raw.githubusercontent.com/{st.secrets['REPO_OWNER']}/{st.secrets['REPO_NAME']}/main/{img['path']}")
                if r.status_code == 200:
                    # Conversion RGB pour le JPEG (Indispensable)
                    img_p = Image.open(io.BytesIO(r.content)).convert("RGB")
                    img_p.thumbnail((1200, 1200))
                    buf = io.BytesIO()
                    img_p.save(buf, format="JPEG", quality=75, optimize=True)
                    envoyer_donnees(img['path'], buf.getvalue(), "📸 Opti Image", est_image=True)
                barre.progress((idx + 1) / len(st.session_state.images_a_compresser))
            
            # Nettoyage et rafraîchissement
            del st.session_state.images_a_compresser
            st.success("Compression terminée ! 🚀")
            st.rerun()

    st.divider()

    # --- SECTION 4 : GESTION CATALOGUE ---
    st.subheader("🛒 Modifier ou ranger les produits")
    idx_z = st.session_state.get("index_zones", {})
    tous_p = sorted(list(idx_z.keys()))
    
    if not tous_p:
        st.info("Veuillez charger la page 'Courses' pour initialiser le catalogue.")
    else:
        sel = st.selectbox("Produit à corriger", ["---"] + tous_p)
        if sel != "---":
            z_act = int(idx_z.get(sel, 0)) + 1
            with st.form("form_maint"):
                c1, c2 = st.columns([2, 1])
                n_nom = c1.text_input("Nouveau Nom", value=sel)
                n_zone = c2.text_input("Zone (1-12)", value=str(z_act))
                col_b1, col_b2 = st.columns(2)
                b_s = col_b1.form_submit_button("💾 ENREGISTRER")
                b_d = col_b2.form_submit_button("🗑️ SUPPRIMER")
                
                if b_s:
                    f_nom = n_nom.strip().capitalize()
                    try: d_idx = str(int("".join(filter(str.isdigit, n_zone))) - 1)
                    except: d_idx = str(z_act - 1)
                    
                    if sel in st.session_state.index_zones: 
                        del st.session_state.index_zones[sel]
                    st.session_state.index_zones[f_nom] = d_idx
                    
                    for k in range(12):
                        cat = st.session_state.data_a5[str(k)]["catalogue"]
                        if sel in cat: cat.remove(sel)
                        for p in st.session_state.data_a5[str(k)]["panier"]:
                            if p["nom"].lower() == sel.lower(): p["nom"] = f_nom
                    
                    new_cat = st.session_state.data_a5[d_idx]["catalogue"]
                    if f_nom not in new_cat:
                        new_cat.append(f_nom)
                        new_cat.sort()
                    
                    envoyer_donnees("data/index_produits_zones.json", json.dumps(st.session_state.index_zones, indent=2, ensure_ascii=False), "🛠️ Maj Catalogue")
                    envoyer_donnees("courses/index_courses.json", json.dumps(st.session_state.data_a5, indent=2, ensure_ascii=False), "🛠️ Maj Data")
                    st.success("Mise à jour réussie ! 🚀")
                    time.sleep(1)
                    st.rerun()

                if b_d:
                    if sel in st.session_state.index_zones: 
                        del st.session_state.index_zones[sel]
                    for k in range(12):
                        if sel in st.session_state.data_a5[str(k)]["catalogue"]: 
                            st.session_state.data_a5[str(k)]["catalogue"].remove(sel)
                    envoyer_donnees("data/index_produits_zones.json", json.dumps(st.session_state.index_zones, indent=2, ensure_ascii=False), "🗑️ Suppression")
                    envoyer_donnees("courses/index_courses.json", json.dumps(st.session_state.data_a5, indent=2, ensure_ascii=False), "🗑️ Suppression")
                    st.rerun()

    st.divider()
