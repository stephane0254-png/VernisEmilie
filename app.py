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

# --- INITIALISATION DES VARIABLES DE SESSION ---
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
    </style>
    """, unsafe_allow_html=True)

# --- FONCTIONS GITHUB (MODE HAUTE CAPACITÉ) ---
def get_github_file_large(path):
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    url_info = f"https://api.github.com/repos/{REPO}/contents/{path}"
    try:
        res_info = requests.get(url_info, headers=headers, timeout=20)
        if res_info.status_code == 200:
            file_sha = res_info.json()["sha"]
            url_blob = f"https://api.github.com/repos/{REPO}/git/blobs/{file_sha}"
            res_blob = requests.get(url_blob, headers=headers, timeout=60)
            if res_blob.status_code == 200:
                content = base64.b64decode(res_blob.json()["content"]).decode("utf-8")
                return content, file_sha
        return None, None
    except:
        return None, None

def load_list(filename, default_values):
    content, _ = get_github_file_large(filename)
    if content:
        try:
            df_list = pd.read_csv(StringIO(content))
            return df_list.iloc[:, 0].dropna().unique().tolist()
        except:
            return default_values
    return default_values

def save_data(df_to_save, sha):
    url = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    csv_content = df_to_save.to_csv(index=False, lineterminator='\n', encoding='utf-8')
    encoded = base64.b64encode(csv_content.encode("utf-8")).decode("utf-8")
    payload = {"message": "Mise à jour stock", "content": encoded, "sha": sha}
    res = requests.put(url, json=payload, headers=headers)
    return (True, res.json()["content"]["sha"]) if res.status_code in [200, 201] else (False, None)

# --- CHARGEMENT INITIAL (SÉCURISÉ) ---
if 'stock_df' not in st.session_state:
    with st.spinner("Chargement de la base de données..."):
        content, sha = get_github_file_large(FILE_PATH)
        cols = ["ID", "Categorie", "Nom", "Description", "Couvrance", "Finition", "Saison", "Lieu", "Photo"]
        
        if content:
            try:
                temp_df = pd.read_csv(StringIO(content), low_memory=False)
                temp_df.columns = temp_df.columns.str.strip()
                for c in cols:
                    if c not in temp_df.columns: temp_df[c] = ""
                temp_df["ID"] = temp_df["ID"].astype(str)
                st.session_state['stock_df'] = temp_df
                st.session_state['current_sha'] = sha
            except:
                st.session_state['stock_df'] = pd.DataFrame(columns=cols)
                st.session_state['current_sha'] = sha
        else:
            st.session_state['stock_df'] = pd.DataFrame(columns=cols)
            st.session_state['current_sha'] = None

        # --- FIX POUR LES LISTES DÉROULANTES ---
        # On définit les valeurs par défaut AVANT de tenter le chargement GitHub
        default_cats = ["Vernis", "Soins", "Accessoires"]
        default_couv = ["Opaque", "Semi-opaque", "Transparent"]
        default_fin = ["Laqué", "Mat", "Irisé", "Pailleté", "Holo"]
        default_sai = ["Toutes", "Printemps", "Été", "Automne", "Hiver"]
        default_lieu = ["Tiroir 1", "Tiroir 2", "Étagère", "Sac à main"]

        # Tentative de chargement depuis GitHub, sinon garde le défaut
        st.session_state['list_cat'] = load_list("categorie.csv", default_cats)
        st.session_state['list_couv'] = load_list("couvrance.csv", default_couv)
        st.session_state['list_fin'] = load_list("finition.csv", default_fin)
        st.session_state['list_sai'] = load_list("saison.csv", default_sai)
        st.session_state['list_lieu'] = load_list("lieu.csv", default_lieu)

        # Double vérification : si après le chargement une liste est vide, on force le défaut
        if not st.session_state['list_cat']: st.session_state['list_cat'] = default_cats
        if not st.session_state['list_couv']: st.session_state['list_couv'] = default_couv
        if not st.session_state['list_fin']: st.session_state['list_fin'] = default_fin
        if not st.session_state['list_sai']: st.session_state['list_sai'] = default_sai
        if not st.session_state['list_lieu']: st.session_state['list_lieu'] = default_lieu

# --- DÉFINITION DE DF (POUR ÉVITER NAMEERROR) ---
df = st.session_state.get('stock_df', pd.DataFrame(columns=["ID", "Categorie", "Nom", "Description", "Couvrance", "Finition", "Saison", "Lieu", "Photo"]))

# --- INTERFACE PRINCIPALE ---
col_titre, col_refresh, col_sort = st.columns([4, 1, 1])
with col_titre:
    st.title("💅 Ma Collection Beauté")
with col_refresh:
    if st.button("🔄 Rafraîchir"):
        if 'stock_df' in st.session_state: del st.session_state['stock_df']
        st.rerun()
with col_sort:
    sort_order = st.selectbox("Tri Nom", ["A-Z", "Z-A"], label_visibility="collapsed")

if not df.empty:
    ascending = (sort_order == "A-Z")
    df = df.sort_values(by="Nom", ascending=ascending, key=lambda col: col.str.lower())

# --- FORMULAIRE D'AJOUT (SIDEBAR) ---
with st.sidebar:
    st.header("✨ Ajouter un article")
    cats = st.session_state.get('list_cat', ["Vernis"])
    cat_select = st.selectbox("Catégorie", cats, key="add_cat_selector")
    
    with st.form("form_ajout", clear_on_submit=True):
        nom = st.text_input("Nom du produit")
        desc = st.text_area("Description")
        couv, fini, sais = "", "", ""
        if cat_select == "Vernis":
            couv = st.selectbox("Couvrance", st.session_state.get('list_couv', []))
            fini = st.selectbox("Finition", st.session_state.get('list_fin', []))
            sais = st.selectbox("Saison", st.session_state.get('list_sai', []))
        lieu = st.selectbox("Lieu", st.session_state.get('list_lieu', []))
        file = st.file_uploader("Photo", type=["jpg", "jpeg", "png"])
        submit = st.form_submit_button("🚀 ENREGISTRER")
        
        if submit and nom:
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

# --- ZONE DE MODIFICATION ---
if st.session_state['editing_product'] is not None:
    p = st.session_state['editing_product']
    st.markdown('<div class="edit-container">', unsafe_allow_html=True)
    st.subheader(f"📝 Modifier : {p.get('Nom', 'Produit')}")
    col_e1, col_e2 = st.columns([2, 1])
    
    with col_e1:
        e_cat = st.selectbox("Catégorie", cats, index=cats.index(p['Categorie']) if p.get('Categorie') in cats else 0)
        e_nom = st.text_input("Nom", value=p.get('Nom', ''))
        e_desc = st.text_area("Description", value=p.get('Description', ''))
        e_couv, e_fini, e_sais = "", "", ""
        if e_cat == "Vernis":
            c_l, f_l, s_l = st.session_state.get('list_couv', []), st.session_state.get('list_fin', []), st.session_state.get('list_sai', [])
            e_couv = st.selectbox("Couvrance", c_l, index=c_l.index(p['Couvrance']) if p.get('Couvrance') in c_l else 0)
            e_fini = st.selectbox("Finition", f_l, index=f_l.index(p['Finition']) if p.get('Finition') in f_l else 0)
            e_sais = st.selectbox("Saison", s_l, index=s_l.index(p['Saison']) if p.get('Saison') in s_l else 0)
        l_l = st.session_state.get('list_lieu', [])
        e_lieu = st.selectbox("Lieu", l_l, index=l_l.index(p['Lieu']) if p.get('Lieu') in l_l else 0)
    
    with col_e2:
        e_file = st.file_uploader("Changer photo", type=["jpg", "jpeg", "png"])
        # CORRECTION ICI : Vérification robuste de la photo existante
        photo_data = p.get('Photo', "")
        if not e_file and isinstance(photo_data, str) and len(photo_data) > 10:
            try:
                st.image(base64.b64decode(photo_data), width=150)
            except:
                st.warning("Impossible d'afficher l'aperçu de l'ancienne photo.")

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("✅ Enregistrer les modifications", use_container_width=True):
            updated_df = st.session_state['stock_df'].copy()
            # On garde l'ancienne photo si aucune nouvelle n'est chargée
            final_img = base64.b64encode(e_file.read()).decode() if e_file else p.get('Photo', "")
            
            # Mise à jour dans le DataFrame
            mask = updated_df['ID'].astype(str) == str(p['ID'])
            updated_df.loc[mask, ["Categorie", "Nom", "Description", "Couvrance", "Finition", "Saison", "Lieu", "Photo"]] = \
                [e_cat, e_nom, e_desc, e_couv, e_fini, e_sais, e_lieu, final_img]
            
            ok, s = save_data(updated_df, st.session_state['current_sha'])
            if ok:
                st.session_state['stock_df'] = updated_df
                st.session_state['current_sha'] = s
                st.session_state['editing_product'] = None
                st.success("Modifications enregistrées !")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Erreur lors de la sauvegarde sur GitHub.")
                
    with col_btn2:
        if st.button("❌ Annuler", use_container_width=True):
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
                    st.subheader(row['Nom'])
                    if row['Categorie'] == "Vernis":
                        st.caption(f"{row['Couvrance']} | {row['Finition']} | {row['Saison']}")
                    st.write(f"📍 {row['Lieu']}")
                    c1, c2 = st.columns(2)
                    if c1.button("📝", key=f"e_{key}_{row['ID']}"):
                        st.session_state['editing_product'] = row.to_dict(); st.rerun()
                    if c2.button("🗑️", key=f"d_{key}_{row['ID']}"):
                        new_df = st.session_state['stock_df'][st.session_state['stock_df']['ID'].astype(str) != str(row['ID'])]
                        ok, s = save_data(new_df, st.session_state['current_sha'])
                        if ok:
                            st.session_state['stock_df'] = new_df
                            st.session_state['current_sha'] = s
                            st.rerun()

for i, t in enumerate(["Tous", "Vernis", "Soins", "Accessoires"]):
    with tabs[i]:
        display_grid(df if t == "Tous" else df[df["Categorie"] == t], t)

with tabs[4]:
    q = st.text_input("Recherche globale")
    if q:
        res = df[df.apply(lambda r: r.astype(str).str.contains(q, case=False).any(), axis=1)]
        display_grid(res, "search")
