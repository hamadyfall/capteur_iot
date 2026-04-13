import streamlit as st
from firebase_admin import db, credentials, initialize_app
import firebase_admin
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# Initialisation via les secrets Streamlit
if not firebase_admin._apps:
    # On transforme les secrets Streamlit en dictionnaire Python
    fb_creds = dict(st.secrets["firebase"])
    # Important : Streamlit gère parfois mal les \n, on s'assure qu'ils sont corrects
    fb_creds["private_key"] = fb_creds["private_key"].replace("\\n", "\n")
    cred = credentials.Certificate(fb_creds)
    firebase_admin.initialize_app(cred, {
        'databaseURL': "https://capteur-iot-default-rtdb.europe-west1.firebasedatabase.app/"
    })

st.set_page_config(page_title="Dashboard IoT", layout="wide")
st.title(" Analyse Historique des Capteurs")


# 1. Récupération des données
@st.cache_data(ttl=60)  # Rafraîchit les données toutes les minutes
def load_data():
    data = db.reference('capteurs/sol').get()
    if not data: return pd.DataFrame()
    df = pd.DataFrame(data.values())
    df['date'] = pd.to_datetime(df['timestamp'], unit='s')
    return df


df = load_data()

if not df.empty:
    # 2. Sidebar pour les FILTRES
    # 2. Sidebar pour les FILTRES
    st.sidebar.header("Filtres")

    # On extrait uniquement la partie date (sans l'heure) pour le calendrier
    df['date_only'] = df['date'].dt.date

    min_date = df['date_only'].min()
    max_date = df['date_only'].max()

    date_range = st.sidebar.date_input(
        "Sélectionnez une période",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    # Application du filtre (on vérifie qu'on a bien une date de début et de fin)
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
        mask = (df['date_only'] >= start_date) & (df['date_only'] <= end_date)
        df_filtered = df.loc[mask]
    else:
        df_filtered = df

    # 3. Affichage des stats filtrées
    st.subheader(f"Données du {date_range}")

    # Graphique interactif (Zoomable)
    colonnes_a_afficher = ['temp', 'humidite', 'ph', 'N', 'P', 'K', 'ec', 'fertilite']

    fig = px.line(
        df_filtered,
        x='date',
        y=colonnes_a_afficher,
        title="Évolution de tous les paramètres du sol"
    )
    st.plotly_chart(fig, use_container_width=True)

    # Tableau des données brutes
    if st.checkbox("Voir le tableau des données brutes"):
        st.write(df_filtered.sort_values(by='date', ascending=False))
else:
    st.warning("Aucune donnée trouvée dans Firebase.")
