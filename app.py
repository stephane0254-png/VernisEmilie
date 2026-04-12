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

# --- INITIALISATION DE LA MÉMOIRE VIVE (OPTIMISATION) ---
if 'zoomed_photo' not in st.session_state:
    st.session_state['zoomed_photo'] = None
if 'editing_product' not in st.session_state:
    st.session_state['editing_product'] = None

# --- STYLE CSS ---
st.markdown("""
    <style>
    h1 { font-size: 28px !important; padding-top: 0px !important; }
    .miniature-container img { height: 180px !important; object-fit: cover; border-radius: 8px; }
    [data-testid="stVerticalBlockBorderWrapper"] { min-height: 520px; display: flex; flex-direction: column; justify-content: space-between; }
    .zoomed-container { text-align: center; margin-bottom: 20px; border: 2px solid #ff4b4b; border-radius: 15px; padding: 10px; background-color: #fff1f1; }
    .edit-container { background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #ff4b4b; margin-bottom: 20px; }
    .search-box { background-color: #f9f9f9; padding: 20px; border-radius: 10px; margin-bottom: 20px; border: 1px solid #ddd; }
    </style>
    """, unsafe_allow_html=True)

# --- FONCTIONS GITHUB OPTIMISÉES ---
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
    
    # OPTIMISATION : On récupère le nouveau SHA directement après l'enregistrement
    if res.status_code in [200, 201]:
        return True, res.json()["content"]["sha"]
    return False, None

# --- CHARGEMENT UNIQUE (OPTIMISATION) ---
# On ne télécharge depuis GitHub que si la mémoire est vide
if 'stock_df' not in st.session_state:
    with st.spinner("Chargement des données..."):
        st.session_state['stock_df'], st.session_state['current_sha'] = get_data()

# On utilise les données en mémoire
df = st.session_state['stock_df']
current_sha = st.session_state['current_sha']

# --- FORMULAIRE D'AJOUT ---
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
                img_str = base64.b64encode(file.read()).decode() if file else ""
                new_id = str(int(time.time()))
                new_line = pd.DataFrame([{"ID": new_id, "Catégorie": cat, "Nom": nom, "Description": desc, "Photo": img_str}])
                
                # Mise à jour de la mémoire locale
                updated_df = pd.concat([st.session_state['stock_df'], new_line], ignore_index=True)
                
                # Sauvegarde rapide (sans re-téléchargement)
                success, new_sha = save_data(updated_df, st.session_state['current_sha'])
                if success:
                    st.session_state['stock_df'] = updated_df
                    st.session_state['current_sha'] = new_sha
                    st.success("Produit ajouté !")
                    st.rerun()

# --- INTERFACE PRINCIPALE ---
col_titre, col_refresh = st.columns([5, 1])
with col_titre:
    st.title("💅 Ma Collection Beauté")
with col_refresh:
    if st.button("🔄 Rafraîchir"):
        # Bouton manuel pour forcer la synchronisation avec GitHub si besoin
        st.session_state['stock_df'], st.session_state['current_sha'] = get_data()
        st.rerun()

# 1. ZONE DE MODIFICATION
if st.session_state['editing_product'] is not None:
    prod = st.session_state['editing_product']
    st.markdown('<div class="edit-container">', unsafe_allow_html=True)
    st.subheader(f"📝 Modifier : {prod['Nom']}")
    
    col_edit1, col_edit2 = st.columns([2, 1])
    with col_edit1:
        new_cat = st.selectbox("Catégorie", ["Vernis", "Soins", "Accessoires"], 
                               index=["Vernis", "Soins", "Accessoires"].index(prod['Catégorie']), key="edit_cat")
        new_nom = st.text_input("Nom", value=prod['Nom'], key="edit_nom")
        new_desc = st.text_area("Description", value=prod['Description'], key="edit_desc")
    
    with col_edit2:
        new_file = st.file_uploader("Remplacer la photo", type=["jpg", "jpeg", "png"], key="edit_file")
        if not new_file and isinstance(prod['Photo'], str) and len(prod['Photo']) > 10:
            st.image(base64.b64decode(prod['Photo']), width=150)
    
    btn_save, btn_cancel = st.columns(2)
    if btn_save.button("✅ Enregistrer", use_container_width=True):
        updated_df = st.session_state['stock_df'].copy()
        final_photo = base64.b64encode(new_file.read()).decode() if new_file else prod['Photo']
            
        updated_df.loc[updated_df['ID'].astype(str) == str(prod['ID']), ['Catégorie', 'Nom', 'Description', 'Photo']] = [new_cat, new_nom, new_desc, final_photo]
        
        success, new_sha = save_data(updated_df, st.session_state['current_sha'])
        if success:
            st.session_state['stock_df'] = updated_df
            st.session_state['current_sha'] = new_sha
            st.session_state['editing_product'] = None
            st.success("Modifications enregistrées !")
            st.rerun()
            
    if btn_cancel.button("❌ Annuler", use_container_width=True):
        st.session_state['editing_product'] = None
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# 2. ZONE DE ZOOM
if st.session_state['zoomed_photo']:
    st.markdown('<div class="zoomed-container">', unsafe_allow_html=True)
    try:
        st.image(base64.b64decode(st.session_state['zoomed_photo']), use_container_width=False)
    except:
        st.error("Image illisible")
    if st.button("❌ Fermer le zoom"):
        st.session_state['zoomed_photo'] = None
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# 3. ONGLETS ET RECHERCHE
tabs = st.tabs(["Tous", "Vernis", "Soins", "Accessoires", "🔍 Recherche"])

def display_grid(data_to_show, tab_key):
    if data_to_show.empty:
        st.info("Aucun produit ne correspond.")
    else:
        cols = st.columns(4)
        for idx, (original_index, row) in enumerate(data_to_show.iterrows()):
            with cols[idx % 4]:
                with st.container(border=True):
                    photo_data = row.get("Photo")
                    has_photo = isinstance(photo_data, str) and len(photo_data) > 10
                    
                    if has_photo:
                        st.markdown('<div class="miniature-container">', unsafe_allow_html=True)
                        st.image(base64.b64decode(photo_data), use_container_width=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                        if st.button("🔍 Zoom", key=f"z_{tab_key}_{row['ID']}"):
                            st.session_state['zoomed_photo'] = photo_data
                            st.rerun()
                    else:
                        st.info("📷 Pas de photo")
                    
                    st.subheader(row["Nom"])
                    st.caption(f"Catégorie: {row['Catégorie']}")
                    st.write(row["Description"])
                    
                    col_act1, col_act2 = st.columns(2)
                    if col_act1.button("📝 Modifier", key=f"ed_{tab_key}_{row['ID']}"):
                        st.session_state['editing_product'] = row.to_dict()
                        st.rerun()
                    if col_act2.button("🗑️", key=f"del_{tab_key}_{row['ID']}"):
                        updated_df = st.session_state['stock_df'][st.session_state['stock_df']["ID"].astype(str) != str(row["ID"])]
                        success, new_sha = save_data(updated_df, st.session_state['current_sha'])
                        if success:
                            st.session_state['stock_df'] = updated_df
                            st.session_state['current_sha'] = new_sha
                            st.rerun()

# Remplissage des onglets
for i, t in enumerate(["Tous", "Vernis", "Soins", "Accessoires"]):
    with tabs[i]:
        view_df = df if t == "Tous" else df[df["Catégorie"] == t]
        display_grid(view_df, t)

# Logique de l'onglet RECHERCHE
with tabs[4]:
    st.markdown('<div class="search-box">', unsafe_allow_html=True)
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        search_name = st.text_input("Rechercher par nom", placeholder="Ex: Vernis Rouge...")
    with col_s2:
        search_cat = st.multiselect("Filtrer par catégorie", ["Vernis", "Soins", "Accessoires"])
    st.markdown('</div>', unsafe_allow_html=True)

    search_df = df.copy()
    if search_name:
        search_df = search_df[search_df['Nom'].str.contains(search_name, case=False, na=False)]
    if search_cat:
        search_df = search_df[search_df['Catégorie'].isin(search_cat)]

    display_grid(search_df, "search")
