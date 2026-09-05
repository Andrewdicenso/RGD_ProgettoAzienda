"""
Ingestion Service - Use Case: Ingestione Dati Adattiva Enterprise.
Gestisce il parsing di file Excel/CSV/SAP con riparazione automatica,
normalizzazione dei sinonimi e conversione in entità di dominio.
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

logger = logging.getLogger("RGD-Alpha.IngestionService")


class IngestionService(BaseService):
    """
    Servizio di Ingestione Dati.
    Normalizza flussi di dati eterogenei (CSV, XLSX, Report SAP/ERP)
    trasformandoli in entità di dominio trasparenti per RGD-Alpha.
    """

    def __init__(self):
        super().__init__("IngestionService")
        self.strategy = AttentionMappingStrategy()

    def _smart_repair_logic(self, bad_line: list[str]) -> list[str]:
        """
        Logica di riparazione automatica per righe CSV malformate o contaminate.
        Unisce eventuali colonne extra derivanti da delimitatori errati.
        """
        if len(bad_line) > 2:
            fixed_line = bad_line[:2] + [" ".join(bad_line[2:])]
            return fixed_line
        return bad_line

    def log_ingestion_error(self, error_type: str, details: str) -> None:
        """Standardizzazione del logging per gli errori del motore di ingestione."""
        self.log_error(f"[{error_type}] {details}")

    def process_file(
        self, file_content: bytes | io.BytesIO | Any, company_id: str
    ) -> list[Asset]:
        """
        Esegue il protocollo completo di ingestione e parsing dati.

        Args:
            file_content: Buffer o contenuto in byte del file caricato
            company_id: ID dell'azienda proprietaria dei dati

        Returns:
            Lista di entità Asset valide create
        """
        self.log_info(f"Avvio Motore di Ingestione Adattivo per Company: {company_id}")

        # Normalizzazione del buffer di input
        if isinstance(file_content, bytes):
            buffer = io.BytesIO(file_content)
        else:
            buffer = file_content

        df: pd.DataFrame = pd.DataFrame()

        # 1. Parsing Flessibile con protezione RAM e Multi-Format
        try:
            buffer.seek(0)
            df = pd.read_excel(buffer)
        except Exception:
            try:
                buffer.seek(0)
                df = pd.read_csv(
                    buffer,
                    sep=None,
                    engine="python",
                    on_bad_lines=self._smart_repair_logic,
                    dtype=str,
                    encoding_errors="replace",
                )
            except Exception as e:
                self.log_ingestion_error("CRITICAL_PARSING_FAILURE", str(e))
                return []

        if df is None or df.empty:
            self.log_ingestion_error(
                "EMPTY_FILE", "Il file caricato non contiene dati o colonne valide."
            )
            return []

        # 2. Ottimizzazione Memoria e Pulizia Dati
        df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
        df = df.dropna(how="all")

        # Casting Tipi Numerici a precisione singola (float32) per risparmio memoria
        numeric_cols = [
            "rischio",
            "quantita",
            "prezzo",
            "livello_servizio",
            "volatilita",
        ]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").astype("float32")

        # 3. Identificazione Settore/Reparto tramite Strategy
        settore = self.strategy.identify_sector(df.columns)
        self.log_info(f"Settore e reparti rilevati: {settore.value}")

        # 4. Normalizzazione e Creazione Entità Asset
        assets: list[Asset] = []
        for _, row in df.iterrows():
            try:
                # Sostituzione dei valori NaN con valori predefiniti
                raw_dict = row.dropna().to_dict()
                normalizzato = self._mappa_campi(raw_dict)
                normalizzato["company_id"] = company_id

                asset = crea_asset_dal_dizionario(normalizzato, settore)
                if asset:
                    assets.append(asset)
            except Exception as e:
                self.log_ingestion_error(
                    "ASSET_CREATION_FAILURE",
                    f"Riga scartata a causa di un errore nei dati: {e}",
                )

        self.log_info(
            f"Ingestione completata: {len(assets)} asset generati con successo."
        )
        return assets

    def _mappa_campi(self, raw_data: dict[str, Any]) -> dict[str, Any]:
        """
        Applica i dizionari di traduzione SAP e i sinonimi di dominio.
        """
        pulito: dict[str, Any] = {}

        # Mappatura Sinonimi Standard
        if hasattr(SINONIMI_MAPPING, "items"):
            for target, sinonimi in SINONIMI_MAPPING.items():
                for key, val in raw_data.items():
                    if str(key).lower() in sinonimi:
                        pulito[target] = val
                        break

        # Mappatura Campi SAP/ERP se presenti
        if hasattr(SAP_FIELD_MAPPING, "items"):
            for sap_key, target in SAP_FIELD_MAPPING.items():
                for key, val in raw_data.items():
                    if str(key).upper() == sap_key.upper():
                        pulito[target] = val

        # Conserva tutti i dati grezzi originali in dati_extra per tracciabilità
        pulito["dati_extra"] = raw_data
        return pulito

    def process_file_with_dto(
        self, file_content: bytes, file_name: str, user_id: str, company_id: str
    ) -> FileIngestionResponseDTO:
        """
        Wrapper che esegue l'ingestione e restituisce un DTO strutturato per la UI.
        """
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
