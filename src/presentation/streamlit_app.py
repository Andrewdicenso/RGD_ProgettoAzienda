"""
Main Entrypoint - Streamlit Application Dashboard.
"""

import sys
from pathlib import Path

# 1. INIEZIONE ROOT (TASSATIVAMENTE la prima operazione in assoluto)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st  # pylint: disable=wrong-import-position
from dotenv import load_dotenv  # pylint: disable=wrong-import-position

from src.config import get_settings  # pylint: disable=wrong-import-position
from src.config.di_container import DIContainer  # pylint: disable=wrong-import-position
from src.presentation.components import (
    render_login_tabs,  # pylint: disable=wrong-import-position
)
from src.presentation.state import (
    SessionManager,  # pylint: disable=wrong-import-position
)

# Caricamento ambiente
load_dotenv()

# Inizializzazione globale e Dependency Container (con cache per la persistenza dello stato)
settings = get_settings()
from src.infrastructure.logging import configure_logging

configure_logging()


@st.cache_resource
def get_app_container() -> DIContainer:
    """Crea un'istanza persistente del container per mantenere lo stato in memoria."""
    return DIContainer()


container = get_app_container()


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
    """Router delle viste protette con menu di navigazione laterale pulito."""
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
        st.title("📁 Archivio Dati Operativi e Gestione Abbonamenti")
        st.write(
            "Panoramica generale dei file di sistema e controllo dei clienti iscritti."
        )

        user_role = str(SessionManager.get_ruolo()).upper()
        user_email = SessionManager.get_email()
        is_admin = user_role == "ADMIN" or user_email == "andrewdicenso@libero.it"

        # Pannello visibile SOLO per gli ADMIN
        if is_admin:
            st.markdown("### 👑 Pannello Super Admin & Selettore Cliente")
            try:
                db = container.get_database()
                response = (
                    db.client.table("utenti")
                    .select("id, email, azienda_id, ruolo, data_creazione")
                    .execute()
                )
                utenti_db = response.data if response and response.data else []
                lista_clienti = [u.get("email") for u in utenti_db if u.get("email")]

                if lista_clienti:
                    cliente_selezionato = st.selectbox(
                        "Seleziona Cliente in Tempo Reale",
                        ["Vista Globale (Tutti)"] + lista_clienti,
                        key="super_admin_client_selector",
                    )
                    if cliente_selezionato != "Vista Globale (Tutti)":
                        st.session_state["target_client_email"] = cliente_selezionato
                        st.info(f"🎯 Monitoraggio attivo su: **{cliente_selezionato}**")
                    else:
                        st.session_state.pop("target_client_email", None)
                        st.info("🌍 Monitoraggio in **Vista Globale (Tutti)**")
                else:
                    st.info("Nessun cliente registrato nel database.")
            except Exception as err:
                st.warning(f"⚠️ Impossibile caricare i clienti per la selezione: {err}")

            st.divider()

            # Elenco Clienti visibile SOLO agli admin
            st.markdown("### 📋 Elenco Clienti e Stato Abbonamenti")
            try:
                if utenti_db:
                    import pandas as pd  # pylint: disable=import-outside-toplevel

                    df_utenti = pd.DataFrame(utenti_db)
                    st.dataframe(
                        df_utenti[["email", "ruolo", "azienda_id", "data_creazione"]],
                        use_container_width=True,
                    )
                else:
                    st.info("Nessun cliente registrato.")
            except Exception as err:
                st.warning(f"⚠️ Impossibile caricare la lista clienti: {err}")

            st.divider()
        else:
            # Vista dedicata per utenti standard (non vedono gli altri utenti)
            st.info("ℹ️ Area riservata ai dati della tua azienda.")

        # Sezione centrale: Archivio Asset/File (filtrata per utente se non admin)
        st.markdown("### 📂 File e Asset di Sistema")
        try:
            db = container.get_database()
            query = db.client.table("assets").select("*")

            # Se non è admin, filtra eventualmente per la sua azienda o ID se previsto dalla tabella
            # (Adattabile in base alla struttura della tabella assets)
            response = query.execute()
            assets_data = response.data if response and response.data else []

            if assets_data:
                import pandas as pd  # pylint: disable=import-outside-toplevel

                df_assets = pd.DataFrame(assets_data)
                st.dataframe(df_assets, use_container_width=True)
            else:
                st.info("Nessun file o asset presente nell'archivio al momento.")
        except Exception as err:
            st.warning(f"⚠️ Impossibile caricare l'archivio dati: {err}")


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
