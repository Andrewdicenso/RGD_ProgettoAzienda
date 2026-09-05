import logging
from datetime import datetime
from types import SimpleNamespace

import numpy as np
import pandas as pd

# Moduli AI e DTO
from src.application.services.base_service import BaseService
from src.infrastructure.security.vault import SecureVault

logger = logging.getLogger(__name__)


class AnalysisService(BaseService):
    def __init__(self, kpi_repo=None, asset_repo=None):
        """Inizializza il servizio ricevendo i repository dal container."""
        self.kpi_repo = kpi_repo
        self.asset_repo = asset_repo

        try:
            self.vault = SecureVault(key_path="src/infrastructure/security/vault.key")
        except Exception as e:
            logger.warning(f"Failed to initialize SecureVault: {e}")
            self.vault = None

        self.ORE_TEORICHE_ANNUE = 2080
        self.pesi_contesto = {
            "Magazzino": 1.2,
            "Fornitori": 1.5,
            "Performance Vendite": 1.0,
            "Produttività Risorse": 1.3,
            "EDILE": 1.4,
            "FASHION": 1.1,
            "UNIVERSAL": 1.0,
        }

    def _calcola_trend_momentum_alpha(self, val1, val2_o_list, w1=0.7, w2=0.3):
        """
        Metodo di calcolo unificato per trend e momentum compatibile con entrambe le chiamate.
        """
        # Caso 1: Chiamata con lista storica (da analyze_asset_risk)
        if isinstance(val2_o_list, (list, tuple)):
            historical = val2_o_list
            r_oggi = val1
            if not historical:
                return "Stabile", 0.0, r_oggi

            diff = r_oggi - historical[-1]
            trend_val = round(diff, 2)

            if trend_val > 0.5:
                momentum = "In Crescita"
            elif trend_val < -0.5:
                momentum = "In Calo"
            else:
                momentum = "Stabile"

            proj_30 = round(r_oggi + trend_val, 2)
            return momentum, trend_val, proj_30

        # Caso 2: Chiamata con due valori numerici e pesi (da esegui_scan_strategico)
        else:
            r_pesato = val1
            r_riferimento = val2_o_list
            m_score = round((r_pesato * w1) - (r_riferimento * w2), 2)
            return max(0.0, m_score)

    def analyze_asset_risk(self, asset, historical_risks=None):
        """Analizza il rischio di un asset e restituisce un DTO completo per la suite di test."""
        if historical_risks is None:
            historical_risks = []

        asset_id = getattr(asset, "id", "unknown")

        r_oggi = getattr(asset, "rischio", None)
        if r_oggi is None:
            r_oggi_val = 0.0
        elif hasattr(r_oggi, "value"):
            r_oggi_val = float(r_oggi.value)
        else:
            r_oggi_val = float(r_oggi)

        if historical_risks:
            momentum, trend_val, proj_30 = self._calcola_trend_momentum_alpha(
                r_oggi_val, historical_risks
            )
        else:
            momentum, trend_val, proj_30 = "Stabile", 0.0, r_oggi_val

        # Determinazione del trend formattato per il test
        diff = r_oggi_val - (historical_risks[0] if historical_risks else r_oggi_val)
        if diff > 1.0:
            trend_str = "ACCELERATING"
        elif diff < -1.0:
            trend_str = "DECELERATING"
        else:
            trend_str = "STABLE"

        is_critical = r_oggi_val >= 7.0 or getattr(asset, "is_critical", False)
        urgenza = "IMMEDIATE" if is_critical else "NORMAL"

        # Calcolo proiezioni incrementali a 60 e 90 giorni
        proj_60 = round(proj_30 + max(0.0, trend_val), 2)
        proj_90 = round(proj_60 + max(0.0, trend_val), 2)

        return SimpleNamespace(
            asset_id=asset_id,
            score=r_oggi_val,
            rischio_attuale=r_oggi_val,
            trend_value=trend_val,
            trend=trend_str,
            momentum=momentum,
            rischio_proiezione_30gg=proj_30,
            rischio_proiezione_60gg=proj_60,
            rischio_proiezione_90gg=proj_90,
            urgenza=urgenza,
            is_critical=is_critical,
        )

    def mappa_colonne_universale(self, df):
        """
        Rileva e rinomina automaticamente le colonne provenienti da qualsiasi ERP/CRM.
        Non interrompe il flusso: se non trova nulla, restituisce il df originale.
        """
        import difflib

        colonne_target = {
            "nome": [
                "Work Center",
                "Reparto",
                "Cantiere",
                "Asset",
                "Macchina",
                "Project",
                "Account Name",
                "Name",
            ],
            "rischio": [
                "Risk",
                "Criticality",
                "Priorità",
                "Livello",
                "Grado",
                "Pericolo",
                "Priority Score",
                "Rischio",
            ],
            "ore_produttive_effettive": [
                "Hours",
                "Ore",
                "Tempo",
                "Effort",
                "Lavorate",
                "Actual Hours",
                "h",
            ],
            "tipo": [
                "Type",
                "Category",
                "Categoria",
                "Genere",
                "Resource Group",
                "Tipo",
            ],
            "stato": ["Status", "Stato", "Health", "Fase", "Current State"],
            "timestamp": [
                "Data",
                "Date",
                "Timestamp",
                "Data Caricamento",
                "Inizio",
                "Giorno",
            ],
        }
        colonne_file = list(df.columns)
        mappa_finale = {}

        for target, sinonimi in colonne_target.items():
            for col in colonne_file:
                if (
                    col.lower() in [s.lower() for s in sinonimi]
                    or col.lower() == target
                ):
                    mappa_finale[col] = target
                    break
            if target not in mappa_finale.values():
                matches = difflib.get_close_matches(
                    target, colonne_file, n=1, cutoff=0.5
                )
                if matches:
                    mappa_finale[matches[0]] = target

        return df.rename(columns=mappa_finale)

    def calcola_volatilita_sistema(self, valori_rischio):
        """
        Rileva instabilità nei dati caricati (Anomalie di Governance).
        """
        if len(valori_rischio) < 2:
            return 0.0
        return round(np.std(valori_rischio), 2)

    def _genera_consiglio_azione(self, rischio, settore, m_score=0):
        alert = " ⚠️ ACCELERAZIONE CRITICA!" if m_score > 1.5 else ""
        if rischio > 8:
            consigli = {
                "PRIMARIO_ALIMENTARE": "🚨 BLOCCO LOTTI: Rischio sanitario/scadenza. Isolare stock.",
                "EDILE_COSTRUZIONI": "🚨 FERMO CANTIERE: Rischio penali elevato. Verificare subappalti.",
                "TERZIARIO_LOGISTICA": "🚨 LIQUIDAZIONE: Saturazione spazi. Liberare magazzino ora.",
                "FASHION_RETAIL": "🚨 OUTLET IMMEDIATO: Merce fuori stagione. Recuperare capitale.",
            }
            return (
                consigli.get(
                    settore, "🚨 EMERGENZA: Azione correttiva richiesta entro 24h."
                )
                + alert
            )
        elif rischio > 5:
            return (
                f"⚠️ MONITORAGGIO: Settore {settore} in allerta. Revisione parametri settimanale."
                + alert
            )
        return "✅ NOMINALE: Proseguire secondo pianificazione."

    def _analizza_e_configura_motore(self, contesto, colonne):
        contesto_upper = str(contesto).upper()
        if "EDILE" in contesto_upper:
            return {
                "settore": "EDILE_COSTRUZIONI",
                "soglia": 7.5,
                "moltiplicatore": 1.2,
            }
        if "FASHION" in contesto_upper:
            return {
                "settore": "FASHION_RETAIL",
                "soglia": 7.0,
                "moltiplicatore": 1.1,
            }
        if "LOGIST" in contesto_upper or "MAGAZZINO" in contesto_upper:
            return {
                "settore": "TERZIARIO_LOGISTICA",
                "soglia": 7.0,
                "moltiplicatore": 1.3,
            }
        if "ALIMENT" in contesto_upper:
            return {
                "settore": "PRIMARIO_ALIMENTARE",
                "soglia": 6.5,
                "moltiplicatore": 1.4,
            }
        return {"settore": "GENERAL", "soglia": 7.0, "moltiplicatore": 1.0}

    def esegui_scan_strategico(
        self, lista_asset, contesto, fattore_stress=1.0, weights=(0.7, 0.3)
    ):
        colonne = []
        if lista_asset:
            colonne = (
                list(lista_asset[0].keys())
                if isinstance(lista_asset[0], dict)
                else list(vars(lista_asset[0]).keys())
            )

        config = self._analizza_e_configura_motore(contesto, colonne)
        settore_rilevato = config.get("settore", "GENERAL")
        soglia = config.get("soglia", 7.0)
        moltiplicatore = (
            config.get("moltiplicatore", 1.0)
            * self.pesi_contesto.get(contesto, 1.0)
            * fattore_stress
        )

        report = []
        for asset in lista_asset:
            d = asset if isinstance(asset, dict) else vars(asset)
            nome = d.get("nome", d.get("asset", "Asset"))
            r_base = d.get("rischio", 0.0)

            voci_perdita = [
                "ferie",
                "festivita",
                "assenze",
                "permessi",
                "ritardi",
                "micropause",
            ]
            ore_p = sum([float(d.get(k, 0)) for k in voci_perdita])

            if ore_p > 0:
                rapporto_perdita = ore_p / self.ORE_TEORICHE_ANNUE
                r_base = round(10 / (1 + np.exp(-15 * (rapporto_perdita - 0.15))), 2)
            else:
                r_base = d.get("rischio", 1.0)

            r_pesato = round(r_base * moltiplicatore, 2)
            m_score = self._calcola_trend_momentum_alpha(
                r_pesato, r_base * 0.85, w1=weights[0], w2=weights[1]
            )
            stato = (
                "CRITICO"
                if r_pesato > soglia
                else "OTTIMALE"
                if r_pesato < 5
                else "ATTENZIONE"
            )

            report.append(
                {
                    "asset": nome,
                    "stato": stato,
                    "rischio": r_pesato,
                    "momentum_score": m_score,
                    "consiglio_strategico": self._genera_consiglio_azione(
                        r_pesato, settore_rilevato, m_score
                    ),
                    "settore": settore_rilevato,
                    "alert": (
                        "🚨 STRESS TEST ATTIVO" if fattore_stress > 1.0 else "Nominale"
                    ),
                }
            )
            self._archivia_asset(d, r_pesato, str(m_score))
        return report

    def analizza_giacenze_e_proponi_marketing(self, df):
        proposte = []
        oggi = datetime.now()
        if df is None or df.empty:
            return proposte
        for _, row in df.iterrows():
            if "timestamp" not in row or pd.isna(row["timestamp"]):
                continue
            giorni = (oggi - pd.to_datetime(row["timestamp"])).days
            if giorni > 30:
                rischio, valore = row.get("rischio", 0.0), row.get("valore_extra", 0.0)
                sconto = 0.4 if rischio > 7 else 0.2
                proposte.append(
                    {
                        "asset": row.get("nome"),
                        "giorni": giorni,
                        "recupero_stimato": f"€ {round(valore * (1 - sconto), 2)}",
                        "consiglio": f"🚨 BLOCCATI {giorni}gg. Applica sconto {int(sconto * 100)}%.",
                    }
                )
        return proposte

    def _archivia_asset(self, d, rischio, momentum_str="Stabile"):
        try:
            self.db.salva_asset(
                user_id=d.get("user_id", 1),
                nome_asset=d.get("nome"),
                rischio=rischio,
                tipo=d.get("tipo", "Enterprise"),
                momentum=momentum_str,
                volatilita=0.0,
            )
        except Exception as e:
            logger.warning(f"DB Sync fallito: {e}")

    def salva_report_certificato(self, report_data):
        if not report_data:
            return False
        logger.info("Report salvato con successo (stub).")
        return True
