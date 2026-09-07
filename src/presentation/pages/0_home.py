"""
Homepage / Dashboard Principale - RGD-Alpha
Pagina di atterraggio per utenti autenticati.
"""

import streamlit as st

from src.presentation.state import SessionManager

# 1. Protezione Accesso
SessionManager.require_auth()


def show() -> None:
    """Funzione principale richiamata dal router per la pagina Home."""

    # Recupero sicuro delle informazioni utente
    user_email = SessionManager.get_email() or "Utente"
    azienda_nome = SessionManager.get_azienda() or "Azienda"

    # --- HEADER ---
    st.title("🛡️ RGD-Alpha | Dashboard Strategica")
    st.subheader(f"Benvenuto, {user_email} | Azienda: {azienda_nome}")
    st.markdown(
        "La piattaforma di **Business Intelligence e Risk Management** progettata per PMI italiane."
    )
    st.divider()

    # --- PANORAMICA STATO SISTEMA (GRID LAYOUT) ---
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### 📌 Panoramica Operativa in Tempo Reale")
        st.success("Piattaforma agganciata al database aziendale con successo.")

        st.info("""
            La tua piattaforma di **Business Intelligence & Risk Management** è attiva.
            """)

        st.markdown("### 🚀 Funzionalità Principali")
        st.markdown("""
            * **📈 Analisi Predittiva del Rischio**
            * **🎯 Dashboard Strategica (War Room)**
            * **⚡ Alerting Automatico**
            * **📊 Simulazioni What-If e Reportistica**
            """)

        st.markdown("### 📌 Roadmap Operativa Dashboard")
        st.markdown("""
            * **📈 KPI Dashboard:** Metriche generali di bilancio e operatività.
            * **🚨 Alert Critici:** Tracciamento live degli asset sotto soglia di sicurezza.
            * **📁 File Recenti:** Storico dei dataset aziendali caricati.
            * **📊 Analisi:** Generazione report prescrittivi in PDF/TXT.
            """)

    with col2:
        st.markdown("### ⚡ Stato Sistema")
        st.metric("Servizi attivi", "4/4")
        st.metric("Database", "Connesso")
        st.metric("Alert critici", "0")
