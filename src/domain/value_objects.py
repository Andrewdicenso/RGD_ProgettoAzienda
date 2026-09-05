"""
Domain Value Objects - Valori immutabili e logica di dominio.
Value Objects incapsulano la logica di business.
"""

from dataclasses import dataclass

from .constants import MomentumStatus, RiskLevel
from .exceptions import InvalidRiscoScoreException


@dataclass(frozen=True)
class RiscoScore:
    """
    Value Object per il punteggio di rischio.
    Immutabile, encapsula logica e validazione.
    Range: 0.0 - 10.0
    """

    value: float

    def __post_init__(self):
        """Validazione al momento della creazione."""
        if not (0 <= self.value <= 10):
            raise InvalidRiscoScoreException(
                f"RiscoScore deve essere tra 0 e 10, ricevuto: {self.value}"
            )

    @property
    def level(self) -> RiskLevel:
        """Ritorna il livello di rischio categorizzato."""
        if self.value >= 7.5:
            return RiskLevel.CRITICAL
        elif self.value >= 5.0:
            return RiskLevel.WARNING
        else:
            return RiskLevel.SAFE

    @property
    def is_critical(self) -> bool:
        """Vero se rischio critico (>= 7.5)."""
        return self.value >= 7.5

    @property
    def is_warning(self) -> bool:
        """Vero se rischio in avvertenza (5.0 - 7.5)."""
        return 5.0 <= self.value < 7.5

    @property
    def is_safe(self) -> bool:
        """Vero se rischio basso (< 5.0)."""
        return self.value < 5.0

    def __str__(self) -> str:
        return f"{self.value:.1f}/10 [{self.level.value}]"


@dataclass(frozen=True)
class Momentum:
    """
    Value Object per il momentum (accelerazione/decelerazione).
    Incapsula il trend del rischio nel tempo.
    """

    status: MomentumStatus
    value: float  # Pendenza trend (-1.0 a +1.0)

    @property
    def is_accelerating(self) -> bool:
        """Vero se il rischio sta accelerando."""
        return self.status == MomentumStatus.ACCELERATING

    @property
    def is_decelerating(self) -> bool:
        """Vero se il rischio sta decelerando."""
        return self.status == MomentumStatus.DECELERATING

    @property
    def is_stable(self) -> bool:
        """Vero se il rischio è stabile."""
        return self.status == MomentumStatus.STABLE

    def __str__(self) -> str:
        return f"{self.status.value} (trend: {self.value:+.2f})"


@dataclass(frozen=True)
class Volatilita:
    """
    Value Object per la volatilità storica del rischio.
    Misura la variabilità del rischio nel tempo.
    """

    value: float  # Deviazione standard (0.0 - 5.0)

    @property
    def is_volatile(self) -> bool:
        """Vero se volatilità alta (> 2.0)."""
        return self.value > 2.0

    @property
    def is_stable(self) -> bool:
        """Vero se volatilità bassa (< 1.0)."""
        return self.value < 1.0

    def __str__(self) -> str:
        return f"σ={self.value:.2f}"


@dataclass(frozen=True)
class PeriodoTemporale:
    """
    Value Object per un periodo temporale.
    """

    anno: int
    mese: int  # 1-12

    def __post_init__(self):
        """Validazione."""
        if not (1 <= self.mese <= 12):
            raise ValueError(f"Mese non valido: {self.mese}")

    def __str__(self) -> str:
        return f"{self.mese:02d}/{self.anno}"
