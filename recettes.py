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

    # --- SECTION 2 : REPARER L'INDEX INGREDIENT (ÉTAPE MANUELLE) ---
    if st.button("🧹 Réparer l'index des ingredients", use_container_width=True):
        index_actuel = charger_index_local()
        erreurs = []
        index_nettoye = []
        
        for recette in index_actuel:
            liste_brute = recette.get("ingredients", [])
            vus = set()
            liste_propre = []
            a_modifie = False
            
            for ing in liste_brute:
                if ing:
                    nom_nettoye = " ".join(ing.split())
                    cle = nom_nettoye.lower()
                    if cle not in vus:
                        vus.add(cle)
                        liste_propre.append(nom_nettoye)
                        if nom_nettoye != ing:
                            a_modifie = True
                    else:
                        a_modifie = True 
            
            if a_modifie:
                erreurs.append({"nom": recette["nom"], "avant": liste_brute, "apres": liste_propre})
            
            recette_nettoyee = recette.copy()
            recette_nettoyee["ingredients"] = liste_propre
            index_nettoye.append(recette_nettoyee)
            
        st.session_state.erreurs_a_corriger = erreurs
        st.session_state.index_a_sauvegarder = index_nettoye
            
    if "erreurs_a_corriger" in st.session_state and st.session_state.erreurs_a_corriger:
        st.warning(f"⚠️ {len(st.session_state.erreurs_a_corriger)} recette(s) ont des ingrédients mal formatés.")
        
        # Boucle inverse pour la suppression correcte
        for i in range(len(st.session_state.erreurs_a_corriger) - 1, -1, -1):
            e = st.session_state.erreurs_a_corriger[i]
            col_info, col_btn = st.columns([0.85, 0.15])
            
            with col_info:
                with st.expander(f"📍 {e['nom']}"):
                    st.write("**Original :**", e["avant"])
                    st.write("**Nettoyé :**", e["apres"])
            
            with col_btn:
                # Clé unique pour chaque bouton
                if st.button("🗑️", key=f"del_err_{i}_{e['nom']}"):
                    st.session_state.erreurs_a_corriger.pop(i)
                    st.rerun()

    if "index_a_sauvegarder" in st.session_state:
        if st.button("🚀 Appliquer le nettoyage des ingrédients", use_container_width=True):
            if envoyer_vers_github("data/index_recettes.json", 
                                   json.dumps(st.session_state.index_a_sauvegarder, indent=4, ensure_ascii=False), 
                                   "🧹 Nettoyage manuel des ingrédients"):
                st.success("✨ Index ingredient réparé !")
                del st.session_state.index_a_sauvegarder
                if "erreurs_a_corriger" in st.session_state:
                    del st.session_state.erreurs_a_corriger
                time.sleep(1)
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
