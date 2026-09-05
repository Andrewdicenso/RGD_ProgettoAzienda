"""
Supabase Connection - Gestore Cloud Enterprise RGD-Alpha.
Sostituisce SQLite con persistenza Cloud-Native e Logging professionale.
"""

import logging

from supabase import Client, create_client

from src.config.settings import get_settings  # <--- Usa il tuo sistema centralizzato

logger = logging.getLogger("RGD-Alpha.Database")


class DatabaseConnection:
    """
    Gestisce la connessione al database Cloud Supabase.
    Utilizza la configurazione centralizzata Settings.
    """

    def __init__(self):
        """Inizializza il client Supabase verificando le credenziali."""

        # Carichiamo i settings validati
        cfg = get_settings()

        self.url = cfg.SUPABASE_URL
        self.key = cfg.SUPABASE_KEY

        # Verifica robusta
        if not self.url or not self.key or "http" not in str(self.url):
            logger.critical(f"❌ Configurazione Supabase non valida. URL: {self.url}")
            raise ValueError(f"URL Supabase non valido o mancante: {self.url}")

        try:
            # Inizializzazione del client Supabase
            self.client: Client = create_client(self.url, self.key)
            logger.info("🛡️ Connessione Cloud Supabase stabilita con successo.")
        except Exception as e:
            logger.error(f"❌ Fallimento connessione Supabase: {e}")
            raise

    def get_client(self) -> Client:
        """Restituisce il client Supabase per le operazioni dei Repository."""
        return self.client
