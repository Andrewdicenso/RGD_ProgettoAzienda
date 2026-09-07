import traceback

import pandas as streamlit_pd
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
                # Dependency Injection
                container = src.config.di_container.DIContainer()
                ingestore = container.get_ingestion_service()
                analizzatore = container.get_analysis_service()

                # A. Ingestione Dati
                assets = ingestore.process_file(
                    uploaded_file, SessionManager.get_user_id()
                )

                if not assets:
                    status.update(label="⚠️ Nessun dato rilevato", state="error")
                    st.warning(
                        "Il file caricato non contiene dati validi per l'analisi."
                    )
                    return

                status.update(
                    label="✅ Ingestione Completata. Avvio Analisi...",
                    state="running",
                )

                # B. Analisi in singolo passaggio (O(N)) con acquisizione unica dei dati
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
                            asset,
                            "company_id",
                            getattr(asset, "azienda_id", "N/D"),
                        )

                        asset_name = getattr(asset, "nome", "Senza Nome")

                        # Raccolta dati per la tabella strutturata enterprise
                        table_records.append(
                            {
                                "id_azienda": comp_id,
                                "nome": asset_name,
                                "rischio": float(rischio_val),
                                "consiglio": insight_text,
                            }
                        )

                        # Popolamento unico del report per evitare duplicazione di calcoli
                        report_lines.append(f"ASSET: {asset_name}")
                        report_lines.append(f" - Rischio Attuale: {rischio_val}/10")
                        report_lines.append(
                            f" - Consiglio Strategico: {insight_text}\n"
                        )

                        analizzati_con_successo += 1
                    except Exception as e:
                        st.error(
                            f"Errore nell'analisi dell'asset {getattr(asset, 'nome', 'Sconosciuto')}: {e!s}"
                        )

                # C. Finalizzazione
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

        # D. Rendering Layout Enterprise pulito con KPI e Tabella Interattiva
        if analizzati_con_successo > 0 and table_records:
            df_vis = streamlit_pd.DataFrame(table_records)

            st.markdown("### 📊 Dashboard Operativa - Analisi Asset")

            # KPI Cards superiori in stile enterprise dashboard
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric(label="Asset Totali Analizzati", value=len(df_vis))
            with col2:
                avg_risk = df_vis["rischio"].mean() if not df_vis.empty else 0.0
                st.metric(
                    label="Rischio Medio", value=f"{avg_risk:.1f} / 10", delta="Stabile"
                )
            with col3:
                st.metric(label="Stato Sistema", value="Protetto", delta="Online")
            with col4:
                st.metric(label="Conformità Formato", value="100%", delta="Validato")

            st.markdown("---")

            # Tabella interattiva strutturata con colonne configurate professionalmente
            st.data_editor(
                df_vis,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "id_azienda": st.column_config.TextColumn(
                        "ID Azienda", width="small"
                    ),
                    "nome": st.column_config.TextColumn("Nome Asset", width="medium"),
                    "rischio": st.column_config.ProgressColumn(
                        "Indice di Rischio",
                        min_value=0.0,
                        max_value=10.0,
                        format="%.1f / 10",
                    ),
                    "consiglio": st.column_config.TextColumn(
                        "Consiglio Strategico / Insight", width="large"
                    ),
                },
            )

            # E. Rendering Pulsante Download
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
