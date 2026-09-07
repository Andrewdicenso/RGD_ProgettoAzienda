# src/application/strategies/risk_analysis_strategy.py
from abc import ABC, abstractmethod

import numpy as np
import pandas as pd

from src.domain.entities import Asset
from src.domain.value_objects import RiscoScore
from src.simulator import AdaptiveEMA, CausalStressTestEngine


class RiskAnalysisStrategy(ABC):
    """Interfaccia astratta per le strategie di analisi del rischio."""

    @abstractmethod
    def calculate(self, asset: Asset, history: list[float]) -> RiscoScore:
        pass


class EMAProtocolStrategy(RiskAnalysisStrategy):
    """Implementazione basata su Media Mobile Esponenziale Adattiva (Momentum)."""

    def __init__(self, half_life_days: float = 30.0):
        self.adaptive_ema = AdaptiveEMA(half_life_days=half_life_days)

    def calculate(self, asset: Asset, history: list[float]) -> RiscoScore:
        if not history:
            return asset.rischio

        series = pd.Series(history)
        # Generazione di delta temporali uniformi o basati sull'indice se non forniti
        time_deltas = pd.Series(np.ones(len(history), dtype=float))

        ema_series = self.adaptive_ema.calculate(series, time_deltas)
        final_val = float(ema_series.iloc[-1])

        return RiscoScore(np.clip(final_val, 0.0, 10.0))


class LinearRegressionStrategy(RiskAnalysisStrategy):
    """Implementazione basata su Stress Test Causale WLS e Intervalli di Confidenza."""

    def __init__(self, confidence_level: float = 0.95):
        self.stress_engine = CausalStressTestEngine(confidence_level=confidence_level)

    def calculate(self, asset: Asset, history: list[float]) -> RiscoScore:
        if len(history) < 2:
            return asset.rischio

        x = np.arange(len(history), dtype=float)
        y = np.array(history, dtype=float)
        weights = np.ones(len(history), dtype=float)

        future_step = float(len(history))
        result = self.stress_engine.run_regression_stress(x, y, weights, future_step)

        prediction = float(result["prediction"])
        return RiscoScore(np.clip(prediction, 0.0, 10.0))
