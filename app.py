import streamlit as st
import pandas as pd
import base64
import requests
from io import StringIO
import time

# --- CONFIGURATION GITHUB ---
try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
except:
    st.error("Le secret 'GITHUB_TOKEN' est manquant.")
    st.stop()

REPO = "stephane0254-png/VernisEmilie"
FILE_PATH = "data.csv"

st.set_page_config(page_title="Beauty Stock", page_icon="💅", layout="wide")

# --- FONCTIONS GITHUB (VERSION OPTIMISÉE) ---
def get_github_file(path):
    url = f"https://api.github.com/repos/{REPO}/contents/{path}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    try:
        # Augmentation du timeout pour les gros fichiers
        res = requests.get(url, headers=headers, timeout=30)
        if res.status_code == 200:
            json_data = res.json()
            content = base64.b64decode(json_data["content"]).decode("utf-8")
            return content, json_data["sha"]
        else:
            return None, None
    except Exception as e:
        st.warning(f"Détail technique : {e}")
        return None, None

def get_data():
    content, sha = get_github_file(FILE_PATH)
    cols = ["ID", "Categorie", "Nom", "Description", "Couvrance", "Finition", "Saison", "Lieu", "Photo"]
    if content:
        if not content.strip() or len(content.strip().split('\n')) <= 1:
            return pd.DataFrame(columns=cols), sha, None
        try:
            # Lecture optimisée
            df_load = pd.read_csv(StringIO(content), sep=',', skipinitialspace=True, low_memory=False)
            df_load.columns = df_load.columns.str.strip()
            for c in cols:
                if c not in df_load.columns: df_load[c] = ""
            df_load["ID"] = df_load["ID"].astype(str)
            return df_load, sha, None
        except Exception as e:
            return pd.DataFrame(columns=cols), sha, f"Erreur de lecture CSV : {e}"
    return None, None, "Erreur de connexion GitHub (Fichier trop lourd ou Token expiré)"

# --- LE RESTE DU CODE RESTE IDENTIQUE ---
# (Gardez le reste de votre logique d'affichage, de tri et de sauvegarde ici)
# ...
