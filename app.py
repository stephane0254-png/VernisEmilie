import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from PIL import Image
import io
import base64

# Configuration
st.set_page_config(page_title="Beauty Stock", page_icon="💅", layout="wide")

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
