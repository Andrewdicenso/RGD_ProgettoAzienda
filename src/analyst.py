# src/analyst.py
import numpy as np
import pandas as pd


class SectoralSensitivityTensor:
    """
    Gestisce i pesi dinamici multi-variati basati su tensori di sensibilità settoriale,
    incorporando volatilità storica, stagionalità e macro-fattori reali.
    """

    def __init__(self, sector_weights: dict, macro_factors: dict):
        self.sector_weights = sector_weights
        self.macro_factors = macro_factors

    def compute_tensor_multiplier(self, sector: str, current_month: int) -> float:
        base_weight = self.sector_weights.get(sector, 1.0)
        macro_multiplier = self.macro_factors.get(sector, {}).get(
            "macro_multiplier", 1.0
        )
        seasonality = (
            self.macro_factors.get(sector, {})
            .get("seasonality", {})
            .get(current_month, 1.0)
        )
        return base_weight * macro_multiplier * seasonality


class AdaptiveEMA:
    """
    Calcola l'Exponential Moving Average (EMA) con un fattore di decadimento
    temporale adattivo basato sul Time Delta effettivo tra i rilevamenti.
    """

    def __init__(self, half_life_days: float = 30.0):
        self.half_life_days = half_life_days

    def calculate(self, series: pd.Series, time_deltas: pd.Series) -> pd.Series:
        # time_deltas espresso in giorni tra un rilevamento e il successivo
        alphas = 1.0 - np.exp(-np.log(2.0) * (time_deltas / self.half_life_days))
        alphas = np.clip(alphas, 0.01, 0.99)

        ema_values = np.zeros_like(series, dtype=float)
        if len(series) == 0:
            return pd.Series(ema_values)

        ema_values[0] = series.iloc[0]
        for i in range(1, len(series)):
            alpha = alphas.iloc[i]
            ema_values[i] = alpha * series.iloc[i] + (1 - alpha) * ema_values[i - 1]

        return pd.Series(ema_values, index=series.index)
