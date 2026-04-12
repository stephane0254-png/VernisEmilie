import streamlit as st
import pandas as pd
import base64
import requests

# Configuration des Secrets
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO_NAME = "votre_nom_utilisateur/votre_depot"
FILE_PATH = "data.csv"
BRANCH = "main"

def get_github_file():
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        content = base64.b64decode(r.json()["content"]).decode("utf-8")
        return pd.read_csv(pd.compat.StringIO(content)), r.json()["sha"]
    return pd.DataFrame(columns=["ID", "Catégorie", "Nom", "Description", "Photo"]), None

def save_to_github(df, sha):
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    csv_content = df.to_csv(index=False)
    encoded_content = base64.b64encode(csv_content.encode("utf-8")).decode("utf-8")
    
    data = {
        "message": "Mise à jour du stock beauté",
        "content": encoded_content,
        "branch": BRANCH,
        "sha": sha
    }
    requests.put(url, json=data, headers=headers)

# --- Logique de l'application ---
st.title("💅 Ma Collection Beauté")
df, file_sha = get_github_file()

# (Le reste du code pour l'interface reste identique)
# Lors de l'ajout d'un produit :
# save_to_github(updated_df, file_sha)

# Connexion au Google Sheet (via votre compte)
conn = st.connection("gsheets", type=GSheetsConnection)

# Chargement des données
def load_data():
    return conn.read(worksheet="Inventaire", ttl=0)

df = load_data()

st.title("💅 Gestion de Collection Beauté")

# Formulaire d'ajout dans la barre latérale
with st.sidebar:
    st.header("Ajouter un article")
    with st.form("add_form", clear_on_submit=True):
        cat = st.selectbox("Catégorie", ["Vernis", "Soins", "Accessoires"])
        nom = st.text_input("Nom du produit")
        desc = st.text_area("Description")
        photo = st.file_uploader("Prendre une photo", type=["jpg", "jpeg", "png"])
        
        submit = st.form_submit_button("Enregistrer")
        
        if submit and nom:
            # Conversion de l'image en Base64 pour le stockage
            img_str = ""
            if photo:
                img_str = base64.b64encode(photo.read()).decode()
            
            # Création de la nouvelle ligne
            new_row = pd.DataFrame([{
                "ID": len(df) + 1,
                "Catégorie": cat,
                "Nom": nom,
                "Description": desc,
                "Photo": img_str
            }])
            
            # Mise à jour du Sheet
            updated_df = pd.concat([df, new_row], ignore_index=True)
            conn.update(worksheet="Inventaire", data=updated_df)
            st.success("Produit ajouté !")
            st.rerun()

# Système d'onglets pour l'affichage
tabs = st.tabs(["Tous", "Vernis", "Soins", "Accessoires"])

for i, tab_name in enumerate(["Tous", "Vernis", "Soins", "Accessoires"]):
    with tabs[i]:
        if tab_name == "Tous":
            display_df = df
        else:
            display_df = df[df["Catégorie"] == tab_name]
            
        if display_df.empty:
            st.info("Aucun article ici.")
        else:
            # Affichage en grille
            cols = st.columns(3)
            for index, row in display_df.iterrows():
                with cols[index % 3]:
                    with st.container(border=True):
                        if row["Photo"]:
                            st.image(base64.b64decode(row["Photo"]), use_container_width=True)
                        st.subheader(row["Nom"])
                        st.caption(f"**{row['Catégorie']}**")
                        st.write(row["Description"])
                        
                        if st.button("Supprimer", key=f"del_{row['ID']}"):
                            df = df.drop(index)
                            conn.update(worksheet="Inventaire", data=df)
                            st.rerun()
