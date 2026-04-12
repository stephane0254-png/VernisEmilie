import streamlit as st
import pandas as pd
import base64
import requests
from io import StringIO
import time
import random

# --- CONFIGURATION GITHUB ---
try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
except:
    st.error("Le secret 'GITHUB_TOKEN' est manquant dans Streamlit Cloud.")
    st.stop()

REPO = "stephane0254-png/VernisEmilie"
FILE_PATH = "data.csv"

st.set_page_config(page_title="Beauty Stock", page_icon="💅", layout="wide")

if 'zoomed_photo' not in st.session_state:
    st.session_state['zoomed_photo'] = None

# --- STYLE CSS ---
st.markdown("""
    <style>
    .miniature-container img { height: 180px !important; object-fit: cover; border-radius: 8px; }
    [data-testid="stVerticalBlockBorderWrapper"] { min-height: 500px; display: flex; flex-direction: column; justify-content: space-between; }
    .zoomed-container { text-align: center; margin-bottom: 20px; border: 2px solid #ff4b4b; border-radius: 15px; padding: 10px; background-color: #fff1f1; }
    </style>
    """, unsafe_allow_html=True)

# --- FONCTIONS GITHUB ---
def get_data():
    url = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}?cb={random.randint(1,10000)}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            content = base64.b64decode(res.json()["content"]).decode("utf-8")
            if not content.strip() or len(content.split('\n')) <= 1:
                return pd.DataFrame(columns=["ID", "Catégorie", "Nom", "Description", "Photo"]), res.json()["sha"]
            
            df_load = pd.read_csv(StringIO(content), sep=',', skipinitialspace=True)
            df_load.columns = df_load.columns.str.strip()
            return df_load, res.json()["sha"]
        return pd.DataFrame(columns=["ID", "Catégorie", "Nom", "Description", "Photo"]), None
    except:
        return pd.DataFrame(columns=["ID", "Catégorie", "Nom", "Description", "Photo"]), None

def save_data(df, sha):
    url = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    csv_content = df.to_csv(index=False, lineterminator='\n', encoding='utf-8')
    encoded = base64.b64encode(csv_content.encode("utf-8")).decode("utf-8")
    payload = {"message": "Mise à jour stock", "content": encoded, "sha": sha}
    res = requests.put(url, json=payload, headers=headers)
    return res.status_code in [200, 201]

# --- CHARGEMENT ---
df, current_sha = get_data()

# --- FORMULAIRE ---
with st.sidebar:
    st.header("✨ Ajouter un article")
    with st.form("form_ajout", clear_on_submit=True):
        cat = st.selectbox("Catégorie", ["Vernis", "Soins", "Accessoires"])
        nom = st.text_input("Nom du produit")
        desc = st.text_area("Description")
        file = st.file_uploader("Photo", type=["jpg", "jpeg", "png"])
        submit = st.form_submit_button("🚀 ENREGISTRER")
        
        if submit:
            if nom:
                img_str = ""
                if file:
                    img_str = base64.b64encode(file.read()).decode()
                
                new_id = str(int(time.time()))
                new_line = pd.DataFrame([{"ID": new_id, "Catégorie": cat, "Nom": nom, "Description": desc, "Photo": img_str}])
                
                f_df, f_sha = get_data()
                updated_df = pd.concat([f_df, new_line], ignore_index=True)
                
                if save_data(updated_df, f_sha):
                    st.success("Produit ajouté !")
                    time.sleep(1)
                    st.rerun()

# --- AFFICHAGE ZOOM ---
if st.session_state['zoomed_photo']:
    st.markdown('<div class="zoomed-container">', unsafe_allow_html=True)
    try:
        st.image(base64.b64decode(st.session_state['zoomed_photo']), use_container_width=False)
    except:
        st.error("Impossible d'afficher cette image.")
    if st.button("❌ Fermer le zoom"):
        st.session_state['zoomed_photo'] = None
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- GRILLE PRODUITS ---
st.title("💅 Ma Collection Beauté")
tabs = st.tabs(["Tous", "Vernis", "Soins", "Accessoires"])

for i, t in enumerate(["Tous", "Vernis", "Soins", "Accessoires"]):
    with tabs[i]:
        view_df = df if t == "Tous" else df[df["Catégorie"] == t]
        
        if view_df.empty:
            st.info(f"Aucun produit trouvé dans '{t}'")
        else:
            cols = st.columns(4)
            for idx, (original_index, row) in enumerate(view_df.iterrows()):
                with cols[idx % 4]:
                    with st.container(border=True):
                        # VÉRIFICATION DE LA PHOTO AVANT DÉCODAGE
                        photo_data = row.get("Photo")
                        has_photo = isinstance(photo_data, str) and len(photo_data) > 10
                        
                        if has_photo:
                            try:
                                st.markdown('<div class="miniature-container">', unsafe_allow_html=True)
                                st.image(base64.b64decode(photo_data), use_container_width=True)
                                st.markdown('</div>', unsafe_allow_html=True)
                                if st.button("🔍 Zoom", key=f"z_{t}_{idx}"):
                                    st.session_state['zoomed_photo'] = photo_data
                                    st.rerun()
                            except:
                                st.warning("Image corrompue")
                        else:
                            st.info("📷 Pas de photo")
                        
                        st.subheader(row["Nom"])
                        st.write(row["Description"])
                        
                        if st.button("🗑️", key=f"b_{t}_{idx}"):
                            f_df, f_sha = get_data()
                            updated_df = f_df[f_df["ID"].astype(str) != str(row["ID"])]
                            save_data(updated_df, f_sha)
                            st.rerun()
