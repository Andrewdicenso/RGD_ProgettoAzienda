"""
Main Entrypoint - Streamlit Application Dashboard.
"""

import sys
from pathlib import Path

# Force Python Path resolution FIRST
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st  # pylint: disable=wrong-import-position
from dotenv import load_dotenv  # pylint: disable=wrong-import-position

from src.config import get_settings  # pylint: disable=wrong-import-position
from src.config.di_container import DIContainer  # pylint: disable=wrong-import-position
from src.infrastructure import (
    configure_logging,  # pylint: disable=wrong-import-position
)
from src.presentation.components import (
    render_login_tabs,  # pylint: disable=wrong-import-position
)
from src.presentation.state import (
    SessionManager,  # pylint: disable=wrong-import-position
)

# ==============================================================================
# INIEZIONE ROOT (Deve essere eseguita TASSATIVAMENTE prima di qualsiasi 'from src...')
# ==============================================================================
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Ora è possibile importare qualsiasi modulo di terze parti e del progetto


# Force Python Path resolution FIRST
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# Caricamento ambiente
load_dotenv()


# Force Python Path resolution FIRST
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# Caricamento ambiente
load_dotenv()


# 1. INIEZIONE ROOT (Eseguita TASSATIVAMENTE prima degli import da src/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# 2. Caricamento ambiente
load_dotenv()

# 3. Import delle librerie di terze parti

# 4. Import dei moduli architetturali del progetto

# 5. Inizializzazione globale e Dependency Container
settings = get_settings()
configure_logging()
container = DIContainer()


# ==========================================
# SRC UI CONFIGURATION & STYLES
# ==========================================


def load_css() -> None:
    """Carica il foglio di stile risolvendo i percorsi reali del repository."""
    css_paths = [
        PROJECT_ROOT / "src" / "presentation" / "style.css",
        PROJECT_ROOT / "style.css",
    ]
    for css_path in css_paths:
        if css_path.exists():
            try:
                with open(css_path, "r", encoding="utf-8") as f:
                    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
                break
            except OSError as err:
                st.warning(f"⚠️ Errore nel caricamento CSS ({css_path.name}): {err}")


def configure_page() -> None:
    """Applica la configurazione globale della pagina Streamlit."""
    st.set_page_config(**settings.ST_PAGE_CONFIG)
    load_css()


# ==========================================
# ACTION HANDLERS (Business Logic via DI)
# ==========================================


def handle_login(email: str, password: str) -> bool:
    """Gestisce il login utente tramite AuthService iniettato dal DIContainer."""
    auth_service = container.get_auth_service()
    response = auth_service.login(email, password)

    if response.success:
        SessionManager.login(
            user_id=response.user_id,
            email=response.email,
            ruolo=response.ruolo,
            azienda=response.azienda,
            azienda_id=response.azienda_id,
        )
        st.success(f"✅ {response.message}")
        st.rerun()

    st.error(f"❌ {response.message}")
    return False


def handle_register(email: str, password: str, confirm: str) -> bool:
    """Gestisce la registrazione di un nuovo utente."""
    auth_service = container.get_auth_service()
    response = auth_service.register(email, password, confirm)

    if response.success:
        st.success(f"✅ {response.message}")
        return True

    st.error(f"❌ {response.message}")
    return False


def handle_request_reset(email: str) -> bool:
    """Gestisce l'invio della richiesta di recupero password."""
    auth_service = container.get_auth_service()
    success, _ = auth_service.request_password_reset(email)

    if success:
        st.success("✅ Se l'email è registrata, riceverai un link di reset")
        return True

    st.warning("⚠️ Se l'email è registrata, riceverai un link di reset")
    return False


def handle_reset_password(token: str, password: str, confirm: str) -> bool:
    """Gestisce il reset effettivo della password via token."""
    auth_service = container.get_auth_service()
    success, message = auth_service.reset_password(token, password, confirm)

    if success:
        st.success(f"✅ {message}")
        return True

    st.error(f"❌ {message}")
    return False


# ==========================================
# PRESENTATION LAYER & ROUTING
# ==========================================


def render_auth_pages() -> None:
    """Renderizza l'interfaccia pubblica per l'autenticazione."""
    st.markdown(
        """
        <style>
            [data-testid="stSidebar"], [data-testid="stSidebarCollapseButton"] {
                display: none !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("🛡️ RGD-Alpha | War Room Strategica")
    st.subheader("Gestione Strategica d'Azienda")

    col1, col2 = st.columns([1.2, 1], gap="large")

    with col1:
        st.markdown("""
        ### Benvenuto in RGD-Alpha

        La piattaforma di **Business Intelligence e Risk Management**
        progettata per PMI italiane.

        **Funzionalità Principali:**
        - 📊 Analisi Predittiva del Rischio
        - 🎯 Dashboard Strategica (War Room)
        - ⚡ Alerting Automatico
        - 📈 Simulazioni What-If

        ---
        """)

    with col2:
        st.markdown("### 🔐 Accedi al Sistema")
        reset_token = st.query_params.get("reset_token")

        render_login_tabs(
            on_login=handle_login,
            on_register=handle_register,
            on_request_reset=handle_request_reset,
            reset_token=reset_token,
            on_reset=handle_reset_password,
        )


def render_app_pages() -> None:
    """Router delle viste protette con menu di navigazione laterale."""
    with st.sidebar:
        st.markdown(f"### 👤 {SessionManager.get_email()}")
        st.caption(f"Ruolo: **{str(SessionManager.get_ruolo()).upper()}**")
        st.caption(f"Azienda: **{SessionManager.get_azienda()}**")

        st.divider()

        menu = st.radio(
            "Navigazione:",
            ["🏠 Home", "📊 War Room", "📁 Archivio Dati"],
            index=0,
        )

        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            SessionManager.logout()
            st.rerun()

    if menu == "🏠 Home":
        try:
            import importlib  # pylint: disable=import-outside-toplevel

            home_module = importlib.import_module("src.presentation.pages.0_home")
            home_module.show()
        except (ImportError, AttributeError):
            st.title("🏠 Homepage RGD-Alpha")
            st.info(
                f"✨ **Benvenuto nella Dashboard, {SessionManager.get_azienda()}!**"
            )

    elif menu == "📊 War Room":
        try:
            from src.presentation.pages.war_room import (
                show,  # pylint: disable=import-outside-toplevel
            )

            show()
        except ImportError as err:
            st.error(f"Errore nel caricamento della War Room: {err}")

    elif menu == "📁 Archivio Dati":
        st.title("📁 Archivio Dati Operativi")
        st.write(
            "Qui verranno elencati i file elaborati dal sistema e prelevati dai gestionali."
        )
        st.info("Nessun file presente nell'archivio al momento.")


# ==========================================
# APPLICATION ENTRY POINT
# ==========================================


def main() -> None:
    """Ciclo di vita principale dell'applicazione."""
    configure_page()
    SessionManager.initialize()

    if SessionManager.is_autenticato():
        render_app_pages()
    else:
        render_auth_pages()


if __name__ == "__main__":
    main()
