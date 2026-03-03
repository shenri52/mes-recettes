import streamlit as st
import requests
import json
import base64

# --- FONCTIONS GITHUB (LECTURE / SUPPRESSION) ---
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

def charger_fichiers(dossier):
    conf = config_github()
    url = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/{dossier}"
    res = requests.get(url, headers=conf['headers'])
    if res.status_code == 200:
        return res.json()
    return []

def supprimer_fichier_github(chemin, message="Suppression"):
    conf = config_github()
    url = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/{chemin}"
    # Il faut d'abord récupérer le SHA du fichier pour le supprimer
    get_res = requests.get(url, headers=conf['headers'])
    if get_res.status_code == 200:
        sha = get_res.json()['sha']
        data = {"message": message, "sha": sha, "branch": "main"}
        del_res = requests.delete(url, headers=conf['headers'], json=data)
        return del_res.status_code in [200, 204]
    return False

def afficher():
    st.header("📚 Mes recettes")

    # --- 1. CHARGEMENT DES DONNÉES ---
    if 'toutes_recettes' not in st.session_state:
        with st.spinner("Chargement de la bibliothèque..."):
            fichiers = charger_fichiers("data/recettes")
            data_recettes = []
            for f in fichiers:
                if f['name'].endswith('.json'):
                    content_res = requests.get(f['download_url'])
                    if content_res.status_code == 200:
                        recette_data = content_res.json()
                        recette_data['chemin_json'] = f['path']
                        data_recettes.append(recette_data)
            st.session_state.toutes_recettes = data_recettes

    # --- 2. ZONE DE RECHERCHE ET FILTRES ---
    col_search, col_app, col_ing = st.columns([2, 1, 1])
    
    with col_search:
        recherche = st.text_input("🔍 Rechercher un plat", "").lower()
    
    with col_app:
        liste_apps = ["Tous"] + list(set(r.get('appareil', 'Aucun') for r in st.session_state.toutes_recettes))
        filtre_app = st.selectbox("Appareil", options=liste_apps)
    
    with col_ing:
        # Extraire tous les ingrédients uniques pour le filtre
        tous_ings = []
        for r in st.session_state.toutes_recettes:
            for i in r.get('ingredients', []):
                tous_ings.append(i.get('Ingrédient'))
        filtre_ing = st.selectbox("Ingrédient", options=["Tous"] + sorted(list(set(tous_ings))))

    # --- 3. LOGIQUE DE FILTRAGE ---
    recettes_filtrees = [
        r for r in st.session_state.toutes_recettes
        if recherche in r['nom'].lower()
        and (filtre_app == "Tous" or r.get('appareil') == filtre_app)
        and (filtre_ing == "Tous" or any(i.get('Ingrédient') == filtre_ing for i in r.get('ingredients', [])))
    ]

    # --- 4. AFFICHAGE DES RÉSULTATS ---
    if not recettes_filtrees:
        st.info("Aucune recette ne correspond à vos critères.")
    else:
        for index, rec in enumerate(recettes_filtrees):
            with st.expander(f"{rec.get('appareil', '🍳')} - {rec['nom']}"):
                col_info, col_media = st.columns([1, 1])
                
                with col_info:
                    st.subheader("Ingrédients")
                    for ing in rec.get('ingredients', []):
                        st.write(f"• {ing['Quantité']} {ing['Ingrédient']}")
                    
                    st.subheader("Préparation")
                    st.write(rec.get('etapes', "Aucune étape renseignée."))
                    
                    # Bouton de suppression
                    if st.button(f"🗑️ Supprimer", key=f"del_{index}"):
                        with st.spinner("Suppression en cours..."):
                            # Supprimer le JSON
                            success_json = supprimer_fichier_github(rec['chemin_json'], f"Suppression recette {rec['nom']}")
                            # Supprimer l'image si elle existe
                            if rec.get('image'):
                                supprimer_fichier_github(rec['image'], "Suppression image associée")
                            
                            if success_json:
                                st.success("Recette supprimée !")
                                del st.session_state.toutes_recettes # Forcer rechargement
                                st.rerun()

                with col_media:
                    st.subheader("Médias")
                    chemin_media = rec.get('image')
                    if chemin_media:
                        conf = config_github()
                        url_media = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/{chemin_media}"
                        res_m = requests.get(url_media, headers=conf['headers'])
                        
                        if res_m.status_code == 200:
                            b64_data = res_m.json()['content']
                            file_bytes = base64.b64decode(b64_data)
                            
                            if chemin_media.lower().endswith('.pdf'):
                                # Affichage PDF
                                st.download_button("📂 Télécharger/Voir PDF", file_bytes, file_name=f"{rec['nom']}.pdf")
                                # Preview PDF simple
                                base64_pdf = base64.b64encode(file_bytes).decode('utf-8')
                                pdf_display = f'<embed src="data:application/pdf;base64,{base64_pdf}" width="100%" height="400" type="application/pdf">'
                                st.markdown(pdf_display, unsafe_allow_html=True)
                            else:
                                # Affichage Image
                                st.image(file_bytes, use_container_width=True)
                    else:
                        st.write("Aucune photo ou PDF.")
