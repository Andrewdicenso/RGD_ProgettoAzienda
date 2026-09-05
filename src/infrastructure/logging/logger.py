"""
Logger - Configurazione logging centralizzato.
"""

import logging
import sys
from pathlib import Path

from src.config import get_settings


def configure_logging() -> None:
    """Configura il logging per l'applicazione."""
    settings = get_settings()

    # Crea logger root
    root_logger = logging.getLogger("RGD-Alpha")
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL))

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.LOG_LEVEL))

    # Formatter
    formatter = logging.Formatter(settings.LOG_FORMAT)
    console_handler.setFormatter(formatter)

    # File handler
    log_file = Path(settings.LOG_DIR) / "application.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    file_handler = logging.FileHandler(str(log_file))
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Aggiungi handlers
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """
    Ottiene un logger per il modulo.

    Args:
        name: Nome del logger (__name__)

    Returns:
        Logger istanza
    """
    return logging.getLogger(name)
