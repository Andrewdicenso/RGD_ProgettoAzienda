# Ensure the project root is on sys.path before importing local modules.
# This makes the app resolvable when launched from VS Code, Streamlit or cron
# and avoids the "Import could not be resolved" warning in the editor.
import os
import sqlite3
import sys
from importlib import import_module

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Ensure src modules can be imported
sys.path.insert(0, PROJECT_ROOT)

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Import modules dynamically so static analyzers do not report an unresolved
# package when the application is launched from different project roots.
try:
    AnalistaRischio = import_module("src.analyst").AnalistaRischio
    analyst = type("analyst", (), {"AnalistaRischio": AnalistaRischio})()
except (ImportError, AttributeError):
    try:
        AnalistaRischio = import_module("analyst").AnalistaRischio
        analyst = type("analyst", (), {"AnalistaRischio": AnalistaRischio})()
    except (ImportError, AttributeError):
        analyst = None
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))
try:
    DatabaseAziendale = import_module(
        "src.infrastructure.persistence.db.database"
    ).DatabaseAziendale
except (ImportError, AttributeError):
    DatabaseAziendale = import_module(
        "infrastructure.persistence.db.database"
    ).DatabaseAziendale

# Import dynamically so static analyzers do not report a missing optional
# package when the application is launched from different project roots.
try:
    SimulatoreRischio = import_module("src.simulator").SimulatoreRischio
except ImportError:
    try:
        SimulatoreRischio = import_module("simulator").SimulatoreRischio
    except ImportError:
        SimulatoreRischio = None

# --- CONFIGURAZIONE PERCORSI (ENGINEERING STANDARD) ---
# Ricaviamo il percorso assoluto per evitare errori "file not found"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "db", "azienda.db")

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="RGandja Alpha - Intelligence Dashboard", layout="wide")

st.title("🚀 RGandja Alpha: Business Intelligence Proattiva")
st.sidebar.header("Impostazioni Analisi")

# --- INIZIALIZZAZIONE COMPONENTI ---
COMPANY_ID = "AZ-TEST-01"
# Inizializziamo i moduli src usando il percorso assoluto definito sopra
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
db = DatabaseAziendale(
    db_folder=os.path.dirname(DB_PATH), db_name=os.path.basename(DB_PATH)
)
analista = analyst.AnalistaRischio(db_path=DB_PATH)
simulatore = SimulatoreRischio()


# --- LOGICA DI ACCESSO AI DATI ---
def get_assets():
    """Recupera la lista degli asset unici dal database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        query = (
            f"SELECT DISTINCT nome FROM asset_logs WHERE company_id = '{COMPANY_ID}'"
        )
        df = pd.read_sql(query, conn)
        conn.close()
        return df["nome"].tolist()
    except Exception as e:
        # Se la tabella non esiste ancora, mostriamo un errore tecnico chiaro
        st.error(f"Errore tecnico nel database: {e}")
        return []


# --- COSTRUZIONE INTERFACCIA ---
assets = get_assets()

if not assets:
    st.warning("⚠️ Nessun dato trovato nel database.")
    st.info(f"Esegui prima: 'python main.py' per popolare il database in: {DB_PATH}")
    st.stop()

selected_asset = st.sidebar.selectbox("Seleziona Asset da monitorare", assets)

if selected_asset:
    # Elaborazione dati tramite l'Analista
    report = analista.calcola_trend_predittivo(selected_asset, COMPANY_ID)

    if report.get("status") == "Inizializzazione":
        st.info(
            f"ℹ️ L'asset '{selected_asset}' è in fase di inizializzazione. Dati insufficienti per il trend."
        )
    else:
        # 1. Metriche Principali (KPI Row)
        col1, col2, col3, col4 = st.columns(4)

        # Calcoliamo la proiezione Monte Carlo
        proiezione = simulatore.esegui_stress_test(
            valore_attuale=report["valore_attuale"],
            volatilita=report.get("indice_volatilita", 0.5),
        )

        col1.metric("Rischio Attuale", f"{report['valore_attuale']}/10")
        col2.metric("Momentum", report.get("momentum_percentuale", "N/D"))
        col3.metric("Volatilità", f"{report.get('indice_volatilita', 0)}")
        col4.metric("Probabilità Crisi (30gg)", f"{proiezione['probabilita_crisi']}%")

        st.markdown("---")

        # 2. Grafici (Data Visualization Row)
        col_left, col_right = st.columns(2)

        with col_left:
            st.subheader("📈 Andamento Storico Rischio")
            conn = sqlite3.connect(DB_PATH)
            query_hist = f"SELECT timestamp, rischio FROM asset_logs WHERE nome='{selected_asset}' ORDER BY timestamp DESC LIMIT 25"
            df_hist = pd.read_sql(query_hist, conn).sort_values("timestamp")
            conn.close()

            fig_hist = px.line(
                df_hist,
                x="timestamp",
                y="rischio",
                markers=True,
                range_y=[0, 10],
                title=f"Evoluzione Temporale: {selected_asset}",
                color_discrete_sequence=["#00CC96"],
            )
            st.plotly_chart(fig_hist, use_container_width=True)

        with col_right:
            st.subheader("🔮 Data di Sopravvivenza Stimata")
            # Tachimetro (Gauge Chart) per la sopravvivenza
            fig_gauge = go.Figure(
                go.Indicator(
                    mode="gauge+number",
                    value=proiezione["giorni_sopravvivenza_stimati"],
                    domain={"x": [0, 1], "y": [0, 1]},
                    gauge={
                        "axis": {"range": [0, 30], "tickwidth": 1},
                        "bar": {"color": "#1f77b4"},
                        "steps": [
                            {"range": [0, 10], "color": "#FF4B4B"},
                            {"range": [10, 20], "color": "#FFAA00"},
                            {"range": [20, 30], "color": "#00CC96"},
                        ],
                    },
                )
            )
            st.plotly_chart(fig_gauge, use_container_width=True)

        # 3. Intelligence Outout (Strategy Row)
        st.markdown("---")
        st.subheader("💡 Valutazione Strategica")

        c_strat, c_act = st.columns(2)
        with c_strat:
            st.info(f"**Diagnosi**: {report.get('valutazione_strategica', 'N/D')}")
        with c_act:
            st.warning(
                f"**Azione Consigliata**: {report.get('azione', 'Monitoraggio Standard')}"
            )

        if report.get("alert_critico") or proiezione["probabilita_crisi"] > 40:
            st.error(
                f"🚨 ALERT: Rilevata criticità elevata per {selected_asset}. Probabilità di rottura entro 30 giorni: {proiezione['probabilita_crisi']}%"
            )
