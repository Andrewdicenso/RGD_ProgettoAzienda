import logging
import os

import pandas as pd
import torch
import torch.nn.functional as F

try:
    from src.database import DatabaseAziendale  # type: ignore[import-not-found]
    from src.entities import (  # type: ignore[import-not-found]
        AssetDiMercato,
        AssetDiRelazione,
        AssetDiValore,
        AssetStrategico,
    )
    from src.secure_vault import SecureVault  # type: ignore[import-not-found]
except (
    ImportError
):  # pragma: no cover - fallback for execution outside a package context
    from database import DatabaseAziendale  # type: ignore[reportMissingImports]
    from entities import (  # type: ignore[import-not-found]
        AssetDiMercato,
        AssetDiRelazione,
        AssetDiValore,
        AssetStrategico,
    )
    from secure_vault import SecureVault  # type: ignore[import-not-found]

logger = logging.getLogger("RGD-Alpha.Ingestor")


class IngestoreDati:
    def __init__(self, key_path="src/security/vault.key"):
        self.vault = SecureVault(key_path=key_path)
        self.db = DatabaseAziendale()

        # 1. DIZIONARIO DI TRADUZIONE SAP (Keys per il rilevamento del sistema sorgente)
        self.dizionario_sap = {
            "quantita": ["menge", "labst", "vclog"],
            "valore": ["netwr", "dmbtr", "waers", "knumv"],
            "nome": ["matnr", "maktx", "arktx"],
            "id_asset": ["belnr", "vbeln", "aufnr"],
        }

        self.mappa_sinonimi = {
            "quantita": [
                "quantita",
                "pezzi",
                "qta",
                "stock",
                "unita",
                "giacenza",
                "quantity",
                "vol",
                "qty",
            ],
            "valore": [
                "prezzo",
                "importo",
                "lordo",
                "valore",
                "costo",
                "ammontare",
                "costo_unitario",
                "prezzo_acquisto",
                "amount",
                "price",
                "netwr",
            ],
            "rischio": [
                "rischio",
                "impatto",
                "criticita",
                "priorita",
                "rischio_logistico",
                "risk_factor",
                "risk",
                "score",
            ],
            "stato": [
                "stato",
                "condizione",
                "status",
                "pagamento",
                "disponibilita",
                "stato_qualita",
                "level",
            ],
            "id_asset": [
                "codice",
                "id",
                "reference",
                "ref",
                "belnr",
                "matnr",
                "id_asset",
            ],
            "nome": [
                "descrizione",
                "prodotto",
                "materiale",
                "item",
                "nome",
                "asset",
                "maktx",
            ],
        }

        self.settori_keys = {
            "FINANCE": ["fattura", "iban", "lordo", "costo_unitario", "netwr", "dmbtr"],
            "LOGISTICS": [
                "bolla",
                "ddt",
                "magazzino",
                "quantita",
                "sku",
                "matnr",
                "menge",
                "labst",
            ],
            "RELATIONS": ["cliente", "fornitore", "crm", "kunnr", "lifnr"],
        }

        self.classi_valori = {
            "FINANCE": AssetDiValore,
            "LOGISTICS": AssetDiMercato,
            "RELATIONS": AssetDiRelazione,
            "GENERAL": AssetStrategico,
        }

    def _rileva_sorgente_sap(self, colonne):
        """
        Usa l'attenzione per capire se il file proviene da SAP.
        Ritorna True se la concentrazione di termini SAP è elevata.
        """
        colonne_lower = [str(c).lower() for c in colonne]
        punteggio_sap = 0
        totale_termini = 0

        for col in colonne_lower:
            for lista_sap in self.dizionario_sap.values():
                if col in lista_sap:
                    punteggio_sap += 1
            totale_termini += 1

        if totale_termini == 0:
            return False
        # Se più del 30% delle colonne usa la nomenclatura tipica SAP, lo classifichiamo come tale
        return (punteggio_sap / totale_termini) > 0.30

    def _calcola_attenzione_settore(self, colonne_file):
        """Identifica il settore (Logistica, Finance, ecc.) bilanciando termini standard e SAP"""
        punteggi_settori = {"FINANCE": 0.0, "LOGISTICS": 0.0, "RELATIONS": 0.0}

        for colonna in colonne_file:
            col_clean = str(colonna).lower()
            for settore, chiavi in self.settori_keys.items():
                for chiave in chiavi:
                    if chiave == col_clean:
                        punteggi_settori[settore] += 2.0  # Match esatto ha più peso
                    elif chiave in col_clean:
                        punteggi_settori[settore] += 1.0

        punteggi_tensor = torch.tensor(
            [list(punteggi_settori.values())], dtype=torch.float32
        )
        if punteggi_tensor.sum() == 0:
            return "GENERAL", self.classi_valori["GENERAL"]

        pesi_attenzione = F.softmax(punteggi_tensor, dim=-1).flatten()
        mappa_pesi = dict(zip(punteggi_settori.keys(), pesi_attenzione.tolist()))

        settore_scelto = max(mappa_pesi, key=mappa_pesi.get)
        if mappa_pesi[settore_scelto] < 0.45:
            return "GENERAL", self.classi_valori["GENERAL"]

        return settore_scelto, self.classi_valori[settore_scelto]

    def _normalizza_riga_intelligente(self, row, is_sap):
        """
        STRATO DI PULIZIA (ATTENTION-BASED CLEANING):
        Prende una riga grezza (anche complessa di SAP) e la mappa
        nei campi standard richiesti dalle entità del tuo software.
        """
        dati_puliti = row.to_dict()
        dizionario_riferimento = self.dizionario_sap if is_sap else self.mappa_sinonimi

        # Per ogni campo standard richiesto dal sistema, calcoliamo dove si concentra l'attenzione
        for campo_target, sinonimi in dizionario_riferimento.items():
            valore_trovato = None
            for colonna_reale in row.index:
                if str(colonna_reale).lower() in sinonimi:
                    valore_trovato = row[colonna_reale]
                    break

            if valore_trovato is not None and not pd.isna(valore_trovato):
                dati_puliti[campo_target] = valore_trovato

        # Garanzia per evitare i crash sui campi vitali delle entità
        dati_puliti["id_asset"] = dati_puliti.get("id_asset", row.get("id", "N/D"))
        dati_puliti["nome"] = dati_puliti.get("nome", row.get("nome", "Asset_Generico"))

        return dati_puliti

    def elabora_csv(self, file_path, company_id):
        asset_list = []
        if not os.path.exists(file_path):
            return asset_list

        try:
            if file_path.endswith(".csv"):
                df = pd.read_csv(file_path)
            elif file_path.endswith((".xlsx", ".xls")):
                df = pd.read_excel(file_path)
            else:
                return asset_list

            if df.empty:
                return asset_list

            # 1. RILEVAMENTO SORGENTE (È SAP oppure No?)
            is_sap = self._rileva_sorgente_sap(df.columns)
            if is_sap:
                logger.info(
                    f"Sorgente SAP rilevata con successo per il file {file_path}. Attivazione filtri di traduzione."
                )

            # 2. RILEVAMENTO REPARTO TRAMITE ATTENZIONE
            _settore_nome, ClasseAsset = self._calcola_attenzione_settore(df.columns)

            for _, row in df.iterrows():
                # 3. PULIZIA E NORMALIZZAZIONE DELLA RIGA
                # Qui convertiamo i codici SAP tipo 'MATNR' nel tuo campo pulito 'nome'
                dati_normalizzati = self._normalizza_riga_intelligente(row, is_sap)

                try:
                    nuovo_asset = ClasseAsset(**dati_normalizzati)
                    if hasattr(nuovo_asset, "genera_kpi_strategici"):
                        nuovo_asset.genera_kpi_strategici()

                    # Salva nel database aziendale per rendere i dati storici pronti per la predizione.
                    # Alcune implementazioni del database possono non fornire ancora questo hook:
                    # in tal caso l'ingestione continua producendo comunque gli asset.
                    salva_asset = getattr(self.db, "salva_asset", None)
                    if callable(salva_asset):
                        salva_asset(nuovo_asset, company_id)

                    asset_list.append(nuovo_asset)
                except Exception as e:
                    logger.debug(f"Salto riga per errore formato: {e}")

        except Exception as e:
            logger.error(f"Errore critico: {e}")

        return asset_list
