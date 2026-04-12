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
    st.error("Secret 'GITHUB_TOKEN' manquant.")
    st.stop()

REPO = "stephane0254-png/VernisEmilie"
FILE_PATH = "data.csv"

st.set_page_config(page_title="Beauty Stock", page_icon="💅", layout="wide")

if 'zoomed_photo' not in st.session_state:
    st.session_state['zoomed_photo'] = None

# --- STYLE ---
st.markdown("""
    <style>
    .miniature-container img { height: 180px !important; object-fit: cover; border-radius: 8px; }
    [data-testid="stVerticalBlockBorderWrapper"] { min-height: 500px; display: flex; flex-direction: column; justify-content: space-between; }
    </style>
    """, unsafe_allow_html=True)

# --- FONCTION DE LECTURE ROBUSTE ---
def get_data():
    url = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}?cb={random.randint(1,10000)}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "Cache-Control": "no-cache"
    }
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            content = base64.b64decode(res.json()["content"]).decode("utf-8")
            
            # DIAGNOSTIC : On affiche le contenu brut si l'app est vide (à retirer plus tard)
            if not content.strip():
                return pd.DataFrame(columns=["ID", "Catégorie", "Nom", "Description", "Photo"]), res.json()["sha"]
            
            # Tentative de lecture flexible (gère virgules ou points-virgules)
            try:
                df_load = pd.read_csv(StringIO(content), sep=None, engine='python')
            except:
                df_load = pd.read_csv(StringIO(content))

            # Nettoyage des noms de colonnes (enlève les espaces invisibles)
            df_load.columns = df_load.columns.str.strip()
            
            return df_load, res.json()["sha"]
        return pd.DataFrame(columns=["ID", "Catégorie", "Nom", "Description", "Photo"]), None
    except Exception as e:
        st.error(f"Erreur technique : {e}")
        return pd.DataFrame(columns=["ID", "Catégorie", "Nom", "Description", "Photo"]), None

def save_data(df, sha):
    url = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    csv_content = df.to_csv(index=False)
    encoded = base64.b64encode(csv_content.encode("utf-8")).decode("utf-8")
    payload = {"message": "Update", "content": encoded, "sha": sha}
    res = requests.put(url, json=payload, headers=headers)
    return res.status_code in [200, 201]

# --- CHARGEMENT ---
df, current_sha = get_data()

# --- INTERFACE ---
st.title("💅 Ma Collection Beauté")

# PETIT TABLEAU DE BORD DE DEBUG (À supprimer quand ça marche)
with st.expander("🛠️ Diagnostic Technique (Si rien ne s'affiche)"):
    st.write(f"Nombre de lignes détectées : {len(df)}")
    st.write("Colonnes trouvées :", list(df.columns))
    st.dataframe(df.head())

# --- FORMULAIRE ---
with st.sidebar:
    st.header("✨ Ajouter")
    with st.form("form_ajout", clear_on_submit=True):
        cat = st.selectbox("Catégorie", ["Vernis", "Soins", "Accessoires"])
        nom = st.text_input("Nom")
        desc = st.text_area("Description")
        file = st.file_uploader("Photo", type=["jpg", "jpeg", "png"])
        if st.form_submit_button("Enregistrer"):
            if nom:
                img_str = base64.b64encode(file.read()).decode() if file else ""
                new_id = str(int(time.time()))
                new_line = pd.DataFrame([{"ID": new_id, "Catégorie": cat, "Nom": nom, "Description": desc, "Photo": img_str}])
                
                f_df, f_sha = get_data()
                updated_df = pd.concat([f_df, new_line], ignore_index=True)
                if save_data(updated_df, f_sha):
                    st.success("Ok !")
                    time.sleep(1)
                    st.rerun()

# --- AFFICHAGE ---
if st.session_state['zoomed_photo']:
    st.image(base64.b64decode(st.session_state['zoomed_photo']))
    if st.button("Fermer"):
        st.session_state['zoomed_photo'] = None
        st.rerun()

tabs = st.tabs(["Tous", "Vernis", "Soins", "Accessoires"])
categories = ["Tous", "Vernis", "Soins", "Accessoires"]

for i, t in enumerate(categories):
    with tabs[i]:
        # Filtrage insensible à la casse pour plus de sécurité
        if t == "Tous":
            view_df = df
        else:
            view_df = df[df["Catégorie"].str.contains(t, case=False, na=False)]
            
        if view_df.empty:
            st.info(f"Aucun produit dans {t}")
        else:
            cols = st.columns(4)
            for idx, (original_index, row) in enumerate(view_df.iterrows()):
                with cols[idx % 4]:
                    with st.container(border=True):
                        if row.get("Photo"):
                            st.markdown('<div class="miniature-container">', unsafe_allow_html=True)
                            st.image(base64.b64decode(row["Photo"]), use_container_width=True)
                            st.markdown('</div>', unsafe_allow_html=True)
                            if st.button("🔍 Zoom", key=f"z_{t}_{idx}"):
                                st.session_state['zoomed_photo'] = row["Photo"]
                                st.rerun()
                        st.subheader(row["Nom"])
                        st.write(row["Description"])
                        if st.button("🗑️", key=f"b_{t}_{idx}"):
                            f_df, f_sha = get_data()
                            updated_df = f_df.drop(original_index)
                            save_data(updated_df, f_sha)
                            st.rerun()
