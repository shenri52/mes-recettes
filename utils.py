import streamlit as st

def get_github_config():
    """
    Centralise les identifiants et les headers pour l'API GitHub.
    À utiliser dans tous les fichiers qui contactent le dépôt.
    """
    return {
        "owner": st.secrets["REPO_OWNER"],
        "repo": st.secrets["REPO_NAME"],
        "token": st.secrets["GITHUB_TOKEN"],
        "headers": {
            "Authorization": f"token {st.secrets['GITHUB_TOKEN']}",
            "Accept": "application/vnd.github.v3+json"
        }
    }
