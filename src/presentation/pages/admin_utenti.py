import pandas as pd
import streamlit as st

import src.config.di_container
from src.presentation.state.session_manager import SessionManager

# Protezione Sicurezza: Richiede autenticazione
SessionManager.require_auth()


def show():
    st.title("🛡️ Pannello Amministrazione - Utenti e Log")
    st.subheader(f"Controllo Sistema per: {SessionManager.get_azienda()}")
    st.divider()

    try:
        container = src.config.di_container.DIContainer()
        db = container.get_database()

        # Eseguiamo una query diretta alla tabella 'utenti' su Supabase
        response = db.client.table("utenti").select("*").execute()
        utenti_data = response.data

        if not utenti_data:
            st.info("Nessun utente registrato trovato nel database.")
            return

        df_utenti = pd.DataFrame(utenti_data)

        st.markdown("### 👥 Elenco Utenti Registrati")
        st.dataframe(
            df_utenti,
            use_container_width=True,
            hide_index=True,
        )

        st.metric(label="Totale Utenti a Sistema", value=len(df_utenti))

    except Exception as e:
        st.error(f"Errore durante il recupero dei dati da Supabase: {e!s}")


if __name__ == "__main__":
    show()
