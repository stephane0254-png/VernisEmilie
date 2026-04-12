import streamlit as st
import pandas as pd
import base64
import requests
from io import StringIO

# --- CONFIGURATION GITHUB ---
# Assurez-vous que GITHUB_TOKEN est bien dans vos Secrets sur Streamlit Cloud
try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
except:
    st.error("Le secret 'GITHUB_TOKEN' est manquant dans les paramètres de Streamlit Cloud.")
    st.stop()

REPO = "stephane0254-png/VernisEmilie"
FILE_PATH = "data.csv"
URL = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"

st.set_page_config(page_title="Beauty Stock", page_icon="💅", layout="wide")

# Initialisation du session_state pour le zoom de photo
if 'zoomed_photo' not in st.session_state:
    st.session_state['zoomed_photo'] = None

# --- STYLE CSS POUR L'INTERFACE ---
st.markdown("""
    <style>
    /* Force la taille des miniatures */
    .miniature-container img {
        height: 180px !important;
        object-fit: cover;
        border-radius: 8px;
        cursor: pointer; /* Montre que c'est cliquable */
    }
    
    /* Force la hauteur identique pour toutes les cartes */
    [data-testid="stVerticalBlockBorderWrapper"] {
        min-height: 500px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    
    /* Style pour la zone de photo zoomée */
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

# --- FONCTIONS DE GESTION GITHUB ---
def get_data():
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    try:
        res = requests.get(URL, headers=headers)
        if res.status_code == 200:
            content = base64.b64decode(res.json()["content"]).decode("utf-8")
            return pd.read_csv(StringIO(content)), res.json()["sha"]
        elif res.status_code == 404:
            return pd.DataFrame(columns=["ID", "Catégorie", "Nom", "Description", "Photo"]), None
        else:
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
    if res.status_code not in [200, 201]:
        st.error(f"❌ Erreur de sauvegarde (Code {res.status_code})")
        st.info(f"Détails : {res.text}")
        return False
    else:
        st.success("✅ Enregistrement réussi sur GitHub !")
        return True

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

# --- ZONE D'AFFICHAGE DE LA PHOTO ZOOMÉE (IMMÉDIAT) ---
if st.session_state['zoomed_photo']:
    # J'utilise une clé unique pour le bouton de fermeture
    st.markdown('<div class="zoomed-container">', unsafe_allow_html=True)
    
    # Affichage de la photo en grand
    st.image(base64.b64decode(st.session_state['zoomed_photo']), use_container_width=False, caption="Affichage grand format")
    
    # Bouton pour fermer le zoom
    if st.button("❌ Fermer le grand format", key="close_zoom"):
        st.session_state['zoomed_photo'] = None
        st.rerun()
        
    st.markdown('</div>', unsafe_allow_html=True)


# --- GRILLE DES PRODUITS ---
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
                        
                        # Partie Photo cliquable
                        if str(row["Photo"]) != "nan" and row["Photo"] != "":
                            # Miniature
                            st.markdown('<div class="miniature-container">', unsafe_allow_html=True)
                            st.image(base64.b64decode(row["Photo"]), use_container_width=True)
                            st.markdown('</div>', unsafe_allow_html=True)
                            
                            # BOUTON ZOOM IMMÉDIAT
                            # On utilise le session_state pour stocker la photo cliquée
                            if st.button("🔍 Voir plus grand", key=f"zoom_{t}_{row['ID']}_{idx}"):
                                st.session_state['zoomed_photo'] = row["Photo"]
                                st.rerun() # Recharge immédiatement la page pour afficher le zoom en haut
                        else:
                            st.info("Pas d'image")
                        
                        # Détails du produit
                        st.subheader(row["Nom"])
                        st.write(f"**{row['Catégorie']}**")
                        st.write(row["Description"])
                        
                        # Bouton Supprimer
                        if st.button("🗑️ Supprimer", key=f"btn_{t}_{row['ID']}_{idx}"):
                            updated_df = df.drop(original_index)
                            save_data(updated_df, current_sha)
                            st.rerun()
