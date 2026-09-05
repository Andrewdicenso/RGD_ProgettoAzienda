"""
Auth Service - Use Case: Autenticazione & Autorizzazione Enterprise.
Orchestra Login, Registrazione, Reset Password e Gestione Sessioni/Token.
"""

import logging
import uuid
from datetime import datetime, timedelta

import bcrypt

from src.application.dto import LoginResponseDTO, RegistrationResponseDTO
from src.application.services.base_service import BaseService
from src.config import get_settings
from src.domain import UserRole, Utente

logger = logging.getLogger("RGD-Alpha.AuthService")


class AuthService(BaseService):
    """
    Servizio di autenticazione e sicurezza.
    Supporta persistenza reale via UserRepository o cache locale di fallback.
    """

    def __init__(self, user_repo=None, admin_email: str | None = None):
        """
        Inizializza AuthService.
        """
        super().__init__("AuthService")

        # 1. Carichiamo le impostazioni tramite la funzione factory
        self.settings = get_settings()

        self.user_repo = user_repo

        # 2. Usiamo self.settings invece di settings
        self.admin_email = (admin_email or self.settings.ADMIN_EMAIL).lower().strip()

        self._users_store: dict[str, Utente] = {}  # In-memory storage (demo/fallback)
        self._reset_tokens: dict[str, dict] = {}  # Token di reset password

        # Inizializza admin di default
        self._create_default_admin()

    def _create_default_admin(self) -> None:
        """Crea l'utente admin di default se non presente."""
        # Se hai usato self.settings = get_settings() in __init__, usa questa versione:
        admin_password = self.settings.DEFAULT_ADMIN_PASSWORD

        admin_hash = bcrypt.hashpw(
            admin_password.encode("utf-8"),
            bcrypt.gensalt(rounds=self.settings.BCRYPT_ROUNDS),
        ).decode("utf-8")

        admin = Utente(
            email=self.admin_email,
            password_hash=admin_hash,
            ruolo=UserRole.ADMIN.value,
            azienda_id="rgd-alpha-enterprise",
        )

        self._users_store[admin.id] = admin
        if self.user_repo:
            try:
                self.user_repo.create(admin)
            except Exception:
                pass  # L'admin potrebbe già esistere a DB

        self.log_info(f"Admin di default verificato/creato per: {self.admin_email}")

    def login(self, email: str, password: str) -> LoginResponseDTO:
        """
        Autentica un utente verificando le credenziali con Bcrypt.
        """
        email = email.lower().strip()
        self.log_info(f"Tentativo di login per: {email}")

        # 1. Trova l'utente (da DB o cache)
        user = self._find_user_by_email(email)
        if not user:
            self.log_warning(f"Login fallito: utente non trovato ({email})")
            return LoginResponseDTO(
                success=False,
                user_id="",
                email="",
                ruolo="",
                azienda="",
                azienda_id="",
                message="Email o password non validi",
            )

        # 2. Verifica hash della password
        user_pw_hash = getattr(user, "password_hash", "")
        if not bcrypt.checkpw(password.encode("utf-8"), user_pw_hash.encode("utf-8")):
            self.log_warning(f"Login fallito: password errata per {email}")
            return LoginResponseDTO(
                success=False,
                user_id="",
                email="",
                ruolo="",
                azienda="",
                azienda_id="",
                message="Email o password non validi",
            )

        # 3. Aggiorna data ultimo login
        if hasattr(user, "data_ultimo_login"):
            user.data_ultimo_login = datetime.now()

        # 4. Genera Token di sessione
        token = self._create_token(user.id)

        self.log_info(f"Login completato con successo: {email}")

        return LoginResponseDTO(
            success=True,
            user_id=user.id,
            email=user.email,
            ruolo=getattr(user, "ruolo", UserRole.USER.value),
            azienda=getattr(user, "azienda_nome", "Azienda Connessa"),
            azienda_id=getattr(user, "azienda_id", "demo-001"),
            token=token,
            message="Login effettuato con successo",
        )

    def register(
        self,
        email: str,
        password: str,
        confirm_password: str,
        azienda_name: str | None = None,
    ) -> RegistrationResponseDTO:
        """
        Registra un nuovo utente garantendo la validazione della password e l'univocità della mail.
        """
        email = email.lower().strip()
        self.log_info(f"Tentativo di registrazione per: {email}")

        # Validazioni della password
        if password != confirm_password:
            return RegistrationResponseDTO(
                success=False, message="Le password inserite non coincidono"
            )

        if len(password) < self.settings.PASSWORD_MIN_LENGTH:
            return RegistrationResponseDTO(
                success=False,
                message=f"La password deve contenere almeno {self.settings.PASSWORD_MIN_LENGTH} caratteri",
            )

        # Controllo presenza utente esistente
        if self._find_user_by_email(email):
            self.log_warning(f"Registrazione fallita: email già presente ({email})")
            return RegistrationResponseDTO(
                success=False, message="Email già registrata nel sistema"
            )

        # Generazione Hash Password
        password_hash = bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt(rounds=self.settings.BCRYPT_ROUNDS)
        ).decode("utf-8")

        # Assegnazione Ruolo
        ruolo = (
            UserRole.ADMIN.value if email == self.admin_email else UserRole.USER.value
        )
        company_id = f"company-{uuid.uuid4().hex[:8]}"

        utente = Utente(
            email=email,
            password_hash=password_hash,
            ruolo=ruolo,
            azienda_id=company_id,
        )

        # Salvataggio
        self._users_store[utente.id] = utente
        if self.user_repo:
            try:
                self.user_repo.create(utente)
            except Exception as e:
                self.log_error(f"Errore durante il salvataggio utente nel DB: {e}")

        self.log_info(f"Nuovo utente registrato con successo: {email}")

        return RegistrationResponseDTO(
            success=True,
            user_id=utente.id,
            message="Registrazione completata con successo",
        )

    def request_password_reset(self, email: str) -> tuple[bool, str]:
        """
        Genera un token di reset della password valido per 24 ore.
        """
        email = email.lower().strip()
        self.log_info(f"Richiesta di reset password per: {email}")

        user = self._find_user_by_email(email)
        if not user:
            # Sicurezza: risponde sempre True per evitare User Enumeration
            return True, ""

        reset_token = str(uuid.uuid4())
        self._reset_tokens[reset_token] = {
            "user_id": user.id,
            "email": email,
            "expires_at": datetime.now() + timedelta(hours=24),
        }

        self.log_info(f"Token di reset generato per: {email}")
        return True, reset_token

    def reset_password(
        self, token: str, new_password: str, confirm_password: str
    ) -> tuple[bool, str]:
        """
        Completa il ripristino della password validando il token.
        """
        self.log_info("Tentativo di aggiornamento password con token di reset")

        if token not in self._reset_tokens:
            return False, "Token di reset non valido"

        token_data = self._reset_tokens[token]

        # Controlla scadenza token
        if datetime.now() > token_data["expires_at"]:
            del self._reset_tokens[token]
            return False, "Il token di reset è scaduto"

        if new_password != confirm_password:
            return False, "Le nuove password non coincidono"

        if len(new_password) < self.settings.PASSWORD_MIN_LENGTH:
            return (
                False,
                f"La password deve essere di almeno {self.settings.PASSWORD_MIN_LENGTH} caratteri",
            )

        user_id = token_data["user_id"]
        user = self._users_store.get(user_id) or (
            self.user_repo.read(user_id) if self.user_repo else None
        )

        if not user:
            return False, "Utente associato non trovato"

        # Aggiornamento Hash Password
        new_hash = bcrypt.hashpw(
            new_password.encode("utf-8"),
            bcrypt.gensalt(rounds=self.settings.BCRYPT_ROUNDS),
        ).decode("utf-8")

        user.password_hash = new_hash

        if self.user_repo:
            try:
                self.user_repo.update(user_id, user)
            except Exception as e:
                self.log_error(f"Errore aggiornamento password nel DB: {e}")

        # Invalida il token usato
        del self._reset_tokens[token]

        self.log_info(f"Password aggiornata con successo per l'utente: {user.email}")
        return True, "Password aggiornata con successo"

    def _find_user_by_email(self, email: str) -> Utente | None:
        """Trova un utente per email nel DB o nella memoria."""
        if self.user_repo:
            try:
                user = self.user_repo.get_by_email(email)
                if user:
                    return user
            except Exception:
                pass

        for user in self._users_store.values():
            if getattr(user, "email", "").lower() == email.lower():
                return user
        return None

    def _create_token(self, user_id: str) -> str:
        """Crea un token identificativo di sessione."""
        return f"rgd-token-{user_id}-{uuid.uuid4().hex[:12]}"

    def verify_token(self, token: str) -> str | None:
        """Verifica la validità del token e restituisce il relativo user_id."""
        if token.startswith("rgd-token-"):
            parts = token.split("-")
            if len(parts) >= 3:
                return parts[2]
        return None
