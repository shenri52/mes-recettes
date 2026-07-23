import streamlit as st
import requests, time
from utils import config_github, charger_index, sauvegarder_index, telecharger_projet_complet

def verifier_images_manquantes():  
    if st.button("🔎 Vérifier les images manquantes", use_container_width=True):
        with st.spinner("Analyse du dépôt GitHub..."):
            conf = config_github()
            
            # 1. Récupération de la liste des fichiers existants sur GitHub
            url_tree = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/git/trees/main?recursive=1"
            res = requests.get(url_tree, headers=conf['headers'])
            
            if res.status_code != 200:
                st.error("Impossible d'accéder à l'API GitHub.")
                return
            
            tree = res.json().get('tree', [])
            images_existantes = {
                item['path'] for item in tree 
                if item['path'].startswith('data/images/')
            }
            
            index = charger_index()
            images_cassees = []  # Lien dans le JSON mais fichier inexistant sur GitHub
            sans_image = []      # Aucune image déclarée dans le JSON
            
            # 2. Vérification de chaque recette
            for r in index:
                url_raw = f"https://raw.githubusercontent.com/{conf['owner']}/{conf['repo']}/main/{r['chemin']}"
                res_rec = requests.get(url_raw)
                
                if res_rec.status_code == 200:
                    data = res_rec.json()
                    imgs = data.get('images', [])
                    
                    if not imgs:
                        sans_image.append(r['nom'])
                    else:
                        for img_path in imgs:
                            p_clean = img_path.strip('/')
                            if p_clean not in images_existantes:
                                images_cassees.append((r['nom'], p_clean))

            # 3. Affichage des résultats
            if images_cassees:
                st.error(f"❌ **{len(images_cassees)} photo(s) introuvable(s) dans `data/images/` :**")
                for nom, img in images_cassees:
                    st.write(f"- **{nom}** ➔ Fichier manquant : `{img}`")
            else:
                st.success("✅ Aucun lien d'image cassé !")

            if sans_image:
                st.warning(f"⚠️ **{len(sans_image)} recette(s) sans photo enregistrée :**")
                for nom in sans_image:
                    st.write(f"- {nom}")

def afficher():
    # --- 1. LOGIQUE DE NETTOYAGE (ANTI-FANTÔME) ---
    if "clic_reparation" not in st.session_state:
        if "a_reparer" in st.session_state:
            del st.session_state["a_reparer"]
    else:
        del st.session_state["clic_reparation"]

    # --- 2. SECTION : ANALYSE ET RÉPARATION DE L'INDEX ---
    if st.button("🔍 Réparer l'index des recettes", use_container_width=True):
        st.session_state.clic_reparation = True
        conf = config_github()
        
        url_tree = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/git/trees/main?recursive=1"
        res = requests.get(url_tree, headers=conf['headers'])
        
        if res.status_code == 200:
            tree = res.json().get('tree', [])
            
            fichiers_physiques = [
                i['path'] for i in tree 
                if i['path'].startswith('data/recettes/') and i['path'].endswith('.json')
            ]
            
            index_actuel = charger_index()
            chemins_dans_index = {r['chemin'] for r in index_actuel}
            
            manquantes = [f for f in fichiers_physiques if f not in chemins_dans_index]

            st.write(f"📁 **Fichiers de recettes trouvés sur GitHub :** {len(fichiers_physiques)}")
            st.write(f"🗂️ **Recettes listées dans l'index :** {len(index_actuel)}")
            
            if manquantes:
                st.warning(f"⚠️ {len(manquantes)} fichier(s) ne sont pas listés dans l'index.")
                with st.expander("📄 Voir la liste des fichiers à intégrer"):
                    for m in manquantes:
                        st.write(f"- `{m}`")
                
                st.session_state.a_reparer = manquantes
            else:
                st.success("✅ L'index est parfaitement à jour.")
        else:
            st.error("Impossible d'accéder à l'API GitHub pour l'analyse.")

    # --- 3. SECTION : ACTION DE RÉPARATION ---
    if "a_reparer" in st.session_state:
        st.divider()
        if st.button("🚀 Lancer la réparation automatique", use_container_width=True):
            with st.spinner("Récupération des données et fusion de l'index..."):
                idx_actuel = charger_index()
                nouvelles_entrees = []
                conf = config_github()

                for chemin in st.session_state.a_reparer:
                    url_raw = f"https://raw.githubusercontent.com/{conf['owner']}/{conf['repo']}/main/{chemin}"
                    r = requests.get(url_raw)
                    
                    if r.status_code == 200:
                        try:
                            d = r.json()
                            nouvelles_entrees.append({
                                "nom": d.get("nom", "Sans nom"),
                                "categorie": d.get("categorie", "Non classé"),
                                "appareil": d.get("appareil", "Aucun"),
                                "ingredients": [i.get("Ingrédient") for i in d.get("ingredients", [])],
                                "chemin": chemin
                            })
                        except Exception as e:
                            st.error(f"Erreur de lecture sur {chemin}: {e}")
                
                index_final = idx_actuel + nouvelles_entrees
                
                if sauvegarder_index(index_final):
                    st.success(f"✅ Réparation terminée : {len(nouvelles_entrees)} recettes ajoutées !")
                    if "a_reparer" in st.session_state:
                        del st.session_state["a_reparer"]
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("Erreur lors de la sauvegarde de l'index mis à jour.")

    # --- 4. SECTION : VÉRIFICATION DES IMAGES MANQUANTES ---
    verifier_images_manquantes()

    # --- 5. SECTION : SAUVEGARDE DU PROJET ---
    if "save_termine" not in st.session_state:
        st.session_state.save_termine = False

    if not st.session_state.save_termine:
        if st.button("💾 Sauvegarder le projet", use_container_width=True):
            with st.spinner("Compression du projet en cours..."):
                zip_data = telecharger_projet_complet()
                
                if zip_data:
                    st.download_button(
                        label="📥 Télécharger le ZIP maintenant",
                        data=zip_data,
                        file_name="SAUVEGARDE_COMPLETE_RECETTES.zip", 
                        mime="application/zip",
                        use_container_width=True,
                        on_click=lambda: st.session_state.update({"save_termine": True})
                    )
                else:
                    st.error("Erreur lors de la récupération du projet.")
    else:
        st.info("✅ Le téléchargement va débuter dans quelques secondes ! Pensez à déplacer le fichier de sauvegarde vers votre dossier sécurisé.")
