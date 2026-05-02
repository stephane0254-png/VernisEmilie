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
    st.error("Le secret 'GITHUB_TOKEN' est manquant dans Streamlit Cloud.")
    st.stop()

REPO = "stephane0254-png/VernisEmilie"
FILE_PATH = "data.csv"

st.set_page_config(page_title="Beauty Stock", page_icon="💅", layout="wide")

# --- INITIALISATION DE LA MÉMOIRE VIVE ---
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

# --- FONCTIONS GITHUB ---
# Modifiez la fonction get_github_file comme ceci pour voir le bug :
def get_github_file(path):
    url = f"https://api.github.com/repos/{REPO}/contents/{path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            content = base64.b64decode(res.json()["content"]).decode("utf-8")
            return content, res.json()["sha"]
        else:
            # Cette ligne affichera la raison précise du refus de GitHub
            st.error(f"GitHub Error: {res.status_code} - {res.json().get('message')}")
            return None, None
    except Exception as e:
        st.error(f"Erreur technique : {e}")
        return None, None

def get_data():
    content, sha = get_github_file(FILE_PATH)
    if content:
        if not content.strip() or len(content.strip().split('\n')) <= 1:
            return pd.DataFrame(columns=["ID", "Categorie", "Nom", "Description", "Couvrance", "Finition", "Saison", "Lieu", "Photo"]), sha, None
        try:
            df_load = pd.read_csv(StringIO(content), sep=',', skipinitialspace=True)
            df_load.columns = df_load.columns.str.strip()
            if "ID" in df_load.columns:
                df_load["ID"] = df_load["ID"].astype(str)
            return df_load, sha, None
        except:
            return pd.DataFrame(columns=["ID", "Categorie", "Nom", "Description", "Couvrance", "Finition", "Saison", "Lieu", "Photo"]), sha, None
    return None, None, "Erreur de connexion GitHub"

def load_list(filename, default_values):
    content, _ = get_github_file(filename)
    if content:
        try:
            df_list = pd.read_csv(StringIO(content))
            return df_list.iloc[:, 0].dropna().unique().tolist()
        except:
            return default_values
    return default_values

def save_data(df, sha):
    url = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    csv_content = df.to_csv(index=False, lineterminator='\n', encoding='utf-8')
    encoded = base64.b64encode(csv_content.encode("utf-8")).decode("utf-8")
    payload = {"message": "Mise à jour stock", "content": encoded, "sha": sha}
    res = requests.put(url, json=payload, headers=headers)
    return (True, res.json()["content"]["sha"]) if res.status_code in [200, 201] else (False, None)

# --- CHARGEMENT INITIAL ---
if 'stock_df' not in st.session_state:
    with st.spinner("Initialisation..."):
        loaded_df, loaded_sha, err = get_data()
        if err: st.error(err); st.stop()
        st.session_state['stock_df'] = loaded_df
        st.session_state['current_sha'] = loaded_sha
        st.session_state['list_cat'] = load_list("categorie.csv", ["Vernis", "Soins", "Accessoires"])
        st.session_state['list_couv'] = load_list("couvrance.csv", [])
        st.session_state['list_fin'] = load_list("finition.csv", [])
        st.session_state['list_sai'] = load_list("saison.csv", [])
        st.session_state['list_lieu'] = load_list("lieu.csv", [])

df = st.session_state['stock_df']

# --- INTERFACE ---
col_titre, col_refresh, col_sort = st.columns([4, 1, 1])
with col_titre:
    st.title("💅 Ma Collection Beauté")
with col_refresh:
    if st.button("🔄 Rafraîchir"):
        del st.session_state['stock_df']
        st.rerun()
with col_sort:
    sort_order = st.selectbox("Tri Nom", ["A-Z", "Z-A"], label_visibility="collapsed")

if not df.empty:
    ascending = (sort_order == "A-Z")
    df = df.sort_values(by="Nom", ascending=ascending, key=lambda col: col.str.lower())

# --- FORMULAIRE D'AJOUT (SIDEBAR) ---
with st.sidebar:
    st.header("✨ Ajouter un article")
    # Utilisation d'un container pour forcer le rafraîchissement lors du changement de catégorie
    cat_select = st.selectbox("Catégorie", st.session_state['list_cat'], key="add_cat_selector")
    
    with st.form("form_ajout", clear_on_submit=True):
        nom = st.text_input("Nom du produit")
        desc = st.text_area("Description")
        
        couv, fini, sais = "", "", ""
        # Affichage conditionnel STRICT
        if cat_select == "Vernis":
            couv = st.selectbox("Couvrance", st.session_state['list_couv'])
            fini = st.selectbox("Finition", st.session_state['list_fin'])
            sais = st.selectbox("Saison", st.session_state['list_sai'])
        
        lieu = st.selectbox("Lieu", st.session_state['list_lieu'])
        file = st.file_uploader("Photo", type=["jpg", "jpeg", "png"])
        submit = st.form_submit_button("🚀 ENREGISTRER")
        
        if submit:
            if nom:
                img_str = base64.b64encode(file.read()).decode() if file else ""
                new_line = pd.DataFrame([{
                    "ID": str(int(time.time())), "Categorie": cat_select, "Nom": nom, "Description": desc,
                    "Couvrance": couv, "Finition": fini, "Saison": sais, "Lieu": lieu, "Photo": img_str
                }])
                updated_df = pd.concat([st.session_state['stock_df'], new_line], ignore_index=True)
                success, new_sha = save_data(updated_df, st.session_state['current_sha'])
                if success:
                    st.session_state['stock_df'] = updated_df
                    st.session_state['current_sha'] = new_sha
                    st.success("Ajouté !"); st.rerun()
            else:
                st.error("Nom requis.")

# --- ZONE DE MODIFICATION ---
if st.session_state['editing_product'] is not None:
    p = st.session_state['editing_product']
    st.markdown('<div class="edit-container">', unsafe_allow_html=True)
    st.subheader(f"📝 Modifier : {p['Nom']}")
    
    col_e1, col_e2 = st.columns([2, 1])
    with col_e1:
        # On définit d'abord la catégorie pour la modification
        cat_list = st.session_state['list_cat']
        idx_cat = cat_list.index(p['Categorie']) if p['Categorie'] in cat_list else 0
        e_cat = st.selectbox("Catégorie", cat_list, index=idx_cat, key="edit_cat_selector")
        
        e_nom = st.text_input("Nom", value=p['Nom'])
        e_desc = st.text_area("Description", value=p['Description'])
        
        e_couv, e_fini, e_sais = "", "", ""
        if e_cat == "Vernis":
            c_l, f_l, s_l = st.session_state['list_couv'], st.session_state['list_fin'], st.session_state['list_sai']
            e_couv = st.selectbox("Couvrance", c_l, index=c_l.index(p['Couvrance']) if p['Couvrance'] in c_l else 0)
            e_fini = st.selectbox("Finition", f_l, index=f_l.index(p['Finition']) if p['Finition'] in f_l else 0)
            e_sais = st.selectbox("Saison", s_l, index=s_l.index(p['Saison']) if p['Saison'] in s_l else 0)
        
        l_l = st.session_state['list_lieu']
        e_lieu = st.selectbox("Lieu", l_l, index=l_l.index(p['Lieu']) if p['Lieu'] in l_l else 0)

    with col_e2:
        e_file = st.file_uploader("Changer photo", type=["jpg", "jpeg", "png"])
        if not e_file and p['Photo']: st.image(base64.b64decode(p['Photo']), width=150)

    c_save, c_cancel = st.columns(2)
    if c_save.button("✅ Enregistrer"):
        updated_df = st.session_state['stock_df'].copy()
        final_img = base64.b64encode(e_file.read()).decode() if e_file else p['Photo']
        updated_df.loc[updated_df['ID'].astype(str) == str(p['ID']), 
                       ["Categorie", "Nom", "Description", "Couvrance", "Finition", "Saison", "Lieu", "Photo"]] = \
                       [e_cat, e_nom, e_desc, e_couv, e_fini, e_sais, e_lieu, final_img]
        success, new_sha = save_data(updated_df, st.session_state['current_sha'])
        if success:
            st.session_state['stock_df'] = updated_df
            st.session_state['current_sha'] = new_sha
            st.session_state['editing_product'] = None
            st.rerun()
    if c_cancel.button("❌ Annuler"):
        st.session_state['editing_product'] = None
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- ZONE DE ZOOM ---
if st.session_state['zoomed_photo']:
    st.markdown('<div class="zoomed-container">', unsafe_allow_html=True)
    st.image(base64.b64decode(st.session_state['zoomed_photo']))
    if st.button("❌ Fermer le zoom"):
        st.session_state['zoomed_photo'] = None
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- AFFICHAGE ---
tabs = st.tabs(["Tous", "Vernis", "Soins", "Accessoires", "🔍 Recherche"])

def display_grid(data_to_show, key):
    if data_to_show.empty:
        st.info("Aucun article.")
    else:
        cols = st.columns(4)
        for idx, (original_idx, row) in enumerate(data_to_show.iterrows()):
            with cols[idx % 4]:
                with st.container(border=True):
                    if isinstance(row['Photo'], str) and len(row['Photo']) > 10:
                        st.markdown('<div class="miniature-container">', unsafe_allow_html=True)
                        st.image(base64.b64decode(row['Photo']), use_container_width=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                        if st.button("🔍", key=f"z_{key}_{row['ID']}"):
                            st.session_state['zoomed_photo'] = row['Photo']; st.rerun()
                    else:
                        st.info("📷 Pas de photo")
                    
                    st.subheader(row['Nom'])
                    if row['Categorie'] == "Vernis":
                        st.caption(f"{row['Couvrance']} | {row['Finition']} | {row['Saison']}")
                    st.write(f"📍 {row['Lieu']}")
                    if row['Description']: st.write(row['Description'])
                    
                    c1, c2 = st.columns(2)
                    if c1.button("📝", key=f"e_{key}_{row['ID']}"):
                        st.session_state['editing_product'] = row.to_dict(); st.rerun()
                    if c2.button("🗑️", key=f"d_{key}_{row['ID']}"):
                        new_df = st.session_state['stock_df'][st.session_state['stock_df']['ID'].astype(str) != str(row['ID'])]
                        ok, s = save_data(new_df, st.session_state['current_sha'])
                        if ok: st.session_state['stock_df'] = new_df; st.session_state['current_sha'] = s; st.rerun()

for i, t in enumerate(["Tous", "Vernis", "Soins", "Accessoires"]):
    with tabs[i]:
        display_grid(df if t == "Tous" else df[df["Categorie"] == t], t)

with tabs[4]:
    st.markdown('<div class="search-box">', unsafe_allow_html=True)
    q = st.text_input("Recherche globale", placeholder="Nom, fini, lieu...")
    if q:
        res = df[df.apply(lambda r: r.astype(str).str.contains(q, case=False).any(), axis=1)]
        display_grid(res, "search")
