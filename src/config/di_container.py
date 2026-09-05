"""
DI Container - Dependency Injection Container per RGD-Alpha.
Gestisce l'istanziazione delle dependencies in modo centralizzato.
"""

import logging
from typing import Any

from .settings import Settings, get_settings

logger = logging.getLogger("RGD-Alpha.DIContainer")


class DIContainer:
    """
    Contenitore di Dipendenze.

    Uso:
        container = DIContainer()
        asset_service = container.get_asset_service()
        analysis_service = container.get_analysis_service()
    """

    def __init__(self, settings: Settings | None = None):
        """
        Inizializza il container.

        Args:
            settings: Settings instance (default: get_settings())
        """
        self.settings = settings or get_settings()
        self._singletons: dict[str, Any] = {}
        self._factories: dict[str, callable] = {}

        # Registra settings come singleton
        self._register_singleton("settings", self.settings)

    def _register_singleton(self, name: str, instance: Any) -> None:
        """Registra un'istanza singleton."""
        self._singletons[name] = instance
        logger.debug(f"✓ Singleton registered: {name}")

    def _register_factory(self, name: str, factory: callable) -> None:
        """Registra una factory function."""
        self._factories[name] = factory
        logger.debug(f"✓ Factory registered: {name}")

    def get(self, name: str) -> Any:
        """
        Ottiene una dependency dal container.

        Precedenza:
        1. Singletons (istanze già create)
        2. Factories (lazy loading)
        3. Exception se non trovato
        """
        # Prova singleton prima
        if name in self._singletons:
            return self._singletons[name]

        # Prova factory (lazy load)
        if name in self._factories:
            instance = self._factories[name]()
            self._singletons[name] = instance  # Cache come singleton
            return instance

        raise ValueError(f"❌ Dependency '{name}' not registered in DIContainer")

    # ========== SERVICE & REPOSITORY GETTERS (Operativi) ==========

    def get_database(self):
        if "database" not in self._singletons:
            from src.infrastructure.persistence.db.connection import DatabaseConnection

            instance = DatabaseConnection()
            self._register_singleton("database", instance)
        return self._singletons["database"]

    def get_user_repository(self):
        from src.infrastructure.persistence.repositories.user_repository import (
            UserRepository,
        )

        return UserRepository(db=self.get_database())

    def get_asset_repository(self):
        from src.infrastructure.persistence.repositories.asset_repository import (
            AssetRepository,
        )

        return AssetRepository(db=self.get_database())

    def get_auth_service(self):
        from src.application.services.auth_service import AuthService

        return AuthService(user_repo=self.get_user_repository())

    # --- AGGIUNTA FONDAMENTALE PER LA WAR ROOM ---
    def get_asset_service(self):
        """Restituisce l'AssetService collegato al suo Repository reale."""
        from src.application.services.asset_service import AssetService

        # Iniettiamo l'AssetRepository nell'AssetService (UI -> SERVICE -> REPO)
        return AssetService(asset_repo=self.get_asset_repository())

    def get_analysis_service(self):
        from src.application.services.analysis_service import AnalysisService
        from src.infrastructure.persistence.repositories.kpi_repository import (
            KPIRepository,
        )

        # Iniettiamo il KPIRepository per i calcoli predittivi
        kpi_repo = KPIRepository(db=self.get_database())
        return AnalysisService(kpi_repo=kpi_repo)

    def get_ingestion_service(self):
        from src.application.services.ingestion_service import IngestionService

        return IngestionService()
