"""
DTOs (Data Transfer Objects) - Application Layer Enterprise RGD-Alpha.
Definisce le strutture dati usate per trasferire dati tra la UI (Streamlit),
i servizi applicativi e i layer esterni (non contengono logica di business).
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field

# ==========================================
# 1. ASSET DTOs
# ==========================================


class AssetDTO(BaseModel):
    """DTO base per Asset - Usato per API e UI rendering."""

    id: str
    nome: str
    categoria: str
    rischio_value: float = Field(default=0.0, ge=0.0, le=10.0)
    rischio_level: str = "SAFE"  # CRITICAL, WARNING, SAFE
    momentum_status: str = "STABLE"
    momentum_value: float = 0.0
    volatilita_value: float = 0.0
    company_id: str
    data_creazione: str = Field(default_factory=lambda: datetime.now().isoformat())
    data_aggiornamento: str = Field(default_factory=lambda: datetime.now().isoformat())
    is_critical: bool = False
    dati_extra: dict[str, Any] = Field(default_factory=dict)


class AssetDiMercatoDTO(AssetDTO):
    """DTO per Asset di Logistica e Mercato."""

    quantita: float = 0.0
    sku: str = ""
    ubicazione: str = ""


class AssetDiValoreDTO(AssetDTO):
    """DTO per Asset di Finanza e Valore."""

    prezzo: float = 0.0
    stato_pagamento: str = ""
    valuta: str = "EUR"


# ==========================================
# 2. RISK ANALYSIS & KPI DTOs
# ==========================================


class RiskAnalysisDTO(BaseModel):
    """DTO per il risultato dell'analisi di rischio e proiezioni."""

    asset_id: str
    asset_nome: str
    rischio_attuale: float
    rischio_proiezione_30gg: float
    rischio_proiezione_60gg: float
    rischio_proiezione_90gg: float
    trend: str = "STABLE"  # ACCELERATING, DECELERATING, STABLE
    trend_value: float = 0.0
    volatilita: float = 0.0
    consiglio_strategico: str = ""
    urgenza: str = "LOW"  # IMMEDIATE, HIGH, MEDIUM, LOW
    confidenza: float = 0.95  # Confidence score (0-1)
    ai_provider: str = "Google Gemini"


class KPIReportDTO(BaseModel):
    """DTO per report sintetico KPI aziendali."""

    periodo: str  # es. "2026-08"
    health_score: float  # 0-10
    asset_critici_count: int = 0
    asset_warning_count: int = 0
    cash_flow_previsto: float = 0.0
    revenue_previsto: float = 0.0
    margin_percentage: float = 0.0
    trend_overall: str = "STABLE"
    summary: str = ""


# ==========================================
# 3. AUTHENTICATION & USER DTOs
# ==========================================


class LoginRequestDTO(BaseModel):
    """DTO per richiesta login."""

    email: EmailStr
    password: str


class LoginResponseDTO(BaseModel):
    """DTO per risposta login."""

    success: bool
    user_id: str = ""
    email: str = ""
    ruolo: str = "USER"
    azienda: str = ""
    azienda_id: str = ""
    token: str | None = None
    message: str = ""


class UserDTO(BaseModel):
    """DTO per rappresentazione Utente."""

    id: str
    email: EmailStr
    ruolo: str = "USER"
    azienda_id: str | None = None
    data_creazione: str = Field(default_factory=lambda: datetime.now().isoformat())
    data_ultimo_login: str | None = None


class RegistrationRequestDTO(BaseModel):
    """DTO per richiesta registrazione nuovo tenant/utente."""

    email: EmailStr
    password: str
    confirm_password: str
    azienda_name: str | None = None


class RegistrationResponseDTO(BaseModel):
    """DTO per risposta registrazione."""

    success: bool
    user_id: str | None = None
    message: str = ""


class PasswordResetRequestDTO(BaseModel):
    """DTO per richiesta reset password."""

    email: EmailStr


class PasswordResetDTO(BaseModel):
    """DTO per completamento reset password con token."""

    token: str
    new_password: str
    confirm_password: str


# ==========================================
# 4. INGESTION & DATA IMPORT DTOs
# ==========================================


class FileIngestionRequestDTO(BaseModel):
    """DTO per richiesta carimento file (CSV, Excel, ERP)."""

    file_name: str
    file_content: bytes
    file_type: str  # csv, xlsx, txt, etc.
    user_id: str
    company_id: str


class FileIngestionResponseDTO(BaseModel):
    """DTO per risposta esito carimento dati."""

    success: bool
    ingestion_id: str
    rows_processed: int = 0
    rows_valid: int = 0
    rows_rejected: int = 0
    assets_created: int = 0
    assets_updated: int = 0
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


# ==========================================
# 5. ALERT & DASHBOARD DTOs
# ==========================================


class AlertDTO(BaseModel):
    """DTO per Notifiche ed Alert di sistema."""

    id: str
    severity: str = "INFO"  # CRITICAL, WARNING, INFO
    title: str
    message: str
    asset_id: str | None = None
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    read: bool = False


class DashboardDTO(BaseModel):
    """DTO per Dashboard Summary principale della War Room."""

    health_score: float = 10.0
    asset_critici: int = 0
    asset_warning: int = 0
    asset_total: int = 0
    alerts: list[AlertDTO] = Field(default_factory=list)
    top_risks: list[RiskAnalysisDTO] = Field(default_factory=list)
    recent_uploads: list[str] = Field(default_factory=list)
    last_sync: str = Field(default_factory=lambda: datetime.now().isoformat())
