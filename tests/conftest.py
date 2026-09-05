"""
Conftest.py - Configurazione pytest e fixtures comuni.
"""

import sys
from pathlib import Path

import pytest

# Risolvi percorsi
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import Settings, get_settings
from src.domain import Asset, AssetCategory, Azienda, RiscoScore, Utente


@pytest.fixture
def settings() -> Settings:
    """Fixture per Settings."""
    return get_settings()


@pytest.fixture
def sample_asset() -> Asset:
    """Fixture per un Asset di esempio."""
    return Asset(
        nome="Test Asset",
        company_id="test-company-001",
        rischio=RiscoScore(5.0),
        categoria=AssetCategory.GENERAL,
    )


@pytest.fixture
def sample_azienda() -> Azienda:
    """Fixture per un'Azienda di esempio."""
    return Azienda(
        nome="Test Company Ltd",
        partita_iva="12345678901",
        settore="Tecnologia",
        owner_email="test@example.com",
    )


@pytest.fixture
def sample_utente() -> Utente:
    """Fixture per un Utente di esempio."""
    return Utente(
        email="test@example.com",
        password_hash="$2b$12$hashed_password_example",
        ruolo="user",
    )


@pytest.fixture
def temp_project_root(tmp_path) -> Path:
    """Fixture che ritorna una directory temporanea."""
    return tmp_path
