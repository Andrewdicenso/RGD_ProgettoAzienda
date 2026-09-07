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

logger = logging.getLogger("RGD-Alpha.IngestionService")


class IngestionService(BaseService):
    """
    Servizio di Ingestione Dati Adattivo ed Enterprise.
    Identifica automaticamente la sorgente (SAP, ERP custom, file standard),
    normalizza i flussi eterogenei e li trasforma in entità di dominio trasparenti per RGD-Alpha.
    """

    def __init__(self):
        super().__init__("IngestionService")
        self.strategy = AttentionMappingStrategy()

        # Database esteso delle firme digitali dei sistemi gestionali di mercato (Fingerprinting)
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

    def _detect_source_system(self, columns: list[str]) -> str:
        """
        Riconosce automaticamente il sistema gestionale di provenienza in base alle intestazioni.
        """
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
                f"[ERP Fingerprint] Sorgente aziendale identificata con successo: {best_match} (Match score: {max_matches})"
            )
        else:
            self.log_info(
                "[ERP Fingerprint] Nessuna firma nota trovata. Attivazione mappatura euristica universale."
            )

        return best_match

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
        Esegue il protocollo completo di ingestione, rilevamento sorgente e parsing dati.

        Args:
            file_content: Buffer o contenuto in byte del file caricato
            company_id: ID dell'azienda proprietaria dei dati

        Returns:
            Lista di entità Asset valide create
        """
        self.log_info(
            f"Avvio Motore di Ingestione Adattivo Universale per Company: {company_id}"
        )

        # Normalizzazione del buffer di input
        if isinstance(file_content, bytes):
            buffer = io.BytesIO(file_content)
        else:
            buffer = file_content

        df: pd.DataFrame = pd.DataFrame()

        # 1. Parsing Flessibile Multi-Format (CSV prioritario o Excel intelligente)
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
        except Exception:
            try:
                buffer.seek(0)
                df = pd.read_excel(buffer, dtype=str)
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

        # Riconoscimento automatico del sistema sorgente tramite le colonne
        detected_system = self._detect_source_system(df.columns.tolist())
        self.log_info(f"Sistema di origine rilevato: {detected_system}")

        # Casting Tipi Numerici a precisione singola (float32) per risparmio memoria
        numeric_cols = [
            "rischio",
            "quantita",
            "prezzo",
            "costo",
            "valore",
            "livello_servizio",
            "volatilita",
        ]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").astype("float32")

        # 3. Identificazione Settore/Reparto tramite Strategy
        settore = self.strategy.identify_sector(df.columns)
        self.log_info(
            f"Settore e reparti rilevati: {settore.value if hasattr(settore, 'value') else settore}"
        )

        # 4. Normalizzazione Semantica e Creazione Entità Asset
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
                    f"Riga scartata a causa di un errore nei dati: {e}",
                )

        self.log_info(
            f"Ingestione completata: {len(assets)} asset generati con successo dal sistema {detected_system}."
        )
        return assets

    def _mappa_campi(self, raw_data: dict[str, Any], index: int) -> dict[str, Any]:
        """
        Applica i dizionari di traduzione SAP, i sinonimi di dominio,
        il fuzzy matching semantico e il fallback posizionale di sicurezza.
        """
        pulito: dict[str, Any] = {}
        values_list = list(raw_data.values())

        # 1. Mappatura Campi SAP/ERP se presenti
        if hasattr(SAP_FIELD_MAPPING, "items"):
            for sap_key, target in SAP_FIELD_MAPPING.items():
                for key, val in raw_data.items():
                    if str(key).strip().upper() == str(sap_key).strip().upper():
                        pulito[target] = val

        # 2. Mappatura Sinonimi Standard
        if hasattr(SINONIMI_MAPPING, "items"):
            for target, sinonimi in SINONIMI_MAPPING.items():
                if target not in pulito:
                    for key, val in raw_data.items():
                        clean_key = str(key).strip().lower()
                        if any(syn in clean_key for syn in sinonimi):
                            pulito[target] = val
                            break

        # 3. Fallback semantico euristico avanzato per coprire colonne come 'prodotto' o 'magazzino'
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

        # 4. Fallback Posizionale e di Sicurezza (Evita scarti e garantisce ID/Nome validi)
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
        if "rischio" not in pulito or pulito["rischio"] is None:
            pulito["rischio"] = 0.0

        # Conserva tutti i dati grezzi originali in dati_extra per tracciabilità totale
        pulito["dati_extra"] = raw_data
        return pulito

    def process_file_with_dto(
        self, file_content: bytes, file_name: str, user_id: str, company_id: str
    ) -> FileIngestionResponseDTO:
        """
        Wrapper che esegue l'ingestione universale e restituisce un DTO strutturato per la UI della War Room.
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
