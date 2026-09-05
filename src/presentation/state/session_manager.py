"""
Session Manager - Wrapper per st.session_state.
Centralizza la gestione dello stato dell'applicazione.
"""

from typing import Any

import streamlit as st


class SessionManager:
    """
    Gestisce lo stato della sessione in modo centralizzato.

    Uso:
        session = SessionManager()
        session.set_autenticato(True)
        if session.is_autenticato:
            ...
    """

    # ========== CHIAVI SESSIONE ==========
    KEY_AUTENTICATO = "autenticato"
    KEY_USER_ID = "user_id"
    KEY_EMAIL = "email"
    KEY_RUOLO = "ruolo"
    KEY_AZIENDA = "azienda"
    KEY_AZIENDA_ID = "azienda_id"

    @staticmethod
    def _init_key(key: str, default_value: Any) -> None:
        """Inizializza una chiave di sessione se non esiste."""
        if key not in st.session_state:
            st.session_state[key] = default_value

    @classmethod
    def initialize(cls) -> None:
        """Inizializza tutte le chiavi di sessione."""
        cls._init_key(cls.KEY_AUTENTICATO, False)
        cls._init_key(cls.KEY_USER_ID, None)
        cls._init_key(cls.KEY_EMAIL, None)
        cls._init_key(cls.KEY_RUOLO, "user")
        cls._init_key(cls.KEY_AZIENDA, "Sconosciuta")
        cls._init_key(cls.KEY_AZIENDA_ID, None)

    # ========== GETTERS ==========

    @staticmethod
    def is_autenticato() -> bool:
        """Vero se l'utente è autenticato."""
        return st.session_state.get(SessionManager.KEY_AUTENTICATO, False)

    @staticmethod
    def get_user_id() -> str | None:
        """Ottiene l'ID dell'utente autenticato."""
        return st.session_state.get(SessionManager.KEY_USER_ID)

    @staticmethod
    def get_email() -> str | None:
        """Ottiene l'email dell'utente autenticato."""
        return st.session_state.get(SessionManager.KEY_EMAIL)

    @staticmethod
    def get_ruolo() -> str:
        """Ottiene il ruolo dell'utente."""
        return st.session_state.get(SessionManager.KEY_RUOLO, "user")

    @staticmethod
    def get_azienda() -> str:
        """Ottiene il nome dell'azienda."""
        return st.session_state.get(SessionManager.KEY_AZIENDA, "Sconosciuta")

    @staticmethod
    def get_azienda_id() -> str | None:
        """Ottiene l'ID dell'azienda."""
        return st.session_state.get(SessionManager.KEY_AZIENDA_ID)

    @staticmethod
    def is_admin() -> bool:
        """Vero se l'utente è amministratore."""
        return SessionManager.get_ruolo() == "admin"

    # ========== SETTERS ==========

    @staticmethod
    def login(
        user_id: str,
        email: str,
        ruolo: str,
        azienda: str = "Sconosciuta",
        azienda_id: str | None = None,
    ) -> None:
        """
        Imposta lo stato di login dell'utente.

        Args:
            user_id: ID univoco dell'utente
            email: Email dell'utente
            ruolo: Ruolo (admin, manager, user)
            azienda: Nome azienda
            azienda_id: ID azienda
        """
        st.session_state[SessionManager.KEY_AUTENTICATO] = True
        st.session_state[SessionManager.KEY_USER_ID] = user_id
        st.session_state[SessionManager.KEY_EMAIL] = email
        st.session_state[SessionManager.KEY_RUOLO] = ruolo
        st.session_state[SessionManager.KEY_AZIENDA] = azienda
        st.session_state[SessionManager.KEY_AZIENDA_ID] = azienda_id
        st.rerun()

    @staticmethod
    def logout() -> None:
        """Effettua il logout pulendo la sessione."""
        st.session_state[SessionManager.KEY_AUTENTICATO] = False
        st.session_state[SessionManager.KEY_USER_ID] = None
        st.session_state[SessionManager.KEY_EMAIL] = None
        st.session_state[SessionManager.KEY_RUOLO] = "user"
        st.session_state[SessionManager.KEY_AZIENDA] = "Sconosciuta"
        st.session_state[SessionManager.KEY_AZIENDA_ID] = None
        st.rerun()

    @staticmethod
    def require_auth(redirect_to_login: bool = True) -> bool:
        """
        Richiede autenticazione.

        Args:
            redirect_to_login: Se True, mostra errore e ferma l'esecuzione

        Returns:
            True se autenticato, False altrimenti
        """
        if not SessionManager.is_autenticato():
            if redirect_to_login:
                st.error("🔐 Accesso negato. Effettua il login per continuare.")
                st.stop()
            return False
        return True

    @staticmethod
    def require_admin() -> bool:
        """
        Richiede ruolo amministratore.

        Returns:
            True se admin, altrimenti mostra errore e ferma esecuzione
        """
        if not SessionManager.is_admin():
            st.error("🔒 Area riservata agli amministratori.")
            st.stop()
        return True
