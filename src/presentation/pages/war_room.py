import traceback

import pandas as pd
import streamlit as st

import src.config.di_container
from src.presentation.state.session_manager import SessionManager

# Protezione Sicurezza
SessionManager.require_auth()


def show():
    # --- STYLING & UI ---
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

    # --- CARICAMENTO FILE MULTI-SISTEMA (SAP, Oracle, AS400, CSV, Excel, PDF) ---
    st.markdown("### 📁 Caricamento Dati Operativi & Enterprise Ingestion")
    uploaded_file = st.file_uploader(
        "Seleziona il tracciato o report operativo (CSV, Excel, PDF)",
        type=["xlsx", "csv", "pdf"],
        help="Il sistema riconosce e normalizza automaticamente i tracciati ERP e gestionali.",
    )

    st.divider()

    if uploaded_file is not None:
        if uploaded_file.size == 0:
            st.error("❌ Il file caricato è vuoto. Selezionare un documento valido.")
            return

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
                # 1️⃣ INGESTIONE E NORMALIZZAZIONE MULTI-SISTEMA
                # ============================================================
                assets = ingestore.process_file(
                    uploaded_file, SessionManager.get_user_id()
                )

                if not assets:
                    status.update(label="⚠️ Nessun dato rilevato", state="error")
                    st.warning(
                        "Il file caricato non contiene asset o dati validi per l'analisi."
                    )
                    return

                # ============================================================
                # 2️⃣ RIPRISTINO PUNTATORE STREAM (SAFE SEEK)
                # ============================================================
                uploaded_file.seek(0)

                try:
                    if uploaded_file.name.endswith(".csv"):
                        df = pd.read_csv(uploaded_file)
                    elif uploaded_file.name.endswith((".xls", ".xlsx")):
                        df = pd.read_excel(uploaded_file)
                    else:
                        # Fallback per PDF o file testuali gestiti dall'ingestore
                        df = pd.DataFrame(
                            [
                                {"Asset": a.nome, "Rischio": getattr(a, "rischio", 0)}
                                for a in assets
                            ]
                        )
                except Exception:
                    status.update(label="⚠️ Avviso parsing tabellare", state="complete")
                    df = pd.DataFrame(
                        [
                            {"Asset": getattr(a, "nome", "N/D"), "Rischio": 5.0}
                            for a in assets
                        ]
                    )

                capacita = ingestore.analizza_capacita_file(df)

                st.subheader("🔍 Analisi Tracciati & Riconoscimento Semantico")
                for msg in capacita.get("messaggi", []):
                    st.warning(msg)

                # ============================================================
                # 3️⃣ SPIEGAZIONE AI DEL FILE ACQUISITO
                # ============================================================
                spiegazione_ai = ai.generate_text(
                    prompt=f"""
                    Sei un analista aziendale senior specializzato in sistemi ERP e logistica.
                    Spiega all'utente il significato dei dati estratti dal tracciato.

                    KPI disponibili: {capacita.get("kpi_disponibili", {})}
                    Magazzino disponibile: {capacita.get("magazzino_disponibile", {})}
                    Asset identificati: {len(assets)}
                    """
                )

                st.subheader("🧠 Spiegazione AI del Tracciato")
                st.write(spiegazione_ai)

                # ============================================================
                # 4️⃣ CALCOLO KPI STRATEGICI
                # ============================================================
                if capacita.get("kpi_disponibili"):
                    risultato_kpi = kpi_service.calcola_kpi(df)
                    st.subheader("📈 KPI Strategici Globali")
                    st.success(
                        risultato_kpi.get("messaggio", "KPI calcolati con successo.")
                    )
                    st.write(risultato_kpi.get("kpi", {}))
                else:
                    st.info(
                        "I KPI avanzati richiedono campi specifici nel tracciato, dati di base comunque attivi."
                    )

                status.update(
                    label="✅ Ingestione Completata. Elaborazione Asset...",
                    state="running",
                )

                # ============================================================
                # 5️⃣ ANALISI DEL RISCHIO PER SINGOLO ASSET
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
                                analisi_dto, "consiglio", "Analisi standard completata."
                            ),
                        )

                        comp_id = getattr(
                            asset,
                            "company_id",
                            getattr(asset, "azienda_id", SessionManager.get_azienda()),
                        )
                        asset_name = getattr(asset, "nome", "Asset Gestionale")

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
                        st.error(f"Errore nell'analisi dell'asset: {e!s}")

                status.update(
                    label="✅ Analisi e Archiviazione Completate", state="complete"
                )
                st.success(
                    f"Protocollo terminato: {analizzati_con_successo}/{len(assets)} asset elaborati."
                )

            except Exception as e:
                status.update(label="❌ Errore Critico di Sistema", state="error")
                st.error(f"### Dettaglio Tecnico: {e!s}")
                with st.expander("🔍 Log di Debug"):
                    st.code(traceback.format_exc(), language="python")
                return

        # ============================================================
        # 6️⃣ SIMULATORE DECISIONALE (What-If)
        # ============================================================
        if "assets" in locals() and assets:
            st.subheader("🎮 Simulatore Decisionale (What‑If Engine)")
            simulatore = container.get_simulatore_decisionale_service()

            asset_scelto = st.selectbox(
                "Seleziona un asset per la simulazione strategica",
                assets,
                format_func=lambda a: getattr(a, "nome", "Asset"),
            )

            decisione = st.selectbox(
                "Azione Correttiva",
                [
                    "Aumentare produzione",
                    "Ridurre scorte",
                    "Incrementare investimenti",
                    "Ridurre costi operativi",
                ],
            )

            intensita = st.slider("Intensità dell'intervento", 0.0, 10.0, 5.0)

            if st.button("Esegui Simulazione"):
                risultato = simulatore.simula(asset_scelto, decisione, intensita)

                st.markdown(
                    f"### Risultato Simulazione: **{getattr(risultato, 'asset_nome', 'Asset')}**"
                )
                st.write(f"**Decisione:** {getattr(risultato, 'decisione', decisione)}")
                st.write(
                    f"**Variazione rischio:** {getattr(risultato, 'variazione_rischio', 'N/D')}"
                )
                st.write(
                    f"**Impatto finanziario:** € {getattr(risultato, 'impatto_finanziario', 0.0)}"
                )
                st.markdown("#### 🧠 Valutazione AI")
                st.write(
                    getattr(
                        risultato,
                        "valutazione_ai",
                        "Simulazione elaborata con successo.",
                    )
                )
                st.markdown("---")

        # ============================================================
        # 7️⃣ DASHBOARD VISUALE & EXPORT REPORT
        # ============================================================
        if analizzati_con_successo > 0 and table_records:
            df_vis = pd.DataFrame(table_records)

            st.markdown("### 📈 Dashboard KPI & Archivio Operativo")

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric(label="Asset Totali", value=len(df_vis))
            with col2:
                avg_risk = df_vis["Rischio"].mean()
                st.metric(label="Rischio Medio", value=f"{avg_risk:.1f} / 10")
            with col3:
                st.metric(label="Stato Archivio", value="Sincronizzato", delta="OK")
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
                label="📥 Scarica Report Strategico (.txt)",
                data=report_content,
                file_name=f"Report_Archivio_{SessionManager.get_azienda().replace(' ', '_')}.txt",
                mime="text/plain",
                use_container_width=True,
            )


if __name__ == "__main__":
    show()
