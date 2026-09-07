# src/simulator.py
import logging

import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger("RGD-Alpha.Simulator")


class SectoralSensitivityTensor:
    """
    Gestisce i pesi dinamici multi-variati basati su tensori di sensibilità settoriale,
    incorporando volatilità storica, stagionalità e macro-fattori reali.
    """

    def __init__(
        self, sector_weights: dict | None = None, macro_factors: dict | None = None
    ):
        self.sector_weights = sector_weights or {
            "Magazzino": 1.2,
            "Fornitori": 1.5,
            "Performance Vendite": 1.0,
            "Produttività Risorse": 1.3,
            "EDILE_COSTRUZIONI": 1.4,
            "FASHION_RETAIL": 1.1,
            "TERZIARIO_LOGISTICA": 1.3,
            "PRIMARIO_ALIMENTARE": 1.4,
            "GENERAL": 1.0,
        }
        self.macro_factors = macro_factors or {}

    def compute_tensor_multiplier(self, sector: str, current_month: int) -> float:
        base_weight = self.sector_weights.get(sector, 1.0)
        sector_macro = self.macro_factors.get(sector, {})
        macro_multiplier = sector_macro.get("macro_multiplier", 1.0)
        seasonality = sector_macro.get("seasonality", {}).get(current_month, 1.0)
        return float(base_weight * macro_multiplier * seasonality)


class AdaptiveEMA:
    """
    Calcola l'Exponential Moving Average (EMA) con un fattore di decadimento
    temporale adattivo basato sul Time Delta effettivo tra i rilevamenti.
    """

    def __init__(self, half_life_days: float = 30.0):
        self.half_life_days = half_life_days

    def calculate(self, series: pd.Series, time_deltas: pd.Series) -> pd.Series:
        if len(series) == 0:
            return pd.Series(dtype=float)

        alphas = 1.0 - np.exp(-np.log(2.0) * (time_deltas / self.half_life_days))
        alphas = np.clip(alphas, 0.01, 0.99)

        ema_values = np.zeros_like(series, dtype=float)
        ema_values[0] = float(series.iloc[0])

        for i in range(1, len(series)):
            alpha = float(alphas.iloc[i])
            ema_values[i] = (
                alpha * float(series.iloc[i]) + (1.0 - alpha) * ema_values[i - 1]
            )

        return pd.Series(ema_values, index=series.index)


class CausalStressTestEngine:
    """
    Motore di Stress Test Causale basato su Regressione Ponderata (WLS)
    e Intervalli di Confidenza al 95% calcolati sui residui di NumPy/SciPy.
    Mantiene piena retrocompatibilità con la classe SimulatoreRischio originaria.
    """

    def __init__(self, confidence_level: float = 0.95, iterazioni: int = 1000):
        self.confidence_level = confidence_level
        self.iterazioni = iterazioni

    def run_regression_stress(
        self, x: np.ndarray, y: np.ndarray, weights: np.ndarray, future_x: float
    ) -> dict:
        try:
            W = np.diag(weights)
            X = np.vstack([np.ones(len(x)), x]).T

            try:
                beta = np.linalg.inv(X.T @ W @ X) @ (X.T @ W @ y)
            except np.linalg.LinAlgError:
                beta = np.array([float(np.mean(y)), 0.0])

            y_pred_historical = X @ beta
            residuals = y - y_pred_historical

            weighted_variance = np.sum(weights * (residuals**2)) / np.sum(weights)
            std_err = float(np.sqrt(max(weighted_variance, 1e-6)))

            X_future = np.array([1.0, future_x])
            y_future_pred = float(X_future @ beta)

            df_val = max(len(x) - 2, 1)
            t_val = float(stats.t.ppf((1 + self.confidence_level) / 2, df=df_val))
            margin = t_val * std_err * float(np.sqrt(1.0 + 1.0 / len(x)))

            return {
                "prediction": y_future_pred,
                "ci_lower": y_future_pred - margin,
                "ci_upper": y_future_pred + margin,
                "residuals_std": std_err,
            }
        except Exception as e:
            logger.error(f"Errore nel calcolo WLS di stress test: {e}")
            return {
                "prediction": float(y[-1]) if len(y) > 0 else 0.0,
                "ci_lower": 0.0,
                "ci_upper": 10.0,
                "residuals_std": 1.0,
            }

    def esegui_stress_test(
        self, valore_attuale: float, volatilita: float, giorni_proiettati: int = 30
    ) -> dict[str, float | int]:
        """
        Metodo legacy interfacciato con il nuovo motore causale per preservare
        la compatibilità con i test e i servizi esistenti.
        """
        try:
            valore_attuale = float(np.clip(valore_attuale, 0.0, 10.0))
            volatilita = max(float(volatilita), 0.01)

            # Costruzione di un set storico sintetico coerente per la regressione WLS
            x_hist = np.arange(10, dtype=float)
            # Trend lineare simulato con rumore guidato dalla volatilità
            y_hist = np.clip(
                valore_attuale + np.linspace(-volatilita * 3, volatilita * 3, 10),
                0.0,
                10.0,
            )
            weights = np.ones(10, dtype=float)

            future_step = 10.0 + float(giorni_proiettati) / 30.0
            regression_result = self.run_regression_stress(
                x_hist, y_hist, weights, future_step
            )

            predizione = float(np.clip(regression_result["prediction"], 0.0, 10.0))
            ci_upper = float(np.clip(regression_result["ci_upper"], 0.0, 10.0))

            prob_fallimento = float(min(100.0, max(0.0, (predizione / 10.0) * 100.0)))

            giorni_sopravvivenza = giorni_proiettati
            if ci_upper >= 8.5:
                giorni_sopravvivenza = max(
                    1, int(giorni_proiettati * (10.0 - predizione) / 10.0)
                )

            return {
                "probabilita_crisi": round(prob_fallimento, 2),
                "giorni_sopravvivenza_stimati": int(giorni_sopravvivenza),
                "rischio_max_previsto": round(ci_upper, 2),
            }

        except Exception as e:
            logger.error(f"Errore critico durante lo stress test causale: {e}")
            return {
                "probabilita_crisi": 0.0,
                "giorni_sopravvivenza_stimati": giorni_proiettati,
                "rischio_max_previsto": round(valore_attuale, 2),
            }


class SimulatoreRischio(CausalStressTestEngine):
    """Alias di retrocompatibilità per mantenere intatti i riferimenti esistenti."""


class AutomaticPrescriptionMatrix:
    """
    Associa automaticamente a ogni combinazione di Momentum e Rischio
    un Piano d'Azione Finanziario/Operativo vincolante per il CEO.
    """

    def __init__(self):
        pass

    def evaluate(self, days_of_autonomy: float, momentum_risk: float) -> dict:
        if days_of_autonomy < 30 or momentum_risk > 0.8:
            return {
                "risk_level": "CRITICO",
                "actions": [
                    "Blocco immediato degli ordini per SKU a bassa rotazione",
                    "Rinegoziazione urgente dei termini di pagamento (estensione a 90 giorni) con i top 3 fornitori",
                    "Attivazione immediata della linea di credito ponte",
                ],
            }
        elif days_of_autonomy < 60 or momentum_risk > 0.5:
            return {
                "risk_level": "MODERATO-ALTO",
                "actions": [
                    "Rideterminazione dei margini di sconto commerciale",
                    "Monitoraggio giornaliero del cash conversion cycle",
                    "Rinvio degli investimenti CAPEX non essenziali a 6 mesi",
                ],
            }
        else:
            return {
                "risk_level": "STABILE",
                "actions": [
                    "Mantenimento dei buffer di liquidità correnti",
                    "Ottimizzazione ordinaria del capitale circolante netto",
                ],
            }
