# src/application/services/analysis_service.py
import logging
from datetime import datetime
from types import SimpleNamespace

import numpy as np
import pandas as pd

from src.application.services.base_service import BaseService
from src.domain.exceptions import InvalidRiscoScoreException
from src.domain.value_objects import RiscoScore
from src.infrastructure.security.vault import SecureVault
from src.simulator import (
    AdaptiveEMA,
    AutomaticPrescriptionMatrix,
    CausalStressTestEngine,
    SectoralSensitivityTensor,
)

logger = logging.getLogger(__name__)


class AnalysisService(BaseService):
    def __init__(self, kpi_repo=None, asset_repo=None):
        self.kpi_repo = kpi_repo
        self.asset_repo = asset_repo

        try:
            self.vault = SecureVault(key_path="src/infrastructure/security/vault.key")
        except Exception as e:
            logger.warning(f"Failed to initialize SecureVault: {e}")
            self.vault = None

        self.ORE_TEORICHE_ANNUE = 2080

        # Inizializzazione dei moduli Enterprise avanzati
        self.tensor_engine = SectoralSensitivityTensor()
        self.adaptive_ema_engine = AdaptiveEMA(half_life_days=30.0)
        self.stress_engine = CausalStressTestEngine()
        self.prescription_matrix = AutomaticPrescriptionMatrix()

    def _calcola_trend_momentum_alpha(self, val1, val2_o_list, w1=0.7, w2=0.3):
        if isinstance(val2_o_list, (list, tuple)):
            historical = val2_o_list
            r_oggi = val1
            if not historical:
                return "Stabile", 0.0, r_oggi

            diff = r_oggi - historical[0]
            trend_val = round(diff, 2)

            if trend_val > 0.5:
                momentum = "In Crescita"
            elif trend_val < -0.5:
                momentum = "In Calo"
            else:
                momentum = "Stabile"

            proj_30 = round(r_oggi + trend_val, 2)
            return momentum, trend_val, proj_30
        else:
            r_pesato = val1
            r_riferimento = val2_o_list
            m_score = round((r_pesato * w1) - (r_riferimento * w2), 2)
            return max(0.0, m_score)

    def analyze_asset_risk(self, asset, historical_risks=None):
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

        try:
            r_score_obj = RiscoScore(r_oggi_val)
            r_oggi_val = r_score_obj.value
        except InvalidRiscoScoreException:
            r_score_obj = RiscoScore(max(0.0, min(10.0, r_oggi_val)))
            r_oggi_val = r_score_obj.value

        if historical_risks:
            momentum, trend_val, proj_30 = self._calcola_trend_momentum_alpha(
                r_oggi_val, historical_risks
            )
        else:
            momentum, trend_val, proj_30 = "Stabile", 0.0, r_oggi_val

        diff = r_oggi_val - (historical_risks[0] if historical_risks else r_oggi_val)
        if diff > 1.0:
            trend_str = "ACCELERATING"
        elif diff < -1.0:
            trend_str = "DECELERATING"
        else:
            trend_str = "STABLE"

        proj_30 = min(10.0, max(0.0, round(proj_30, 2)))

        # Sfruttiamo il motore di stress test causale per proiezioni a 60 e 90 giorni più robuste
        stress_res_60 = self.stress_engine.esegui_stress_test(
            proj_30, volatilita=0.15, giorni_proiettati=30
        )
        proj_60 = min(10.0, max(0.0, float(stress_res_60["rischio_max_previsto"])))

        stress_res_90 = self.stress_engine.esegui_stress_test(
            proj_60, volatilita=0.18, giorni_proiettati=30
        )
        proj_90 = min(10.0, max(0.0, float(stress_res_90["rischio_max_previsto"])))

        is_critical = (
            r_score_obj.is_critical
            or proj_30 >= 7.0
            or getattr(asset, "is_critical", False)
        )

        if is_critical and (trend_str == "ACCELERATING" or r_score_obj.value >= 8.0):
            urgenza = "IMMEDIATE"
        elif is_critical or trend_str == "ACCELERATING":
            urgenza = "HIGH"
        elif trend_str == "STABLE" and r_score_obj.value > 4.0:
            urgenza = "MEDIUM"
        else:
            urgenza = "NORMAL"

        return SimpleNamespace(
            asset_id=asset_id,
            score=r_score_obj.value,
            rischio_attuale=r_score_obj.value,
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
        if len(valori_rischio) < 2:
            return 0.0
        return round(float(np.std(valori_rischio)), 2)

    def _genera_consiglio_azione(self, rischio, settore, m_score=0):
        days_dummy = max(10, int(100 - (rischio * 10)))
        prescrizione = self.prescription_matrix.evaluate(
            days_dummy, float(m_score) / 2.0
        )

        actions_str = " | ".join(prescrizione.get("actions", []))
        level = prescrizione.get("risk_level", "STABILE")

        alert = f" ⚠️ [Livello: {level}]" if rischio > 5.0 else ""
        return f"{actions_str}{alert}"

    def _analizza_e_configura_motore(self, contesto, colonne):
        contesto_upper = str(contesto).upper()
        if "EDILE" in contesto_upper:
            return {
                "settore": "EDILE_COSTRUZIONI",
                "soglia": 7.5,
                "moltiplicatore": self.tensor_engine.compute_tensor_multiplier(
                    "EDILE_COSTRUZIONI", datetime.now().month
                ),
            }
        if "FASHION" in contesto_upper:
            return {
                "settore": "FASHION_RETAIL",
                "soglia": 7.0,
                "moltiplicatore": self.tensor_engine.compute_tensor_multiplier(
                    "FASHION_RETAIL", datetime.now().month
                ),
            }
        if "LOGIST" in contesto_upper or "MAGAZZINO" in contesto_upper:
            return {
                "settore": "TERZIARIO_LOGISTICA",
                "soglia": 7.0,
                "moltiplicatore": self.tensor_engine.compute_tensor_multiplier(
                    "TERZIARIO_LOGISTICA", datetime.now().month
                ),
            }
        if "ALIMENT" in contesto_upper:
            return {
                "settore": "PRIMARIO_ALIMENTARE",
                "soglia": 6.5,
                "moltiplicatore": self.tensor_engine.compute_tensor_multiplier(
                    "PRIMARIO_ALIMENTARE", datetime.now().month
                ),
            }
        return {
            "settore": "GENERAL",
            "soglia": 7.0,
            "moltiplicatore": self.tensor_engine.compute_tensor_multiplier(
                "GENERAL", datetime.now().month
            ),
        }

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
        config.get("soglia", 7.0)
        moltiplicatore = config.get("moltiplicatore", 1.0) * fattore_stress

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
                r_base = round(
                    10.0 / (1.0 + np.exp(-15.0 * (rapporto_perdita - 0.15))), 2
                )
            else:
                r_base = d.get("rischio", 1.0)

            r_pesato = round(r_base * moltiplicatore, 2)

            try:
                r_pesato_obj = RiscoScore(r_pesato)
            except InvalidRiscoScoreException:
                r_pesato_obj = RiscoScore(max(0.0, min(10.0, r_pesato)))

            r_pesato_val = r_pesato_obj.value

            m_score = self._calcola_trend_momentum_alpha(
                r_pesato_val, r_base * 0.85, w1=weights[0], w2=weights[1]
            )

            if r_pesato_obj.is_critical:
                stato = "CRITICO"
            elif r_pesato_obj.is_safe:
                stato = "OTTIMALE"
            else:
                stato = "ATTENZIONE"

            consiglio_generato = self._genera_consiglio_azione(
                r_pesato_val, settore_rilevato, m_score
            )

            report.append(
                {
                    "asset": nome,
                    "stato": stato,
                    "rischio": r_pesato_val,
                    "momentum_score": m_score,
                    "consiglio_strategico": consiglio_generato,
                    "consiglio": consiglio_generato,  # Retrocompatibilità UI
                    "insight": consiglio_generato,  # Retrocompatibilità UI
                    "settore": settore_rilevato,
                    "alert": (
                        "🚨 STRESS TEST ATTIVO" if fattore_stress > 1.0 else "Nominale"
                    ),
                }
            )
            self._archivia_asset(d, r_pesato_val, str(m_score))
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
                        "consiglio": f"🚨 BLOCCATI {giorni}gg. Applica sconto {int(sconto * 100)}%\u200b.",
                    }
                )
        return proposte

    def _archivia_asset(self, d, rischio, momentum_str="Stabile"):
        try:
            if self.kpi_repo:
                self.kpi_repo.record_kpi(
                    asset_id=d.get("id", d.get("nome")),
                    risk_value=rischio,
                    metadata={
                        "tipo": d.get("tipo", "Enterprise"),
                        "momentum": momentum_str,
                    },
                )
            elif self.asset_repo:
                pass
        except Exception as e:
            logger.warning(f"DB Sync fallito tramite repository: {e}")

    def salva_report_certificato(self, report_data):
        if not report_data:
            return False
        logger.info("Report salvato con successo (stub).")
        return True
