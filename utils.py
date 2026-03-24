import streamlit as st
import requests, json, base64, time

# --- CONFIGURATION GITHUB ---
def config_github():
    return {
      "headers": {"Authorization": f"token {st.secrets['GITHUB_TOKEN']}",
                  "Accept": "application/vnd.github.v3+json"},
      "owner": st.secrets["REPO_OWNER"],
      "repo": st.secrets["REPO_NAME"]
    }
