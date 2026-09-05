import traceback

import streamlit as st

from src.config.di_container import DIContainer
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

        with st.status(
            "🚀 Protocollo Analitico RGD in corso...", expanded=True
        ) as status:
            try:
                # Dependency Injection
                container = DIContainer()
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
                        history = [asset.rischio.value] * 5
                        analisi_dto = analizzatore.analyze_asset_risk(asset, history)

                        insight_text = getattr(
                            analisi_dto,
                            "insight",
                            getattr(
                                analisi_dto, "consiglio", "Analisi non disponibile"
                            ),
                        )

                        # UI Rendering
                        with st.expander(f"🔍 Analisi Asset: {asset.nome}"):
                            col_info, col_risk = st.columns([2, 1])
                            with col_info:
                                st.write(f"**ID Azienda:** `{asset.azienda_id}`")
                                st.info(f"**Consiglio Strategico:**\n{insight_text}")
                            with col_risk:
                                st.metric(
                                    "Rischio Attuale",
                                    f"{asset.rischio.value}/10",
                                )

                        # Popolamento unico del report per evitare duplicazione di calcoli
                        report_lines.append(f"ASSET: {asset.nome}")
                        report_lines.append(
                            f" - Rischio Attuale: {asset.rischio.value}/10"
                        )
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

        # D. Rendering Pulsante Download fuori dal blocco status (evita UI glitches)
        if analizzati_con_successo > 0:
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
