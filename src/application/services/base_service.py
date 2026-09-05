"""
Base Service - Classe astratta base per tutti gli Application Services.
Fornisce logging centralizzato, gestione unificata delle eccezioni e contratti comuni.
"""

import logging
from abc import ABC


class BaseService(ABC):
    """
    Classe base per tutti i servizi applicativi di RGD-Alpha.
    Inizializza un logger dedicato e fornisce metodi Helper per la tracciabilità.
    """

    def __init__(self, service_name: str):
        """
        Inizializza il servizio base.

        Args:
            service_name: Nome del servizio (usato per la categoria dei log)
        """
        self.service_name = service_name
        self.logger = logging.getLogger(f"RGD-Alpha.{service_name}")

    def log_info(self, message: str) -> None:
        """Log a livello INFO."""
        self.logger.info(f"[{self.service_name}] {message}")

    def log_warning(self, message: str) -> None:
        """Log a livello WARNING."""
        self.logger.warning(f"[{self.service_name}] {message}")

    def log_debug(self, message: str) -> None:
        """Log a livello DEBUG."""
        self.logger.debug(f"[{self.service_name}] {message}")

    def log_error(self, message: str, exception: Exception | None = None) -> None:
        """
        Log a livello ERROR con tracciamento dello stack trace opzionale.

        Args:
            message: Messaggio descrittivo dell'errore
            exception: Eccezione catturata (opzionale)
        """
        if exception:
            self.logger.error(
                f"[{self.service_name}] {message} - Dettagli: {exception}",
            )
        else:
            self.logger.error(f"[{self.service_name}] {message}")
