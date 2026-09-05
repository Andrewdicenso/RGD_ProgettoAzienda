from abc import ABC, abstractmethod

from src.domain.entities import Asset
from src.domain.value_objects import RiscoScore


class RiskAnalysisStrategy(ABC):
    """Interfaccia astratta per le strategie di analisi del rischio."""

    @abstractmethod
    def calculate(self, asset: Asset, history: list[float]) -> RiscoScore:
        pass


class EMAProtocolStrategy(RiskAnalysisStrategy):
    """Implementazione basata su Media Mobile Esponenziale (Momentum)."""

    def calculate(self, asset: Asset, history: list[float]) -> RiscoScore:
        if not history:
            return asset.rischio
        # Calcolo EMA semplificato per RGD-Alpha
        ema = history[-1] * 0.7 + (sum(history) / len(history)) * 0.3
        return RiscoScore(ema)


class LinearRegressionStrategy(RiskAnalysisStrategy):
    """Implementazione basata su Regressione Lineare Predittiva."""

    def calculate(self, asset: Asset, history: list[float]) -> RiscoScore:
        import numpy as np

        if len(history) < 2:
            return asset.rischio
        x = np.arange(len(history))
        y = np.array(history)
        slope, intercept = np.polyfit(x, y, 1)
        # Previsione al prossimo step
        prediction = slope * (len(history)) + intercept
        return RiscoScore(prediction)
