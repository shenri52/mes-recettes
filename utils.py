import streamlit as st
import requests
import json
import base64
import time
import datetime

# --- CONFIGURATION GITHUB ---
def get_github_config():
    """Centralise les secrets GitHub pour éviter de les répéter partout."""
    return {
        "token": st.secrets["GITHUB_TOKEN"],
        "owner": st.secrets["REPO_OWNER"],
        "repo": st.secrets["REPO_NAME"],
        "headers": {
            "Authorization": f"token {st.secrets['GITHUB_TOKEN']}",
            "Accept": "application/vnd.github.v3+json"
        }
    }
