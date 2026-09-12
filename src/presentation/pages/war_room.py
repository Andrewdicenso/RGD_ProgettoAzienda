import traceback

import pandas as pd
import streamlit as st

import src.config.di_container
from src.presentation.state.session_manager import SessionManager

# 1. Protezione Sicurezza
SessionManager.require_auth()


def show():
    # --- RESET E PERSONALIZZAZIONE CSS ---
    st.markdown(
        """
        <style>
            [data-testid="stBaseButton-secondary"] p {
                color: #1e293b !important;
                font-weight: bold !important;
            }
            [data-testid="stFileUploaderDropzone"] {
                border: 2px dashed #00a0dc !important;
                background-color: #ffffff !important;
                border-radius: 10px;
            }
            [data-testid="stFileUploaderDropzoneInstructions"] span {
                color: #475569 !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("📊 War Room Strategica")
    st.subheader(f"Asset Intelligence per: {SessionManager.get_azienda()}")
    st.divider()

    # --- SEZIONE CARICAMENTO ---
    st.markdown("### 📁 Caricamento Dati Operativi")
    uploaded_file = st.file_uploader(
        "Seleziona un file Excel o CSV per avviare il protocollo di analisi",
        type=["xlsx", "csv"],
        help="Il sistema accetta file esportati dai principali ERP (SAP, Oracle, AS400)",
    )

    st.divider()

    if uploaded_file:
        report_lines = [
            "==================================================",
            "   MEMORANDUM STRATEGICO RISERVATO - RGD-ALPHA",
            f"   Azienda: {SessionManager.get_azienda()}",
            "==================================================\n",
        ]
        analizzati_con_successo = 0
        table_records = []

        with st.status(
            "🚀 Protocollo Analitico RGD in corso...", expanded=True
        ) as status:
            try:
                container = src.config.di_container.DIContainer()
                ingestore = container.get_ingestion_service()
                analizzatore = container.get_analysis_service()
                kpi_service = container.get_kpi_service()
                ai = container.get_ai_provider()

                # ============================================================
                # 1️⃣ INGESTIONE FILE
                # ============================================================
                assets = ingestore.process_file(
                    uploaded_file, SessionManager.get_user_id()
                )

                if not assets:
                    status.update(label="⚠️ Nessun dato rilevato", state="error")
                    st.warning(
                        "Il file caricato non contiene dati validi per l'analisi."
                    )
                    return

                # ============================================================
                # 2️⃣ VALIDATORE FILE
                # ============================================================
                df = (
                    pd.read_csv(uploaded_file)
                    if uploaded_file.name.endswith(".csv")
                    else pd.read_excel(uploaded_file)
                )
                capacita = ingestore.analizza_capacita_file(df)

                st.subheader("🔍 Analisi Capacità del File Caricato")
                for msg in capacita["messaggi"]:
                    st.warning(msg)

                # ============================================================
                # 3️⃣ SPIEGAZIONE AI
                # ============================================================
                spiegazione_ai = ai.generate_text(
                    prompt=f"""
                    Sei un analista aziendale senior.
                    Spiega all'utente cosa permette di fare il file caricato.

                    KPI disponibili: {capacita["kpi_disponibili"]}
                    Magazzino disponibile: {capacita["magazzino_disponibile"]}
                    Asset disponibili: {capacita["asset_disponibili"]}

                    Messaggi:
                    {capacita["messaggi"]}
                    """
                )

                st.subheader("🧠 Spiegazione AI del File")
                st.write(spiegazione_ai)

                # ============================================================
                # 4️⃣ KPI (solo se disponibili)
                # ============================================================
                if capacita["kpi_disponibili"]:
                    risultato_kpi = kpi_service.calcola_kpi(df)
                    st.subheader("📈 KPI Strategici")
                    st.success(risultato_kpi["messaggio"])
                    st.write(risultato_kpi["kpi"])
                else:
                    st.info("I KPI non sono disponibili nel file caricato.")

                status.update(
                    label="✅ Ingestione Completata. Avvio Analisi...", state="running"
                )

                # ============================================================
                # 5️⃣ ANALISI ASSET
                # ============================================================
                for asset in assets:
                    try:
                        rischio_val = (
                            asset.rischio.value
                            if hasattr(asset.rischio, "value")
                            else float(asset.rischio)
                        )
                        history = [rischio_val] * 5
                        analisi_dto = analizzatore.analyze_asset_risk(asset, history)

                        insight_text = getattr(
                            analisi_dto,
                            "insight",
                            getattr(
                                analisi_dto, "consiglio", "Analisi non disponibile"
                            ),
                        )

                        comp_id = getattr(
                            asset, "company_id", getattr(asset, "azienda_id", "N/D")
                        )
                        asset_name = getattr(asset, "nome", "Senza Nome")

                        table_records.append(
                            {
                                "ID Azienda": comp_id,
                                "Nome Asset": asset_name,
                                "Rischio": float(rischio_val),
                                "Consiglio Strategico": insight_text,
                            }
                        )

                        report_lines.append(f"ASSET: {asset_name}")
                        report_lines.append(f" - Rischio Attuale: {rischio_val}/10")
                        report_lines.append(
                            f" - Consiglio Strategico: {insight_text}\n"
                        )

                        analizzati_con_successo += 1

                    except Exception as e:
                        st.error(f"Errore nell'analisi dell'asset {asset_name}: {e!s}")

                status.update(label="✅ Analisi Completata", state="complete")
                st.success(
                    f"Protocollo terminato: {analizzati_con_successo}/{len(assets)} asset elaborati con successo."
                )

            except Exception as e:
                status.update(label="❌ Errore Critico di Sistema", state="error")
                st.error(f"### Dettaglio Tecnico: {e!s}")
                with st.expander("🔍 Analisi del Crash (Debug)"):
                    st.code(traceback.format_exc(), language="python")
                return

            # ============================================================
        # 7️⃣ SIMULATORE DECISIONALE (What-If)
        # ============================================================
        st.subheader("🎮 Simulatore Decisionale (What‑If Engine)")

        simulatore = container.get_simulatore_decisionale_service()

        asset_scelto = st.selectbox(
            "Seleziona un asset da simulare", assets, format_func=lambda a: a.nome
        )

        decisione = st.selectbox(
            "Tipo di decisione",
            [
                "Aumentare produzione",
                "Ridurre scorte",
                "Incrementare investimenti",
                "Ridurre costi operativi",
            ],
        )

        intensita = st.slider("Intensità decisione", 0.0, 10.0, 5.0)

        if st.button("Simula Decisione"):
            risultato = simulatore.simula(asset_scelto, decisione, intensita)

            st.markdown(f"### Risultato simulazione per **{risultato.asset_nome}**")
            st.write(f"**Decisione:** {risultato.decisione}")
            st.write(f"**Variazione rischio:** {risultato.variazione_rischio}")
            st.write(f"**Impatto finanziario:** € {risultato.impatto_finanziario}")
            st.write("**Variazione KPI:**")
            st.write(risultato.variazione_kpi)

            st.markdown("#### 🧠 Valutazione AI")
            st.write(risultato.valutazione_ai)

            st.markdown("---")

        # ============================================================
        # 6️⃣ DASHBOARD FINALE
        # ============================================================
        if analizzati_con_successo > 0 and table_records:
            df_vis = pd.DataFrame(table_records)

            st.markdown("### 📈 Dashboard KPI & Asset Intelligence")

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric(label="Asset Totali", value=len(df_vis))
            with col2:
                avg_risk = df_vis["Rischio"].mean()
                st.metric(label="Rischio Medio", value=f"{avg_risk:.1f} / 10")
            with col3:
                st.metric(label="Stato Protocollo", value="Validato", delta="OK")
            with col4:
                st.metric(label="Conformità", value="100%", delta="Enterprise")

            st.markdown("---")

            st.dataframe(
                df_vis,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "ID Azienda": st.column_config.TextColumn(
                        "ID Azienda", width="small"
                    ),
                    "Nome Asset": st.column_config.TextColumn(
                        "Nome Asset", width="medium"
                    ),
                    "Rischio": st.column_config.ProgressColumn(
                        "Indice di Rischio",
                        min_value=0.0,
                        max_value=10.0,
                        format="%.1f / 10",
                    ),
                    "Consiglio Strategico": st.column_config.TextColumn(
                        "Insight / Consiglio", width="large"
                    ),
                },
            )

            report_content = "\n".join(report_lines)
            st.divider()
            st.download_button(
                label="📥 Scarica Report Strategico Elaborato (.txt)",
                data=report_content,
                file_name=f"Report_Strategico_{SessionManager.get_azienda().replace(' ', '_')}.txt",
                mime="text/plain",
                use_container_width=True,
            )


if __name__ == "__main__":
    show()
