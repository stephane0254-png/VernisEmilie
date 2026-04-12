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
    st.error("Le secret 'GITHUB_TOKEN' est manquant dans les paramètres de Streamlit Cloud.")
    st.stop()

REPO = "stephane0254-png/VernisEmilie"
FILE_PATH = "data.csv"
URL = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"

st.set_page_config(page_title="Beauty Stock", page_icon="💅", layout="wide")

if 'zoomed_photo' not in st.session_state:
    st.session_state['zoomed_photo'] = None

# --- STYLE CSS ---
st.markdown("""
    <style>
    .miniature-container img {
        height: 180px !important;
        object-fit: cover;
        border-radius: 8px;
    }
    [data-testid="stVerticalBlockBorderWrapper"] {
        min-height: 500px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .zoomed-container {
        text-align: center;
        margin-bottom: 20px;
        border: 2px solid #ff4b4b;
        border-radius: 15px;
        padding: 10px;
        background-color: #fff1f1;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FONCTIONS GITHUB ---
@st.cache_data(ttl=1) # On force Streamlit à ne pas garder les données en cache plus d'une seconde
def get_data():
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Cache-Control": "no-cache"
    }
    try:
        res = requests.get(URL, headers=headers)
        if res.status_code == 200:
            content = base64.b64decode(res.json()["content"]).decode("utf-8")
            return pd.read_csv(StringIO(content)), res.json()["sha"]
        return pd.DataFrame(columns=["ID", "Catégorie", "Nom", "Description", "Photo"]), None
    except:
        return pd.DataFrame(columns=["ID", "Catégorie", "Nom", "Description", "Photo"]), None

def save_data(df, sha):
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    csv_content = df.to_csv(index=False)
    encoded = base64.b64encode(csv_content.encode("utf-8")).decode("utf-8")
    payload = {
        "message": "Mise à jour du catalogue",
        "content": encoded
    }
    if sha:
        payload["sha"] = sha
        
    res = requests.put(URL, json=payload, headers=headers)
    return res.status_code in [200, 201]

# --- LOGIQUE ---
df, current_sha = get_data()

with st.sidebar:
    st.header("✨ Ajouter un article")
    with st.form("form_ajout", clear_on_submit=True):
        cat = st.selectbox("Catégorie", ["Vernis", "Soins", "Accessoires"])
        nom = st.text_input("Nom du produit")
        desc = st.text_area("Description / Couleur")
        file = st.file_uploader("Photo", type=["jpg", "jpeg", "png"])
        submit = st.form_submit_button("Enregistrer")
        
        if submit and nom:
            with st.spinner("Enregistrement..."):
                img_str = ""
                if file:
                    img_str = base64.b64encode(file.read()).decode()
                
                new_id = str(pd.Timestamp.now().timestamp()).replace('.', '')
                new_line = pd.DataFrame([{"ID": new_id, "Catégorie": cat, "Nom": nom, "Description": desc, "Photo": img_str}])
                
                updated_df = pd.concat([df, new_line], ignore_index=True)
                if save_data(updated_df, current_sha):
                    st.success("Enregistré !")
                    time.sleep(1) # Petit temps d'attente pour GitHub
                    st.cache_data.clear() # On vide le cache pour forcer la relecture
                    st.rerun()

# --- AFFICHAGE ---
st.title("💅 Ma Collection Beauté")

if st.session_state['zoomed_photo']:
    st.markdown('<div class="zoomed-container">', unsafe_allow_html=True)
    st.image(base64.b64decode(st.session_state['zoomed_photo']), use_container_width=False)
    if st.button("❌ Fermer"):
        st.session_state['zoomed_photo'] = None
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

tabs = st.tabs(["Tous", "Vernis", "Soins", "Accessoires"])
for i, t in enumerate(["Tous", "Vernis", "Soins", "Accessoires"]):
    with tabs[i]:
        view_df = df if t == "Tous" else df[df["Catégorie"] == t]
        if view_df.empty:
            st.info("Aucun produit enregistré ici.")
        else:
            cols = st.columns(4)
            for idx, (original_index, row) in enumerate(view_df.iterrows()):
                with cols[idx % 4]:
                    with st.container(border=True):
                        if str(row["Photo"]) != "nan" and row["Photo"] != "":
                            st.markdown('<div class="miniature-container">', unsafe_allow_html=True)
                            st.image(base64.b64decode(row["Photo"]), use_container_width=True)
                            st.markdown('</div>', unsafe_allow_html=True)
                            if st.button("🔍 Voir plus grand", key=f"z_{t}_{row['ID']}_{idx}"):
                                st.session_state['zoomed_photo'] = row["Photo"]
                                st.rerun()
                        
                        st.subheader(row["Nom"])
                        st.write(f"**{row['Catégorie']}**")
                        st.write(row["Description"])
                        
                        if st.button("🗑️ Supprimer", key=f"b_{t}_{row['ID']}_{idx}"):
                            updated_df = df.drop(original_index)
                            if save_data(updated_df, current_sha):
                                st.cache_data.clear()
                                st.rerun()
