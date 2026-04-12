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

# --- STYLE CSS POUR HARMONISER LES CARTES ET LES IMAGES ---
st.markdown("""
    <style>
    /* Force la taille des miniatures */
    .miniature-container img {
        height: 180px !important;
        object-fit: cover;
        border-radius: 8px;
    }
    
    /* Force la hauteur identique pour toutes les cartes du stock */
    [data-testid="stVerticalBlockBorderWrapper"] {
        min-height: 450px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    </style>
    """, unsafe_allow_html=True)

# --- AFFICHAGE ---
tabs = st.tabs(["Tous", "Vernis", "Soins", "Accessoires"])
for i, t in enumerate(["Tous", "Vernis", "Soins", "Accessoires"]):
    with tabs[i]:
        view_df = df if t == "Tous" else df[df["Catégorie"] == t]
        
        cols = st.columns(3)
        
        for idx, (idx_row, row) in enumerate(view_df.iterrows()):
            with cols[idx % 3]:
                with st.container(border=True):
                    # Affichage de la miniature
                    if row["Photo"]:
                        st.markdown('<div class="miniature-container">', unsafe_allow_html=True)
                        st.image(base64.b64decode(row["Photo"]), use_container_width=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        # Agrandissement en taille normale
                        with st.expander("🔍 Voir en grand"):
                            # Ici, on n'utilise pas le container CSS pour laisser la taille normale
                            st.image(base64.b64decode(row["Photo"]), use_container_width=False, caption=row["Nom"])
                    
                    # Informations du produit
                    st.subheader(row["Nom"])
                    st.write(f"**Catégorie :** {row['Catégorie']}")
                    st.write(row["Description"])
                    
                    # Bouton supprimer en bas de carte
                    if st.button("🗑️ Supprimer", key=f"del_{t}_{row['ID']}"):
                        df = df[df["ID"] != row["ID"]]
                        save_data(df, current_sha)
                        st.rerun()

# --- AFFICHAGE ---
tabs = st.tabs(["Tous", "Vernis", "Soins", "Accessoires"])
for i, t in enumerate(["Tous", "Vernis", "Soins", "Accessoires"]):
    with tabs[i]:
        view_df = df if t == "Tous" else df[df["Catégorie"] == t]
        
        # On crée une grille de 3 colonnes pour plus de lisibilité
        cols = st.columns(3)
        
        for idx, (idx_row, row) in enumerate(view_df.iterrows()):
            with cols[idx % 3]:
                with st.container(border=True):
                    if row["Photo"]:
                        # Affichage formaté (fixe)
                        st.markdown('<div class="fixed-image-container">', unsafe_allow_html=True)
                        st.image(base64.b64decode(row["Photo"]), use_container_width=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        # Bouton pour agrandir
                        with st.expander("🔍 Voir en grand"):
                            st.image(base64.b64decode(row["Photo"]), use_container_width=True)
                    
                    st.subheader(row["Nom"])
                    st.caption(f"ID: {str(row['ID'])[:8]}") # Petit rappel de l'ID
                    st.write(row["Description"])
                    
                    # Bouton supprimer avec clé unique
                    if st.button("🗑️ Supprimer", key=f"del_{t}_{row['ID']}"):
                        df = df[df["ID"] != row["ID"]]
                        save_data(df, current_sha)
                        st.rerun()
