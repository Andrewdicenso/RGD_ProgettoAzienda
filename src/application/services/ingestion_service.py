"""
Ingestion Service - Use Case: Ingestione Dati Adattiva Enterprise.
Gestisce il parsing di file Excel/CSV/SAP con riparazione automatica,
normalizzazione dei sinonimi e riconoscimento universale dei sistemi aziendali.
"""

import io
import logging
from typing import Any

import pandas as pd

from src.application.dto import FileIngestionResponseDTO
from src.application.services.base_service import BaseService
from src.application.strategies.mapping_strategy import AttentionMappingStrategy
from src.domain.constants import SAP_FIELD_MAPPING, SINONIMI_MAPPING
from src.domain.entities import Asset, crea_asset_dal_dizionario
from src.domain.exceptions import InvalidRiscoScoreException
from src.domain.value_objects import RiscoScore

logger = logging.getLogger("RGD-Alpha.IngestionService")


class IngestionService(BaseService):
    """
    Servizio di Ingestione Dati Adattivo ed Enterprise.
    Identifica automaticamente la sorgente (SAP, ERP custom, file standard),
    normalizza i flussi eterogenei e li trasforma in entità di dominio trasparenti per RGD-Alpha.
    """

    def __init__(self, asset_repo=None, ai_provider=None):
        super().__init__("IngestionService")
        self.asset_repo = asset_repo
        self.ai_provider = ai_provider
        self.strategy = AttentionMappingStrategy()

        self.enterprise_signatures = {
            "SAP_MM": ["MATNR", "WERKS", "LABST", "MEINS", "LGORT"],
            "SAP_SD": ["KUNNR", "VKORG", "MATNR", "KWMENG", "VRKME"],
            "MICROSOFT_DYNAMICS": [
                "ItemNumber",
                "InventSiteId",
                "QtyAvailable",
                "CostPrice",
            ],
            "ZUCCHETTI_ERP": [
                "CodArt",
                "DescArt",
                "Giacenza",
                "ScortaMin",
                "Fornitore",
            ],
            "STANDARD_MAGAZZINO": ["id", "nome", "quantita", "prezzo", "rischio"],
        }

    def analizza_capacita_file(self, df: pd.DataFrame) -> dict:
        """
        Analizza le colonne del file e determina quali processi aziendali sono possibili,
        attivando un fallback semantico tramite AI se la struttura non è riconosciuta.
        """
        colonne = set(df.columns)
        report = {
            "kpi_disponibili": False,
            "magazzino_disponibile": False,
            "asset_disponibili": False,
            "messaggi": [],
            "semantic_warning": False,
            "ai_suggestions": None,
        }

        kpi_cols = {
            "KPI_Produttività",
            "KPI_Efficienza",
            "KPI_Rendimento",
            "KPI_Saturazione",
        }
        if kpi_cols.issubset(colonne):
            report["kpi_disponibili"] = True

        mag_cols = {"CodiceArticolo", "Quantità", "Magazzino"}
        if mag_cols.issubset(colonne):
            report["magazzino_disponibile"] = True

        asset_cols = {"Asset", "Rischio", "Stato"}
        if asset_cols.issubset(colonne):
            report["asset_disponibili"] = True

        if not any(
            [
                report["kpi_disponibili"],
                report["magazzino_disponibile"],
                report["asset_disponibili"],
            ]
        ):
            report["messaggi"].append(
                "❌ Il file non contiene uno schema standard direttamente compatibile."
            )

            # Fallback Semantico con AI se disponibile
            if self.ai_provider:
                try:
                    prompt = (
                        f"Analizza le seguenti intestazioni di un file aziendale caricato: {list(colonne)}. "
                        "Il sistema richiede concetti simili a magazzino, asset o KPI. "
                        "Fornisci una breve analisi tecnica in italiano suggerendo a quali campi noti "
                        "potrebbero corrispondere queste colonne anomale."
                    )
                    ai_analysis = self.ai_provider.generate_text(prompt)
                    if ai_analysis:
                        report["semantic_warning"] = True
                        report["ai_suggestions"] = ai_analysis
                        report["messaggi"].append(
                            "⚠️ Analisi semantica AI attivata per tracciato non standard."
                        )
                except Exception as e:
                    self.log_warning(
                        f"Impossibile completare l'analisi semantica AI del tracciato: {e}"
                    )

        return report

    def _detect_source_system(self, columns: list[str]) -> str:
        cols_upper = [str(c).upper() for c in columns]
        best_match = "CUSTOM_OR_UNKNOWN"
        max_matches = 0

        for system_name, signature in self.enterprise_signatures.items():
            matches = sum(1 for sig in signature if sig.upper() in cols_upper)
            if matches > max_matches:
                max_matches = matches
                best_match = system_name

        if max_matches > 0:
            self.log_info(
                f"[ERP Fingerprint] Sorgente aziendale identificata: {best_match} (Match score: {max_matches})"
            )
        else:
            self.log_info(
                "[ERP Fingerprint] Nessuna firma nota trovata. Attivazione mappatura euristica universale."
            )

        return best_match

    def _smart_repair_logic(self, bad_line: list[str]) -> list[str]:
        if len(bad_line) > 2:
            return bad_line[:2] + [" ".join(bad_line[2:])]
        return bad_line

    def log_ingestion_error(self, error_type: str, details: str) -> None:
        self.log_error(f"[{error_type}] {details}")

    def process_file(
        self, file_content: bytes | io.BytesIO | Any, company_id: str
    ) -> list[Asset]:
        self.log_info(
            f"Avvio Motore di Ingestione Adattivo Universale per Company: {company_id}"
        )

        FORMATI_TABULARI = [".csv", ".xlsx", ".xls", ".txt"]
        nome_file = getattr(file_content, "name", "file_sconosciuto").lower()

        if not isinstance(file_content, (bytes, io.BytesIO)) and not any(
            nome_file.endswith(ext) for ext in FORMATI_TABULARI
        ):
            self.log_ingestion_error(
                "INVALID_FILE_FORMAT",
                f"Formato file non tabulare o non supportato: {nome_file}",
            )
            return []

        buffer = (
            io.BytesIO(file_content)
            if isinstance(file_content, bytes)
            else file_content
        )
        df = pd.DataFrame()

        try:
            buffer.seek(0)
            if nome_file.endswith((".xlsx", ".xls")):
                df = pd.read_excel(buffer, dtype=str)
            else:
                df = pd.read_csv(
                    buffer,
                    sep=None,
                    engine="python",
                    on_bad_lines=self._smart_repair_logic,
                    dtype=str,
                    encoding_errors="replace",
                )
        except Exception as e:
            try:
                buffer.seek(0)
                df = pd.read_excel(buffer, dtype=str)
            except Exception as inner_e:
                self.log_ingestion_error(
                    "CRITICAL_PARSING_FAILURE",
                    f"Errore di parsing (CSV: {e} | Excel: {inner_e})",
                )
                return []

        if df is None or df.empty:
            self.log_ingestion_error(
                "EMPTY_FILE", "Il file caricato non contiene dati o righe valide."
            )
            return []

        df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
        df = df.dropna(how="all")

        detected_system = self._detect_source_system(df.columns.tolist())
        settore = self.strategy.identify_sector(df.columns)

        assets: list[Asset] = []
        for idx, row in df.iterrows():
            try:
                raw_dict = row.dropna().to_dict()
                normalizzato = self._mappa_campi(raw_dict, idx)
                normalizzato["company_id"] = company_id
                normalizzato["source_system"] = detected_system

                asset = crea_asset_dal_dizionario(normalizzato, settore)
                if asset:
                    assets.append(asset)
            except Exception as e:
                self.log_ingestion_error(
                    "ASSET_CREATION_FAILURE",
                    f"Scartata riga {idx + 1} per errore di dominio: {e}",
                )

        if self.asset_repo and assets:
            try:
                for asset in assets:
                    self.asset_repo.save(asset)
                self.log_info(
                    f"Persistenza completata: {len(assets)} asset salvati sul repository."
                )
            except Exception as db_err:
                self.log_warning(
                    f"Errore non bloccante durante la persistenza su DB: {db_err}"
                )

        self.log_info(
            f"Ingestione completata con successo: {len(assets)} asset elaborati da {detected_system}."
        )
        return assets

    def _mappa_campi(self, raw_data: dict[str, Any], index: int) -> dict[str, Any]:
        pulito: dict[str, Any] = {}
        values_list = list(raw_data.values())

        if hasattr(SAP_FIELD_MAPPING, "items"):
            for sap_key, target in SAP_FIELD_MAPPING.items():
                for key, val in raw_data.items():
                    if str(key).strip().upper() == str(sap_key).strip().upper():
                        pulito[target] = val

        if hasattr(SINONIMI_MAPPING, "items"):
            for target, sinonimi in SINONIMI_MAPPING.items():
                if target not in pulito:
                    for key, val in raw_data.items():
                        clean_key = str(key).strip().lower()
                        if any(syn in clean_key for syn in sinonimi):
                            pulito[target] = val
                            break

        for key, val in raw_data.items():
            k_low = str(key).strip().lower()
            if (
                any(k in k_low for k in ["id", "cod", "sku", "articolo", "matnr"])
                and "id" not in pulito
            ):
                pulito["id"] = val
            elif (
                any(
                    k in k_low
                    for k in ["prodotto", "nome", "desc", "art", "materiale", "text"]
                )
                and "nome" not in pulito
            ):
                pulito["nome"] = val
            elif (
                any(k in k_low for k in ["qta", "quant", "giacenz", "stock", "labst"])
                and "quantita" not in pulito
            ):
                pulito["quantita"] = val
            elif (
                any(k in k_low for k in ["prezzo", "cost", "valore"])
                and "prezzo" not in pulito
            ):
                pulito["prezzo"] = val
            elif (
                any(k in k_low for k in ["rischio", "risk", "livello"])
                and "rischio" not in pulito
            ):
                pulito["rischio"] = val

        if not pulito.get("id"):
            pulito["id"] = f"AST-{index + 1}"

        if not pulito.get("nome"):
            for val in values_list:
                if isinstance(val, str) and len(str(val).strip()) > 1:
                    pulito["nome"] = str(val)
                    break
            if not pulito.get("nome"):
                pulito["nome"] = f"Asset_{index + 1}"

        if "quantita" not in pulito or pulito["quantita"] is None:
            pulito["quantita"] = 1.0
        else:
            try:
                pulito["quantita"] = float(pulito["quantita"])
            except (ValueError, TypeError):
                pulito["quantita"] = 1.0

        raw_rischio = pulito.get("rischio", 0.0)
        try:
            val_rischio_float = float(raw_rischio) if raw_rischio is not None else 0.0
            score_obj = RiscoScore(val_rischio_float)
            pulito["rischio"] = score_obj.value
        except (InvalidRiscoScoreException, ValueError, TypeError):
            try:
                numeric_fallback = (
                    float(raw_rischio) if raw_rischio is not None else 0.0
                )
                clamped_val = max(0.0, min(10.0, numeric_fallback))
                pulito["rischio"] = RiscoScore(clamped_val).value
            except Exception:
                pulito["rischio"] = 0.0

        pulito["dati_extra"] = raw_data
        return pulito

    def process_file_with_DTO(
        self, file_content: bytes, file_name: str, user_id: str, company_id: str
    ) -> FileIngestionResponseDTO:
        assets = self.process_file(file_content, company_id)

        return FileIngestionResponseDTO(
            success=len(assets) > 0,
            ingestion_id=f"ing-{pd.Timestamp.now().strftime('%Y%m%d%H%M%S')}",
            rows_processed=len(assets),
            rows_valid=len(assets),
            rows_rejected=0,
            assets_created=len(assets),
            assets_updated=0,
            errors=[],
            warnings=[],
        )
