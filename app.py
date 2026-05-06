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
    st.error("Le secret 'GITHUB_TOKEN' est manquant.")
    st.stop()

REPO = "stephane0254-png/VernisEmilie"
FILE_PATH = "data.csv"

st.set_page_config(page_title="Beauty Stock", page_icon="💅", layout="wide")

# --- FONCTIONS GITHUB (VERSION HAUTE CAPACITÉ) ---
def get_github_file_large(path):
    # 1. Récupérer le SHA du fichier via l'API standard
    url_info = f"https://api.github.com/repos/{REPO}/contents/{path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    
    try:
        res_info = requests.get(url_info, headers=headers, timeout=20)
        if res_info.status_code == 200:
            file_sha = res_info.json()["sha"]
            
            # 2. Utiliser l'API BLOB pour télécharger le contenu lourd
            url_blob = f"https://api.github.com/repos/{REPO}/git/blobs/{file_sha}"
            res_blob = requests.get(url_blob, headers=headers, timeout=60)
            
            if res_blob.status_code == 200:
                content = base64.b64decode(res_blob.json()["content"]).decode("utf-8")
                return content, file_sha
        return None, None
    except Exception as e:
        st.error(f"Erreur technique : {e}")
        return None, None

def get_data():
    content, sha = get_github_file_large(FILE_PATH)
    cols = ["ID", "Categorie", "Nom", "Description", "Couvrance", "Finition", "Saison", "Lieu", "Photo"]
    if content:
        try:
            df_load = pd.read_csv(StringIO(content), low_memory=False)
            df_load.columns = df_load.columns.str.strip()
            for c in cols:
                if c not in df_load.columns: df_load[c] = ""
            df_load["ID"] = df_load["ID"].astype(str)
            return df_load, sha, None
        except Exception as e:
            return None, sha, f"Erreur d'analyse : {e}"
    return None, None, "Fichier inaccessible (trop volumineux ou token invalide)"

# --- CHARGEMENT INITIAL ---
if 'stock_df' not in st.session_state:
    with st.spinner("Chargement de la base de données volumineuse..."):
        loaded_df, loaded_sha, err = get_data()
        if err: 
            st.error(err)
            st.info("💡 Si le fichier est trop lourd, essayez de le nettoyer manuellement sur GitHub.")
            st.stop()
        st.session_state['stock_df'] = loaded_df
        st.session_state['current_sha'] = loaded_sha


# --- INTERFACE ---
col_titre, col_refresh, col_sort = st.columns([4, 1, 1])
with col_titre:
    st.title("💅 Ma Collection Beauté")
with col_refresh:
    if st.button("🔄 Rafraîchir"):
        for key in ['stock_df', 'current_sha']:
            if key in st.session_state: del st.session_state[key]
        st.rerun()
with col_sort:
    sort_order = st.selectbox("Tri Nom", ["A-Z", "Z-A"], label_visibility="collapsed")

if not df.empty:
    ascending = (sort_order == "A-Z")
    df = df.sort_values(by="Nom", ascending=ascending, key=lambda col: col.str.lower())

# --- FORMULAIRE D'AJOUT (SIDEBAR) ---
with st.sidebar:
    st.header("✨ Ajouter un article")
    cat_select = st.selectbox("Catégorie", st.session_state['list_cat'], key="add_cat_selector")
    
    with st.form("form_ajout", clear_on_submit=True):
        nom = st.text_input("Nom du produit")
        desc = st.text_area("Description")
        
        couv, fini, sais = "", "", ""
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
                success, result = save_data(updated_df)
                if success:
                    st.session_state['stock_df'] = updated_df
                    st.session_state['current_sha'] = result
                    st.success("Ajouté !"); time.sleep(1); st.rerun()
                else:
                    st.error(f"Erreur de sauvegarde : {result}")
            else:
                st.error("Nom requis.")

# --- ZONE DE MODIFICATION ---
if st.session_state['editing_product'] is not None:
    p = st.session_state['editing_product']
    st.markdown('<div class="edit-container">', unsafe_allow_html=True)
    st.subheader(f"📝 Modifier : {p['Nom']}")
    
    col_e1, col_e2 = st.columns([2, 1])
    with col_e1:
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
        success, result = save_data(updated_df)
        if success:
            st.session_state['stock_df'] = updated_df
            st.session_state['current_sha'] = result
            st.session_state['editing_product'] = None
            st.rerun()
        else:
            st.error(f"Erreur : {result}")

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
                        ok, result = save_data(new_df)
                        if ok:
                            st.session_state['stock_df'] = new_df
                            st.session_state['current_sha'] = result
                            st.rerun()

for i, t in enumerate(["Tous", "Vernis", "Soins", "Accessoires"]):
    with tabs[i]:
        display_grid(df if t == "Tous" else df[df["Categorie"] == t], t)

with tabs[4]:
    st.markdown('<div class="search-box">', unsafe_allow_html=True)
    q = st.text_input("Recherche globale", placeholder="Nom, fini, lieu...")
    if q:
        res = df[df.apply(lambda r: r.astype(str).str.contains(q, case=False).any(), axis=1)]
        display_grid(res, "search")
