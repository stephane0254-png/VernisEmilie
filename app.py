import streamlit as st
import pandas as pd
from PIL import Image
import io

# Configuration de la page
st.set_page_config(page_title="Beauty Stock", page_icon="💅")

st.title("💅 Ma Collection Beauté")

# Initialisation du stockage (Simulé ici par session_state pour l'exemple)
# Pour un usage réel, on connecterait une base de données ici
if 'inventory' not in st.session_state:
    st.session_state.inventory = []

# Barre latérale pour l'ajout
st.sidebar.header("Ajouter un article")
category = st.sidebar.selectbox("Catégorie", ["Vernis", "Soins", "Accessoires"])
name = st.sidebar.text_input("Nom du produit")
description = st.sidebar.text_area("Description")
uploaded_file = st.sidebar.file_input("Photo", type=["jpg", "png", "jpeg"])

if st.sidebar.button("Ajouter à la collection"):
    if name:
        new_item = {
            "cat": category,
            "nom": name,
            "desc": description,
            "image": uploaded_file.read() if uploaded_file else None
        }
        st.session_state.inventory.append(new_item)
        st.sidebar.success("Ajouté !")
    else:
        st.sidebar.error("Le nom est obligatoire")

# Affichage des onglets
tab1, tab2, tab3, tab4 = st.tabs(["Tous", "Vernis", "Soins", "Accessoires"])

def display_items(filter_cat=None):
    items = st.session_state.inventory
    if filter_cat:
        items = [i for i in items if i['cat'] == filter_cat]
    
    if not items:
        st.write("Aucun article dans cette catégorie.")
        return

    cols = st.columns(3)
    for idx, item in enumerate(items):
        with cols[idx % 3]:
            if item['image']:
                st.image(item['image'], use_container_width=True)
            st.subheader(item['nom'])
            st.caption(f"**{item['cat']}**")
            st.write(item['desc'])
            if st.button("Supprimer", key=f"del_{idx}_{filter_cat}"):
                st.session_state.inventory.remove(item)
                st.rerun()

with tab1: display_items()
with tab2: display_items("Vernis")
with tab3: display_items("Soins")
with tab4: display_items("Accessoires")
