"""
Domain Exceptions - Eccezioni di Dominio.
Eccezioni specifiche della logica di business.
"""


class DomainException(Exception):
    """Eccezione base per il dominio."""


class AssetException(DomainException):
    """Eccezione relativa agli Asset."""


class RiskException(DomainException):
    """Eccezione relativa al calcolo del rischio."""


class ValidationException(DomainException):
    """Eccezione di validazione."""


class InvalidRiscoScoreException(ValidationException):
    """Rischio score non valido (deve essere 0-10)."""


class InvalidAssetException(ValidationException):
    """Asset non valido."""


class AssetNotFound(DomainException):
    """Asset non trovato."""
