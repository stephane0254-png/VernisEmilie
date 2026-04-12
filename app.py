import streamlit as st
import pandas as pd
import base64
import requests
from io import StringIO

# --- CONFIGURATION GITHUB ---
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO = "stephane0254-png/VernisEmilie"
FILE_PATH = "data.csv"
URL = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"

st.set_page_config(page_title="Beauty Stock", page_icon="💅")

def get_data():
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    res = requests.get(URL, headers=headers)
    if res.status_code == 200:
        content = base64.b64decode(res.json()["content"]).decode("utf-8")
        return pd.read_csv(StringIO(content)), res.json()["sha"]
    return pd.DataFrame(columns=["ID", "Catégorie", "Nom", "Description", "Photo"]), None

def save_data(df, sha):
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    csv_content = df.to_csv(index=False)
    encoded = base64.b64encode(csv_content.encode("utf-8")).decode("utf-8")
    payload = {
        "message": "Mise à jour stock",
        "content": encoded,
        "sha": sha
    }
    requests.put(URL, json=payload, headers=headers)

# --- INTERFACE ---
st.title("💅 Ma Collection Beauté")
df, current_sha = get_data()

with st.sidebar:
    st.header("Ajouter un article")
    cat = st.selectbox("Catégorie", ["Vernis", "Soins", "Accessoires"])
    nom = st.text_input("Nom")
    desc = st.text_area("Description")
    file = st.file_uploader("Photo", type=["jpg", "png"])
    
    if st.button("Enregistrer"):
        img_str = ""
        if file:
            img_str = base64.b64encode(file.read()).decode()
        
        new_line = pd.DataFrame([{"ID": str(pd.Timestamp.now().timestamp()), "Catégorie": cat, "Nom": nom, "Description": desc, "Photo": img_str}])
        df = pd.concat([df, new_line], ignore_index=True)
        save_data(df, current_sha)
        st.success("Enregistré !")
        st.rerun()

# --- AFFICHAGE ---
tabs = st.tabs(["Tous", "Vernis", "Soins", "Accessoires"])
for i, t in enumerate(["Tous", "Vernis", "Soins", "Accessoires"]):
    with tabs[i]:
        view_df = df if t == "Tous" else df[df["Catégorie"] == t]
        cols = st.columns(2)
        
        # On utilise une boucle avec index pour la mise en page
        for idx, (idx_row, row) in enumerate(view_df.iterrows()):
            with cols[idx % 2]:
                with st.container(border=True):
                    if row["Photo"]:
                        st.image(base64.b64decode(row["Photo"]))
                    st.subheader(row["Nom"])
                    st.write(row["Description"])
                    
                    # LA CORRECTION EST ICI : 
                    # On ajoute 't' (le nom de l'onglet) dans la key pour qu'elle soit unique
                    if st.button("Supprimer", key=f"del_{t}_{row['ID']}"):
                        df = df[df["ID"] != row["ID"]]
                        save_data(df, current_sha)
                        st.rerun()
