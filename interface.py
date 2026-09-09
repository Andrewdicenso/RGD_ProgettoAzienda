import logging

import streamlit as st

from src.infrastructure.persistence.db.connection import DatabaseConnection

# Configurazione del logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RGD-Alpha.Interface")

st.set_page_config(
    page_title="RGD-Alpha Enterprise Dashboard",
    page_icon="🚀",
    layout="wide",
)

st.title("🚀 RGD-Alpha - Enterprise Cloud Dashboard")
st.markdown("---")

# Inizializzazione della connessione al database
try:
    db = DatabaseConnection()
    st.sidebar.success("Connessione Supabase attiva ✅")
    logger.info("DatabaseConnection inizializzato con successo.")
except Exception as e:
    st.sidebar.error("Connessione Supabase fallita ❌")
    logger.error(f"Errore di connessione al database in interfaccia: {e}")

# Sezione principale della dashboard
st.subheader("Stato del Sistema e Gestione Asset")
st.write("Benvenuto nel sistema enterprise Cloud-Native migrato a Clean Architecture.")

# Esempio di utilizzo dell'interfaccia Streamlit
if st.button("Verifica Stato Connessione"):
    if "db" in locals() and db:
        st.info("Il client Cloud Supabase è correttamente istanziato e pronto.")
    else:
        st.warning("Client database non disponibile.")
