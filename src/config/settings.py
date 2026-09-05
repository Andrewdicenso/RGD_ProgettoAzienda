"""
Settings.py - Configurazione Centralizzata Enterprise RGD-Alpha.
Utilizza Pydantic Settings per validazione automatica, gestione sicura
delle variabili d'ambiente (.env) e garanzia del tipo a runtime.
"""

from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import EmailStr, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Configurazione Centralizzata - RGD-Alpha Enterprise.
    Legge dal file .env e valida automaticamente tutti i parametri all'avvio.
    """

    # ========== PROJECT PATHS ==========
    PROJECT_ROOT: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parent.parent.parent
    )

    @property
    def DATA_ROOT(self) -> Path:
        return self.PROJECT_ROOT / "data"

    @property
    def UPLOAD_DIR(self) -> Path:
        return self.DATA_ROOT / "uploads"

    @property
    def DB_DIR(self) -> Path:
        return self.DATA_ROOT / "db"

    @property
    def LOG_DIR(self) -> Path:
        return self.DATA_ROOT / "logs"

    # ========== APPLICATION ==========
    APP_NAME: str = "RGD-Alpha Enterprise"
    APP_VERSION: str = "1.0.0-ALPHA"
    APP_DESCRIPTION: str = "War Room Strategica Aziendale"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "RGD_ALPHA_SECURE_KEY_2026_XyZ987"

    # ========== DATABASE & SUPABASE ==========
    DATABASE_URL: str = "sqlite:///data/db/azienda.db"
    SUPABASE_URL: str = "https://byzyyjbfjmvmgkbitcs.supabase.co"
    SUPABASE_KEY: str | None = None
    DB_PASSWORD: str | None = None

    @property
    def DB_PATH(self) -> str:
        return str(self.DB_DIR / "azienda.db")

    # ========== SECURITY & AUTH ==========
    VAULT_KEY_PATH: str = "src/security/vault.key"
    JWT_SECRET: str = "dev-secret-change-in-production"
    ADMIN_EMAIL: EmailStr = "andrewdicenso@libero.it"
    DEFAULT_ADMIN_PASSWORD: str = "WarRoom123!"

    # ========== PASSWORD HASHING ==========
    BCRYPT_ROUNDS: int = 12
    PASSWORD_MIN_LENGTH: int = 8

    # ========== STREAMLIT CONFIG ==========
    ST_PAGE_CONFIG: dict[str, Any] = {
        "page_title": "RGD-Alpha | War Room Strategica",
        "layout": "wide",
        "page_icon": "🛡️",
        "initial_sidebar_state": "expanded",
    }

    # ========== RISK THRESHOLDS ==========
    RISK_THRESHOLD_CRITICAL: float = 7.5
    RISK_THRESHOLD_WARNING: float = 5.0
    RISK_THRESHOLD_SAFE: float = 3.0

    # ========== BUSINESS METRICS ==========
    SOGLIA_CAC: float = 50.0
    SOGLIA_LTV: float = 200.0
    SOGLIA_BURN_RATE: float = 10000.0
    SOGLIA_MARGINE: float = 20.0
    SOGLIA_CONVERSIONE: float = 2.0
    ORE_TEORICHE_ANNUE: int = 2080

    # ========== EMAIL CONFIG (SMTP) ==========
    SMTP_SERVER: str = "smtp.libero.it"
    SMTP_PORT: int = 465
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None

    # ========== GOOGLE WORKSPACE / GMAIL API ==========
    GMAIL_CLIENT_ID: str | None = None
    GMAIL_CLIENT_SECRET: str | None = None
    GMAIL_REFRESH_TOKEN: str | None = None

    # ========== AI PROVIDERS (GEMINI & GROQ) ==========
    GEMINI_API_KEY: str | None = None
    GROQ_API_KEY: str | None = None
    GROQ_MODEL: str = "mixtral-8x7b-32768"

    # ========== LOGGING ==========
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # ========== ASSET CATEGORIES (Domain Constants) ==========
    ASSET_CATEGORIES: dict[str, str] = {
        "FINANCE": "AssetDiValore",
        "LOGISTICS": "AssetDiMercato",
        "RELATIONS": "AssetDiRelazione",
        "GENERAL": "AssetStrategico",
    }

    # ========== ERP SYSTEM SIGNATURES ==========
    ERP_SIGNATURES: dict[str, str] = {
        "SAP": r"\|",
        "ORACLE": r"\-{5,}",
        "AS400": r"PAGINA\s+\d+|PAGE\s+\d+",
    }

    # ========== CONFIGURAZIONE PYDANTIC SETTINGS ==========
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignora eventuali variabili extra presenti nel file .env
        case_sensitive = True

    def ensure_directories(self) -> None:
        """Crea le directory di sistema se non esistono."""
        for dir_path in [self.DATA_ROOT, self.UPLOAD_DIR, self.DB_DIR, self.LOG_DIR]:
            dir_path.mkdir(parents=True, exist_ok=True)

    @property
    def has_ai_key(self) -> bool:
        """Verifica se e presente almeno una chiave AI (Gemini o Groq) per l'analisi."""
        return bool(self.GEMINI_API_KEY or self.GROQ_API_KEY)

    def to_dict(self) -> dict:
        """Converte le impostazioni in dizionario nascondendo le credenziali sensibili."""
        sensitive_words = ["SECRET", "PASSWORD", "TOKEN", "KEY"]
        data = self.model_dump()
        return {
            k: v
            for k, v in data.items()
            if not any(secret in k.upper() for secret in sensitive_words)
        }


# Singleton - Factory per settings con cache LRU
@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Factory function singleton per accedere alle configurazioni valide dell'app.
    Crea le directory necessarie al primo utilizzo.
    """
    settings_instance = Settings()
    settings_instance.ensure_directories()
    return settings_instance


# Export pronto per comodo import
settings = get_settings()
