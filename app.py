import streamlit as st
import pandas as pd
import base64
import requests
from io import StringIO

# --- CONFIGURATION GITHUB ---
# Assurez-vous que GITHUB_TOKEN est bien configuré dans les Secrets de Streamlit Cloud
try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
except:
    st.error("Le secret 'GITHUB_TOKEN' est manquant dans les paramètres de Streamlit Cloud.")
    st.stop()

REPO = "stephane0254-png/VernisEmilie"
FILE_PATH = "data.csv"
URL = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"

st.set_page_config(page_title="Beauty Stock", page_icon="💅", layout="wide")

# --- STYLE CSS POUR L'INTERFACE ---
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
    </style>
    """, unsafe_allow_html=True)

# --- FONCTIONS DE GESTION GITHUB ---
def get_data():
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    res = requests.get(URL, headers=headers)
    if res.status_code == 200:
        content = base64.b64decode(res.json()["content"]).decode("utf-8")
        return pd.read_csv(StringIO(content)), res.json()["sha"]
    elif res.status_code == 404:
        st.warning("Fichier 'data.csv' non trouvé. Il sera créé lors du premier enregistrement.")
        return pd.DataFrame(columns=["ID", "Catégorie", "Nom", "Description", "Photo"]), None
    else:
        st.error(f"Erreur lors de la lecture des données (Code {res.status_code})")
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
    if res.status_code in [200, 201]:
        st.success("✅ Enregistrement réussi sur GitHub !")
        return True
    else:
        st.error(f"❌ Erreur de sauvegarde (Code {res.status_code})")
        st.info(f"Détails : {res.text}")
        return False

# --- LOGIQUE PRINCIPALE ---
df, current_sha = get_data()

# Barre latérale pour l'ajout
with st.sidebar:
    st.header("✨ Ajouter un article")
    with st.form("form_ajout", clear_on_submit=True):
        cat = st.selectbox("Catégorie", ["Vernis", "Soins", "Accessoires"])
        nom = st.text_input("Nom du produit")
        desc = st.text_area("Description / Couleur")
        file = st.file_uploader("Prendre une photo", type=["jpg", "jpeg", "png"])
        
        submit = st.form_submit_button("Enregistrer dans la collection")
        
        if submit:
            if nom:
                with st.spinner("Envoi des données vers GitHub..."):
                    img_str = ""
                    if file:
                        img_str = base64.b64encode(file.read()).decode()
                    
                    # Génération d'un ID unique sans points
                    new_id = str(pd.Timestamp.now().timestamp()).replace('.', '')
                    new_line = pd.DataFrame([{
                        "ID": new_id, 
                        "Catégorie": cat, 
                        "Nom": nom, 
                        "Description": desc, 
                        "Photo": img_str
                    }])
                    
                    updated_df = pd.concat([df, new_line], ignore_index=True)
                    if save_data(updated_df, current_sha):
                        st.rerun()
            else:
                st.warning("Veuillez donner au moins un nom au produit.")

# Affichage des résultats
st.title("💅 Ma Collection Beauté")
tabs = st.tabs(["Tous", "Vernis", "Soins", "Accessoires"])

for i, t in enumerate(["Tous", "Vernis", "Soins", "Accessoires"]):
    with tabs[i]:
        view_df = df if t == "Tous" else df[df["Catégorie"] == t]
        if view_df.empty:
            st.info("Aucun produit enregistré dans cette section.")
        else:
            cols = st.columns(4)
            for idx, (original_index, row) in enumerate(view_df.iterrows()):
                with cols[idx % 4]:
                    with st.container(border=True):
                        # Photo et Zoom
                        if str(row["Photo"]) != "nan" and row["Photo"] != "":
                            st.markdown('<div class="miniature-container">', unsafe_allow_html=True)
                            st.image(base64.b64decode(row["Photo"]), use_container_width=True)
                            st.markdown('</div>', unsafe_allow_html=True)
                            with st.expander("🔍 Voir en grand", key=f"exp_{t}_{row['ID']}_{idx}"):
                                st.image(base64.b64decode(row["Photo"]), use_container_width=False)
                        else:
                            st.info("Pas d'image")
                        
                        # Détails
                        st.subheader(row["Nom"])
                        st.write(f"**{row['Catégorie']}**")
                        st.write(row["Description"])
                        
                        # Bouton Supprimer
                        if st.button("🗑️ Supprimer", key=f"btn_{t}_{row['ID']}_{idx}"):
                            updated_df = df.drop(original_index)
                            save_data(updated_df, current_sha)
                            st.rerun()
