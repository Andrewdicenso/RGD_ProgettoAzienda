"""
Base Repository - Classe astratta base per tutti i repository.
Definisce l'interfaccia per accesso ai dati.
"""

import logging
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    """Repository pattern base class."""

    def __init__(self, name: str):
        """
        Inizializza il repository.

        Args:
            name: Nome del repository (per logging)
        """
        self.logger = logging.getLogger(f"RGD-Alpha.{name}Repository")
        self.name = name

    @abstractmethod
    def create(self, entity: T) -> T:
        """Crea una nuova entity."""

    @abstractmethod
    def read(self, id: str) -> T | None:
        """Legge un entity per ID."""

    @abstractmethod
    def update(self, entity: T) -> T:
        """Aggiorna un entity."""

    @abstractmethod
    def delete(self, id: str) -> bool:
        """Cancella un entity."""

    @abstractmethod
    def list_all(self) -> list[T]:
        """Lista tutte le entities."""

    def log_info(self, msg: str) -> None:
        """Log info level."""
        self.logger.info(msg)

    def log_error(self, msg: str, exc: Exception | None = None) -> None:
        """Log error level."""
        if exc:
            self.logger.error(msg, exc_info=exc)
        else:
            self.logger.error(msg)
