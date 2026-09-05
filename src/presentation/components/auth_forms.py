"""
Auth Components - Componenti UI per autenticazione.
"""

from collections.abc import Callable

import streamlit as st

from ...config import get_settings

settings = get_settings()


def render_login_form(on_login: Callable[[str, str], bool]) -> None:
    """
    Renderizza il form di login.

    Args:
        on_login: Callback che riceve (email, password) e ritorna True se login ok
    """
    with st.form("login_form", clear_on_submit=True):
        email = st.text_input("📧 Email Aziendale", placeholder="tu@azienda.it")
        password = st.text_input("🔐 Password", type="password")

        col1, col2 = st.columns(2)
        with col1:
            submit = st.form_submit_button("🔓 Accedi", use_container_width=True)
        with col2:
            st.form_submit_button("Annulla", use_container_width=True)

        if submit:
            if not email or not password:
                st.error("⚠️ Compila email e password")
                return

            if on_login(email, password):
                st.success("✅ Accesso eseguito!")
                st.rerun()
            else:
                st.error("❌ Credenziali non valide")


def render_registration_form(on_register: Callable[[str, str, str], bool]) -> None:
    """
    Renderizza il form di registrazione.

    Args:
        on_register: Callback che riceve (email, password, confirm_password) e ritorna True se ok
    """
    with st.form("registration_form", clear_on_submit=True):
        email = st.text_input("📧 Email", placeholder="tu@azienda.it", key="reg_email")
        password = st.text_input(
            "🔐 Password", type="password", key="reg_pwd", help="Min 8 caratteri"
        )
        confirm = st.text_input("🔐 Conferma Password", type="password", key="reg_conf")

        st.info("ℹ️ Riceverai una mail di conferma con il link di attivazione")

        col1, col2 = st.columns(2)
        with col1:
            submit = st.form_submit_button("📝 Registrati", use_container_width=True)
        with col2:
            st.form_submit_button("Annulla", use_container_width=True)

        if submit:
            if not email or not password or not confirm:
                st.error("⚠️ Compila tutti i campi")
                return

            if password != confirm:
                st.error("❌ Le password non coincidono")
                return

            if len(password) < settings.PASSWORD_MIN_LENGTH:
                st.error(
                    f"❌ Password deve essere almeno {settings.PASSWORD_MIN_LENGTH} caratteri"
                )
                return

            if on_register(email, password, confirm):
                st.success(
                    "✅ Registrazione completata! Controlla la mail per l'attivazione."
                )
                st.balloons()
            else:
                st.error("❌ Errore nella registrazione")


def render_password_recovery_form(
    on_request_reset: Callable[[str], bool],
    reset_token: str | None = None,
    on_reset: Callable[[str, str, str], bool] | None = None,
) -> None:
    """
    Renderizza il form di recupero password.

    Args:
        on_request_reset: Callback per richiedere reset (riceve email)
        reset_token: Token da URL se in fase reset
        on_reset: Callback per completare reset (riceve token, password, confirm)
    """
    if not reset_token:
        st.subheader("🔄 Recupero Password")
        st.info("Inserisci la tua email per ricevere il link di recupero")

        with st.form("password_recovery_form"):
            email = st.text_input("📧 Email Registrata", placeholder="tu@azienda.it")
            submit = st.form_submit_button(
                "📧 Invia Link di Recupero", use_container_width=True
            )

            if submit:
                if not email:
                    st.error("⚠️ Inserisci la tua email")
                    return

                if on_request_reset(email):
                    st.success("✅ Link inviato alla tua email!")
                    st.info("Clicca il link nella mail per resettar la password")
                else:
                    st.error("❌ Email non trovata nel sistema")
    else:
        st.subheader("🔑 Reset Password")
        st.warning("⚠️ Link di reset attivo")

        with st.form("password_reset_form"):
            new_password = st.text_input("🔐 Nuova Password", type="password")
            confirm_password = st.text_input("🔐 Conferma Password", type="password")
            submit = st.form_submit_button(
                "✅ Conferma Reset", use_container_width=True
            )

            if submit:
                if not new_password or not confirm_password:
                    st.error("⚠️ Compila entrambi i campi")
                    return

                if new_password != confirm_password:
                    st.error("❌ Le password non coincidono")
                    return

                if len(new_password) < settings.PASSWORD_MIN_LENGTH:
                    st.error(
                        f"❌ Password deve essere almeno {settings.PASSWORD_MIN_LENGTH} caratteri"
                    )
                    return

                if on_reset(reset_token, new_password, confirm_password):
                    st.success("✅ Password aggiornata! Effettua il login")
                    st.rerun()
                else:
                    st.error("❌ Errore nel reset della password")


def render_login_tabs(
    on_login: Callable[[str, str], bool],
    on_register: Callable[[str, str, str], bool],
    on_request_reset: Callable[[str], bool],
    reset_token: str | None = None,
    on_reset: Callable[[str, str, str], bool] | None = None,
) -> None:
    """
    Renderizza i tre tab di autenticazione in un'unica funzione.

    Args:
        on_login: Callback login
        on_register: Callback registrazione
        on_request_reset: Callback richiesta reset
        reset_token: Token reset da URL
        on_reset: Callback reset password
    """
    tab1, tab2, tab3 = st.tabs(["🔐 Login", "🆕 Registrazione", "🔄 Recupero Password"])

    with tab1:
        render_login_form(on_login)

    with tab2:
        render_registration_form(on_register)

    with tab3:
        render_password_recovery_form(on_request_reset, reset_token, on_reset)
