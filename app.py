import streamlit as st
import pandas as pd
import base64
import requests
from io import StringIO

# --- CONFIGURATION GITHUB ---
# Assure-toi que GITHUB_TOKEN est bien dans tes Secrets sur Streamlit Cloud
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO = "TON_PSEUDO/TON_DEPOT" # <--- À MODIFIER ICI
FILE_PATH = "data.csv"
URL = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"

st.set_page_config(page_title="Beauty Stock", page_icon="💅", layout="wide")

# --- STYLE CSS POUR L'HARMONISATION ---
st.markdown("""
    <style>
    /* Force la taille des miniatures */
    .miniature-container img {
        height: 180px !important;
        object-fit: cover;
        border-radius: 8px;
    }
    
    /* Force la hauteur identique pour toutes les cartes */
    [data-testid="stVerticalBlockBorderWrapper"] {
        min-height: 480px;
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
    # Si le fichier n'existe pas, on crée la structure
    return pd.DataFrame(columns=["ID", "Catégorie", "Nom", "Description", "Photo"]), None

def save_data(df, sha):
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    csv_content = df.to_csv(index=False)
    encoded = base64.b64encode(csv_content.encode("utf-8")).decode("utf-8")
    payload = {
        "message": "Mise à jour stock beauté",
        "content": encoded,
        "sha": sha
    }
    res = requests.put(URL, json=payload, headers=headers)
    if res.status_code not in [200, 201]:
        st.error(f"Erreur de sauvegarde : {res.text}")

# --- CHARGEMENT DES DONNÉES ---
df, current_sha = get_data()

# --- BARRE LATÉRALE (AJOUT) ---
with st.sidebar:
    st.header("✨ Nouveau Produit")
    with st.form("ajout_produit", clear_on_submit=True):
        cat = st.selectbox("Catégorie", ["Vernis", "Soins", "Accessoires"])
        nom = st.text_input("Nom du produit")
        desc = st.text_area("Description / Couleur")
        file = st.file_uploader("Prendre une photo", type=["jpg", "jpeg", "png"])
        
        if st.form_submit_button("Enregistrer dans la collection"):
            if nom:
                img_str = ""
                if file:
                    img_str = base64.b64encode(file.read()).decode()
                
                # Création de l'ID unique basé sur le timestamp
                new_id = str(pd.Timestamp.now().timestamp()).replace('.', '')
                new_line = pd.DataFrame([{
                    "ID": new_id, 
                    "Catégorie": cat, 
                    "Nom": nom, 
                    "Description": desc, 
                    "Photo": img_str
                }])
                
                df = pd.concat([df, new_line], ignore_index=True)
                save_data(df, current_sha)
                st.success("Produit ajouté !")
                st.rerun()
            else:
                st.error("Le nom est obligatoire.")

# --- AFFICHAGE PRINCIPAL ---
st.title("💅 Ma Collection Beauté")

tabs = st.tabs(["Tous", "Vernis", "Soins", "Accessoires"])

for i, t in enumerate(["Tous", "Vernis", "Soins", "Accessoires"]):
    with tabs[i]:
        view_df = df if t == "Tous" else df[df["Catégorie"] == t]
        
        if view_df.empty:
            st.info("Aucun article enregistré pour le moment.")
        else:
            cols = st.columns(4) # 4 colonnes pour une meilleure vue d'ensemble
            for idx, (original_index, row) in enumerate(view_df.iterrows()):
                with cols[idx % 4]:
                    with st.container(border=True):
                        # Gestion de l'image
                        if str(row["Photo"]) != "nan" and row["Photo"] != "":
                            st.markdown('<div class="miniature-container">', unsafe_allow_html=True)
                            st.image(base64.b64decode(row["Photo"]), use_container_width=True)
                            st.markdown('</div>', unsafe_allow_html=True)
                            
                            with st.expander("🔍 Voir en grand", key=f"exp_{t}_{row['ID']}_{idx}"):
                                st.image(base64.b64decode(row["Photo"]), use_container_width=False)
                        else:
                            st.info("Pas de photo")

                        # Textes
                        st.subheader(row["Nom"])
                        st.write(f"**{row['Catégorie']}**")
                        st.write(f"*{row['Description']}*")
                        
                        # Bouton supprimer
                        if st.button("🗑️ Supprimer", key=f"btn_{t}_{row['ID']}_{idx}"):
                            df = df.drop(original_index)
                            save_data(df, current_sha)
                            st.rerun()
