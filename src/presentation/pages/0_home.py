"""
Homepage / Dashboard Principale - RGD-Alpha
Pagina di atterraggio per utenti autenticati.
"""

import streamlit as st

from src.presentation.state import SessionManager

# 1. Protezione Accesso
SessionManager.require_auth()


def show() -> None:
    """Entry point standard per la visualizzazione della Home Page."""

    # Recupero sicuro delle informazioni utente
    user_email = SessionManager.get_email() or "Utente"
    azienda_nome = SessionManager.get_azienda() or "Azienda"

    # --- HEADER ---
    st.title("🏠 Homepage RGD-Alpha")
    st.subheader(f"Benvenuto, {user_email} | {azienda_nome}")
    st.divider()

    # --- PANORAMICA STATO SISTEMA (GRID LAYOUT) ---
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("### 📌 Roadmap Operativa Dashboard")
        st.info("""
            La tua piattaforma di **Business Intelligence & Risk Management** è attiva.
            Le seguenti metriche verranno collegate in tempo reale:

            * **📈 KPI Dashboard:** Metriche generali di bilancio e operatività.
            * **🚨 Alert Critici:** Tracciamento live degli asset sotto soglia di sicurezza.
            * **📁 File Recenti:** Storico dei dataset aziendali caricati.
            * **📊 Analisi:** Generazione report prescrittivi in PDF/TXT.
            """)

    with col2:
        st.markdown("### ⚡ Stato Sistema")
        st.metric("Servizi attivi", "4/4")
        st.metric("Dataset pronti", "12")
        st.metric("Alert rilevate", "0")


if __name__ == "__main__":
    show()
