"""
DI Container - Dependency Injection Container per RGD-Alpha.
Gestisce l'istanziazione delle dependencies in modo centralizzato.
"""

import importlib
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
        kpi_service = container.get_kpi_service()
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

    # ============================================================
    # REGISTRAZIONE SINGLETON / FACTORY
    # ============================================================
    def _register_singleton(self, name: str, instance: Any) -> None:
        self._singletons[name] = instance
        logger.debug(f"✓ Singleton registered: {name}")

    def _register_factory(self, name: str, factory: callable) -> None:
        self._factories[name] = factory
        logger.debug(f"✓ Factory registered: {name}")

    def get(self, name: str) -> Any:
        """
        Ottiene una dependency dal container.

        Precedenza:
        1. Singletons
        2. Factories
        3. Exception se non trovato
        """
        if name in self._singletons:
            return self._singletons[name]

        if name in self._factories:
            instance = self._factories[name]()
            self._singletons[name] = instance
            return instance

        raise ValueError(f"❌ Dependency '{name}' not registered in DIContainer")

    # ============================================================
    # DATABASE & REPOSITORIES
    # ============================================================
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

    # ============================================================
    # 🔥 AI PROVIDER (Groq Ultra + Gemini Free + Offline)
    # ============================================================
    def get_ai_provider(self):
        if "ai_provider" not in self._singletons:
            AIProvider = None

            for module_name in (
                "src.ai_modules.modelli.factory",
                "src.ai_modules.modelli.providers",
                "src.ai_modules.modelli.provider_groq",
                "src.ai_modules.modelli.provider_gemini",
                "src.ai_modules.modelli.base_model",
                "src.infrastructure.external.providers",
                "src.infrastructure.external.ai_provider",
            ):
                try:
                    module = importlib.import_module(module_name)
                    if hasattr(module, "AIProvider"):
                        AIProvider = module.AIProvider
                        break
                except (ImportError, AttributeError):
                    continue

            if AIProvider is None:
                raise ImportError(
                    "Unable to import AIProvider from any known module path."
                )

            instance = AIProvider()
            self._register_singleton("ai_provider", instance)

        return self._singletons["ai_provider"]

    # ============================================================
    # SERVICES
    # ============================================================
    def get_auth_service(self):
        from src.application.services.auth_service import AuthService

        return AuthService(user_repo=self.get_user_repository())

    def get_asset_service(self):
        from src.application.services.asset_service import AssetService

        return AssetService(
            asset_repo=self.get_asset_repository(),
            ai_provider=self.get_ai_provider(),
        )

    def get_analysis_service(self):
        from src.application.services.analysis_service import AnalysisService
        from src.infrastructure.persistence.repositories.kpi_repository import (
            KPIRepository,
        )

        kpi_repo = KPIRepository(db=self.get_database())
        asset_repo = self.get_asset_repository()
        ai_provider = self.get_ai_provider()

        return AnalysisService(
            kpi_repo=kpi_repo,
            asset_repo=asset_repo,
            ai_provider=ai_provider,
        )

    def get_ingestion_service(self):
        from src.application.services.ingestion_service import IngestionService

        return IngestionService(asset_repo=self.get_asset_repository())

    # ============================================================
    # ⭐ KPI SERVICE (AGGIUNTO COME RICHIESTO)
    # ============================================================
    def get_kpi_service(self):
        from src.application.services.kpi_service import KPIService
        from src.infrastructure.persistence.repositories.kpi_repository import (
            KPIRepository,
        )

        return KPIService(kpi_repo=KPIRepository(db=self.get_database()))
