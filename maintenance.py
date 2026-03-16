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

    # INITIALISATION : Nettoyage si on change de page
    if "bouton_analyse_clique" not in st.session_state:
        if "a_reparer" in st.session_state:
            del st.session_state.a_reparer
        if "index_a_sauvegarder" in st.session_state:
            del st.session_state.index_a_sauvegarder

    # --- SECTION 1 : RÉPARER L'INDEX ---
    if st.button("🔍 Réparer l'index des recettes", use_container_width=True):
        st.session_state.bouton_analyse_clique = True
        conf = config_github()
        
        url_tree = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/git/trees/main?recursive=1&t={int(time.time())}"
        res = requests.get(url_tree, headers=conf['headers'])
        
        if res.status_code == 200:
            tree = res.json().get('tree', [])
            
            # Exclusion des fichiers de données spécifiques 🚫
            fichiers_exclus = [
                'data/index_recettes.json',
                'data/index_produits_zones.json',
                'data/planning.json',
                'data/plats_rapides.json'
            ]
            
            fichiers_physiques = [
                item['path'] for item in tree 
                if item['path'].startswith('data/') 
                and item['path'].endswith('.json') 
                and item['path'] not in fichiers_exclus
            ]
            
            index_actuel = charger_index_local()
            chemins_index = [r['chemin'] for r in index_actuel]
            manquantes = [f for f in fichiers_physiques if f not in chemins_index]
            
            col1, col2 = st.columns(2)
            col1.metric("Fichiers dans /data", len(fichiers_physiques))
            col2.metric("Recettes dans l'index", len(index_actuel))

            if manquantes:
                st.warning(f"⚠️ {len(manquantes)} fichier(s) trouvé(s) hors index :")
                for m in manquantes:
                    st.code(m)
                st.session_state.a_reparer = manquantes
            else:
                st.success("✅ Félicitations ! Votre index est parfaitement synchronisé.")
                if "a_reparer" in st.session_state:
                    del st.session_state.a_reparer
            
            with st.expander("📂 Voir la liste de tous les fichiers détectés"):
                for i, f in enumerate(sorted(fichiers_physiques), 1):
                    st.write(f"{i}. `{f}`")
        else:
            st.error("Impossible d'accéder à GitHub.")

    if "a_reparer" in st.session_state and st.session_state.a_reparer:
        st.divider()
        st.info("Voulez-vous intégrer ces fichiers à l'index ?")
        if st.button("🚀 Appliquer la réparation", use_container_width=True):
            with st.spinner("Synchronisation..."):
                manquantes = st.session_state.a_reparer
                index_actuel = charger_index_local()
                nouvelles_recettes = []
                for chemin in manquantes:
                    url_raw = f"https://raw.githubusercontent.com/{config_github()['owner']}/{config_github()['repo']}/main/{chemin}?t={int(time.time())}"
                    res_rec = requests.get(url_raw)
                    if res_rec.status_code == 200:
                        data = res_rec.json()
                        nouvelles_recettes.append({
                            "nom": data.get("nom", "Sans nom"),
                            "categorie": data.get("categorie", "Non classé"),
                            "appareil": data.get("appareil", "Aucun"),
                            "ingredients": [i.get("Ingrédient") for i in data.get("ingredients", [])],
                            "chemin": chemin
                        })
                index_final = sorted(index_actuel + nouvelles_recettes, key=lambda x: x['nom'].lower())
                if envoyer_vers_github("data/index_recettes.json", 
                                       json.dumps(index_final, indent=4, ensure_ascii=False), 
                                       "🛠️ Réparation automatique de l'index"):
                    st.success(f"✅ Terminé ! {len(nouvelles_recettes)} recettes ajoutées.")
                    st.session_state.index_recettes = index_final
                    if "a_reparer" in st.session_state: del st.session_state.a_reparer
                    time.sleep(1)
                    st.rerun()

    # --- SECTION 2 : REPARER L'INDEX INGREDIENT (LOGIQUE DOUBLE) ---
    if st.button("🧹 Réparer l'index et les fichiers recettes", use_container_width=True):
        index_actuel = charger_index_local()
        erreurs = []
        index_nettoye = []
        fichiers_a_modifier = [] # Liste pour stocker les fichiers de recettes à mettre à jour
        
        for recette in index_actuel:
            # On récupère le contenu complet de la recette pour vérifier l'intérieur du fichier
            url_raw = f"https://raw.githubusercontent.com/{config_github()['owner']}/{config_github()['repo']}/main/{recette['chemin']}?t={int(time.time())}"
            res_rec = requests.get(url_raw)
            
            if res_rec.status_code == 200:
                data_complete = res_rec.json()
                liste_details = data_complete.get("ingredients", []) # Liste d'objets {"Ingrédient": "...", "Quantité": "..."}
                
                a_modifie_fichier = False
                nouveaux_details = []
                noms_pour_index = []

                for item in liste_details:
                    nom_brut = item.get("Ingrédient", "")
                    if nom_brut:
                        # Nettoyage
                        nom_nettoye = " ".join(nom_brut.split())
                        nouveaux_details.append({
                            "Ingrédient": nom_nettoye,
                            "Quantité": item.get("Quantité", "")
                        })
                        noms_pour_index.append(nom_nettoye)
                        if nom_nettoye != nom_brut:
                            a_modifie_fichier = True

                if a_modifie_fichier:
                    erreurs.append({"nom": recette["nom"], "chemin": recette["chemin"]})
                    # On prépare la version mise à jour du fichier complet
                    data_complete["ingredients"] = nouveaux_details
                    fichiers_a_modifier.append({
                        "chemin": recette["chemin"],
                        "contenu": data_complete
                    })
                
                # Mise à jour de l'index (liste simple de noms)
                recette_nettoyee = recette.copy()
                recette_nettoyee["ingredients"] = noms_pour_index
                index_nettoye.append(recette_nettoyee)
            
        if erreurs:
            st.warning(f"⚠️ {len(erreurs)} recette(s) à synchroniser.")
            st.session_state.index_a_sauvegarder = index_nettoye
            st.session_state.fichiers_a_sauvegarder = fichiers_a_modifier
        else:
            st.success("✅ Tout est déjà parfaitement propre !")

    if "index_a_sauvegarder" in st.session_state:
        if st.button("🚀 Appliquer la réparation globale", use_container_width=True):
            with st.spinner("Mise à jour des fichiers..."):
                # 1. On répare chaque fichier de recette
                for f in st.session_state.fichiers_a_sauvegarder:
                    envoyer_vers_github(f['chemin'], 
                                       json.dumps(f['contenu'], indent=4, ensure_ascii=False), 
                                       f"🧹 Nettoyage ingrédient : {f['chemin']}")
                
                # 2. On répare l'index global
                if envoyer_vers_github("data/index_recettes.json", 
                                       json.dumps(st.session_state.index_a_sauvegarder, indent=4, ensure_ascii=False), 
                                       "🧹 Nettoyage global de l'index"):
                    st.success("✨ Réparation terminée sur tous les fichiers !")
                    del st.session_state.index_a_sauvegarder
                    del st.session_state.fichiers_a_sauvegarder
                    time.sleep(2) # On laisse un peu de temps à GitHub
                    st.rerun()

    # --- SECTION 3 : COMPRESSION DES IMAGES ---
    if st.button("🖼️ Optimisation des Images", use_container_width=True):
        conf = config_github()
        url_tree = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/git/trees/main?recursive=1"
        res = requests.get(url_tree, headers=conf['headers'])
        
        if res.status_code == 200:
            tree = res.json().get('tree', [])
            lourdes = [i for i in tree if i['path'].lower().endswith(('.jpg', '.jpeg', '.png')) and i.get('size', 0) > 500 * 1024]
            
            if lourdes:
                st.warning(f"Il y a {len(lourdes)} images à optimiser.")
                for img in lourdes:
                    st.text(f"📍 {img['path']} ({img['size']//1024} Ko)")
                st.session_state.images_a_compresser = lourdes
            else:
                st.success("Toutes les images sont légères !")
        else:
            st.error("Erreur GitHub.")

    if "images_a_compresser" in st.session_state:
        if st.button("⚡ Lancer la compression sans perte", use_container_width=True):
            barre = st.progress(0)
            lourdes = st.session_state.images_a_compresser
            for idx, img_info in enumerate(lourdes):
                url_raw = f"https://raw.githubusercontent.com/{config_github()['owner']}/{config_github()['repo']}/main/{img_info['path']}"
                res = requests.get(url_raw)
                if res.status_code == 200:
                    image_pil = Image.open(io.BytesIO(res.content))
                    buffer = io.BytesIO()
                    image_pil.save(buffer, format="JPEG", quality=80, optimize=True)
                    if envoyer_image_vers_github(img_info['path'], buffer.getvalue(), "📸 Compression image"):
                        st.write(f"✅ {img_info['path']} optimisée.")
                barre.progress((idx + 1) / len(lourdes))
            del st.session_state.images_a_compresser
            st.success("Toutes les images ont été traitées.")

    st.divider()

    # --- SECTION 4 : GESTION PRODUIT ---
    def maintenance_produits():
        st.subheader("🛠️ Modification du Catalogue")
    
        # On récupère l'index des produits pour savoir quoi modifier
        index_zones = st.session_state.get("index_zones", {})
        tous_produits = sorted(list(index_zones.keys()))
    
        if not tous_produits:
            st.info("Le catalogue est vide.")
            return
    
        # Sélecteur du produit
        prod_sel = st.selectbox("Choisir un produit à corriger", ["---"] + tous_produits)
    
        if prod_sel != "---":
            zone_actuelle = int(index_zones.get(prod_sel, 0)) + 1
            
            with st.form("form_maintenance"):
                col1, col2 = st.columns([2, 1])
                nouveau_nom = col1.text_input("Nom du produit", value=prod_sel)
                nouvelle_zone = col2.text_input("Zone", value=str(zone_actuelle))
                
                c_save, c_del = st.columns(2)
                btn_save = c_save.form_submit_button("💾 ENREGISTRER", use_container_width=True)
                btn_del = c_del.form_submit_button("🗑️ SUPPRIMER", use_container_width=True)
    
                if btn_save:
                    final_nom = nouveau_nom.strip().capitalize()
                    try:
                        num_extrait = "".join(filter(str.isdigit, nouvelle_zone))
                        dest_idx = str(int(num_extrait) - 1)
                    except:
                        dest_idx = str(zone_actuelle - 1)
    
                    # 1. Mise à jour de l'index des zones
                    if prod_sel in st.session_state.index_zones:
                        del st.session_state.index_zones[prod_sel]
                    st.session_state.index_zones[final_nom] = dest_idx
                    
                    # 2. Mise à jour dans data_a5 (Catalogue et Panier)
                    for k in range(12):
                        # Correction du catalogue
                        if prod_sel in st.session_state.data_a5[str(k)]["catalogue"]:
                            st.session_state.data_a5[str(k)]["catalogue"].remove(prod_sel)
                        
                        # Mise à jour du nom dans le panier si déjà présent
                        for p in st.session_state.data_a5[str(k)]["panier"]:
                            if p["nom"].lower() == prod_sel.lower():
                                p["nom"] = final_nom
    
                    # Ajout du nouveau nom dans le catalogue de la zone de destination
                    if final_nom not in st.session_state.data_a5[dest_idx]["catalogue"]:
                        st.session_state.data_a5[dest_idx]["catalogue"].append(final_nom)
                        st.session_state.data_a5[dest_idx]["catalogue"].sort()
    
                    # Sauvegardes GitHub
                    save_github_data("data/index_produits_zones.json", st.session_state.index_zones, st.session_state.sha_index)
                    save_github_data("courses/data_a5.json", st.session_state.data_a5, st.session_state.sha_a5)
                    
                    st.success(f"✅ {final_nom} mis à jour !")
                    time.sleep(1)
                    st.rerun()
    
                if btn_del:
                    # Suppression totale
                    if prod_sel in st.session_state.index_zones:
                        del st.session_state.index_zones[prod_sel]
                    
                    for k in range(12):
                        if prod_sel in st.session_state.data_a5[str(k)]["catalogue"]:
                            st.session_state.data_a5[str(k)]["catalogue"].remove(prod_sel)
                    
                    save_github_data("data/index_produits_zones.json", st.session_state.index_zones, st.session_state.sha_index)
                    save_github_data("courses/data_a5.json", st.session_state.data_a5, st.session_state.sha_a5)
                    
                    st.warning(f"🗑️ {prod_sel} supprimé.")
                    time.sleep(1)
                    st.rerun()
                
                maintenance_produits()
