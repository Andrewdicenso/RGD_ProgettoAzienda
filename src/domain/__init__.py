"""
Domain Module - Logica Pura di Business.
Contiene: Entità, Value Objects, Rules, Exceptions.
Zero dipendenze da Infrastructure/Application.
"""

from .constants import (
    SAP_FIELD_MAPPING,
    SETTORE_KEYS,
    SINONIMI_MAPPING,
    AssetCategory,
    InventoryStatus,
    MomentumStatus,
    PaymentStatus,
    RiskLevel,
    UserRole,
)
from .entities import (
    Asset,
    AssetDiMercato,
    AssetDiRelazione,
    AssetDiValore,
    Azienda,
    Utente,
    crea_asset_dal_dizionario,
)
from .exceptions import (
    AssetException,
    AssetNotFound,
    DomainException,
    InvalidAssetException,
    InvalidRiscoScoreException,
    RiskException,
    ValidationException,
)
from .value_objects import Momentum, PeriodoTemporale, RiscoScore, Volatilita

__all__ = [
    "SAP_FIELD_MAPPING",
    "SETTORE_KEYS",
    "SINONIMI_MAPPING",
    # Entities
    "Asset",
    # Constants
    "AssetCategory",
    "AssetDiMercato",
    "AssetDiRelazione",
    "AssetDiValore",
    "AssetException",
    "AssetNotFound",
    "Azienda",
    # Exceptions
    "DomainException",
    "InvalidAssetException",
    "InvalidRiscoScoreException",
    "InventoryStatus",
    "Momentum",
    "MomentumStatus",
    "PaymentStatus",
    "PeriodoTemporale",
    # Value Objects
    "RiscoScore",
    "RiskException",
    "RiskLevel",
    "UserRole",
    "Utente",
    "ValidationException",
    "Volatilita",
    "crea_asset_dal_dizionario",
]
