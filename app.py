import streamlit as st
import pandas as pd
import base64
import requests
from io import StringIO
import time

# --- CONFIGURATION GITHUB ---
try:
    if "GITHUB_TOKEN" not in st.secrets:
        st.error("❌ Erreur : Le secret 'GITHUB_TOKEN' est introuvable dans les paramètres de Streamlit Cloud.")
        st.stop()
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
except Exception as e:
    st.error(f"❌ Erreur lors de la lecture des secrets : {e}")
    st.stop()

REPO = "stephane0254-png/VernisEmilie"
FILE_PATH = "data.csv"

st.set_page_config(page_title="Beauty Stock", page_icon="💅", layout="wide")

# --- STYLE CSS ---
st.markdown("""
    <style>
    h1 { font-size: 28px !important; padding-top: 0px !important; }
    .miniature-container img { height: 180px !important; object-fit: cover; border-radius: 8px; }
    .zoomed-container { text-align: center; margin-bottom: 20px; border: 2px solid #ff4b4b; border-radius: 15px; padding: 10px; background-color: #fff1f1; }
    .edit-container { background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #ff4b4b; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- FONCTIONS GITHUB (DIAGNOSTIC AMÉLIORÉ) ---
def get_github_file(path):
    url = f"https://api.github.com/repos/{REPO}/contents/{path}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    try:
        res = requests.get(url, headers=headers, timeout=10)
        
        if res.status_code == 200:
            data = res.json()
            content = base64.b64decode(data["content"]).decode("utf-8")
            return content, data["sha"], None
        elif res.status_code == 401:
            return None, None, "Token non valide (401). Vérifiez s'il a expiré sur GitHub."
        elif res.status_code == 404:
            return None, None, f"Fichier ou Dépôt introuvable (404). Vérifiez le nom : {REPO}/{path}"
        else:
            msg = res.json().get('message', 'Erreur inconnue')
            return None, None, f"Erreur GitHub {res.status_code} : {msg}"
            
    except requests.exceptions.RequestException as e:
        return None, None, f"Erreur de connexion réseau : {e}"

def get_data():
    content, sha, error = get_github_file(FILE_PATH)
    if error:
        return None, None, error
    
    if not content or not content.strip() or len(content.strip().split('\n')) <= 1:
        return pd.DataFrame(columns=["ID", "Categorie", "Nom", "Description", "Couvrance", "Finition", "Saison", "Lieu", "Photo"]), sha, None
    
    try:
        df_load = pd.read_csv(StringIO(content), sep=',', skipinitialspace=True)
        df_load.columns = df_load.columns.str.strip()
        if "ID" in df_load.columns:
            df_load["ID"] = df_load["ID"].astype(str)
        return df_load, sha, None
    except Exception as e:
        return None, None, f"Erreur de lecture CSV : {e}"

def load_list(filename, default_values):
    content, _, error = get_github_file(filename)
    if not error and content:
        try:
            df_list = pd.read_csv(StringIO(content))
            return df_list.iloc[:, 0].dropna().unique().tolist()
        except:
            return default_values
    return default_values

# --- CHARGEMENT INITIAL ---
if 'stock_df' not in st.session_state:
    with st.spinner("Vérification de la connexion GitHub..."):
        loaded_df, loaded_sha, err = get_data()
        if err:
            st.error(f"🚨 {err}")
            st.info("💡 Conseil : Vérifiez vos 'Secrets' dans Streamlit Cloud et assurez-vous que le token commence par 'ghp_'")
            st.stop()
        
        st.session_state['stock_df'] = loaded_df
        st.session_state['current_sha'] = loaded_sha
        st.session_state['list_cat'] = load_list("categorie.csv", ["Vernis", "Soins", "Accessoires"])
        st.session_state['list_couv'] = load_list("couvrance.csv", [])
        st.session_state['list_fin'] = load_list("finition.csv", [])
        st.session_state['list_sai'] = load_list("saison.csv", [])
        st.session_state['list_lieu'] = load_list("lieu.csv", [])

# On continue le reste du code normalement...
st.title("💅 Ma Collection Beauté")
df = st.session_state['stock_df']
st.write(f"Connexion réussie ! {len(df)} articles trouvés.")

# (Le reste du code d'affichage reste identique à ta version précédente)
