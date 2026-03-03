import streamlit as st
import requests
import base64

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

def afficher():
    st.title("Test Affichage Direct")
    conf = config_github()
    
    # 1. Lister les fichiers JSON
    url = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/data/recettes"
    res = requests.get(url, headers=conf['headers'])
    
    if res.status_code == 200:
        fichiers = res.json()
        for f in fichiers:
            if f['name'].endswith('.json'):
                # 2. Lire le contenu du JSON
                r_res = requests.get(f['download_url'])
                data = r_res.json()
                
                st.write(f"### Recette : {data.get('nom')}")
                
                # Vérifier la présence de 'images'
                médias = data.get('images', [])
                if not médias and data.get('image'): médias = [data.get('image')]
                
                if médias:
                    st.write(f"📸 {len(médias)} image(s) trouvée(s) dans le JSON")
                    for path in médias:
                        # 3. Charger l'image via l'API
                        p = path.strip("/").replace("data/data/", "data/")
                        if not p.startswith("data/"): p = f"data/{p}"
                        
                        api_url = f"https://api.github.com/repos/{conf['owner']}/{conf['repo']}/contents/{p}"
                        img_res = requests.get(api_url, headers=conf['headers'])
                        
                        if img_res.status_code == 200:
                            img_b64 = img_res.json().get('content')
                            st.image(base64.b64decode(img_b64), caption=p)
                        else:
                            st.error(f"GitHub ne trouve pas le fichier image : {p}")
                else:
                    st.warning("Le JSON de cette recette ne contient aucun lien d'image.")
                    st.json(data) # Affiche le contenu pour voir ce qui manque
    else:
        st.error(f"Erreur connexion GitHub : {res.status_code}")
