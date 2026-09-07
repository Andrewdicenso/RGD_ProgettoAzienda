"""
User Repository Enterprise - Unione tra Design Pattern e Persistenza Cloud Supabase.
"""

import src.domain
import src.infrastructure.persistence.db.connection

from ...security.vault import SecureVault
from .base_repository import BaseRepository


class UserRepository(BaseRepository[src.domain.Utente]):
    """
    Repository per Utente con persistenza su Supabase e cifratura dati sensibili.
    """

    def __init__(
        self, db: src.infrastructure.persistence.db.connection.DatabaseConnection
    ):
        """Inizializza il repository con il client Supabase e il Vault."""
        super().__init__("User")
        self.supabase = db.get_client()
        self.vault = SecureVault()

    def create(self, entity: src.domain.Utente) -> src.domain.Utente:
        """Crea e salva un utente su Supabase criptando i dati."""
        email_enc = self.vault.encrypt_data(entity.email)
        azienda_enc = (
            self.vault.encrypt_data(entity.azienda_id) if entity.azienda_id else None
        )

        data = {
            "id": entity.id,
            "email": email_enc,
            "password_hash": entity.password_hash,
            "ruolo": entity.ruolo,
            "azienda_id": azienda_enc,
        }

        self.supabase.table("utenti").insert(data).execute()
        self.log_info(f"User Enterprise creato su Cloud: {entity.email}")
        return entity

    def read(self, id: str) -> src.domain.Utente | None:  # pylint: disable=redefined-builtin
        """Legge un utente per ID dal Cloud e lo decripta."""
        response = self.supabase.table("utenti").select("*").eq("id", id).execute()
        if not response.data:
            return None

        row = response.data[0]
        row["email"] = self.vault.decrypt_data(row["email"])
        row["azienda_id"] = (
            self.vault.decrypt_data(row["azienda_id"]) if row["azienda_id"] else None
        )
        return src.domain.Utente(**row)

    def read_by_email(self, email: str) -> src.domain.Utente | None:
        """Legge un utente per email (Matching sicuro decriptato con debug)."""
        response = self.supabase.table("utenti").select("*").execute()
        for row in response.data:
            try:
                dec_email = self.vault.decrypt_data(row["email"])
                if dec_email.lower() == email.lower():
                    row["email"] = dec_email
                    row["azienda_id"] = (
                        self.vault.decrypt_data(row["azienda_id"])
                        if row["azienda_id"]
                        else None
                    )
                    return src.domain.Utente(**row)
            except Exception as e:
                print(f"DEBUG - Errore decifrazione utente ID {row.get('id')}: {e}")
                continue
        return None

    def get_by_email(self, email: str) -> src.domain.Utente | None:
        """Alias compatibile per AuthService."""
        return self.read_by_email(email)

    def update(self, entity: src.domain.Utente) -> src.domain.Utente:
        """Aggiorna un utente esistente su Supabase."""
        email_enc = self.vault.encrypt_data(entity.email)
        azienda_enc = (
            self.vault.encrypt_data(entity.azienda_id) if entity.azienda_id else None
        )

        data = {
            "email": email_enc,
            "password_hash": entity.password_hash,
            "ruolo": entity.ruolo,
            "azienda_id": azienda_enc,
        }

        self.supabase.table("utenti").update(data).eq("id", entity.id).execute()
        self.log_info(f"User Enterprise aggiornato: {entity.email}")
        return entity

    def delete(self, id: str) -> bool:  # pylint: disable=redefined-builtin
        """Cancella un utente dal Cloud."""
        response = self.supabase.table("utenti").delete().eq("id", id).execute()
        self.log_info(f"User Enterprise eliminato: {id}")
        return len(response.data) > 0

    def list_all(self) -> list[src.domain.Utente]:
        """Lista tutti gli utenti decriptati (per Admin Panel)."""
        response = self.supabase.table("utenti").select("*").execute()
        users = []
        for row in response.data:
            try:
                row["email"] = self.vault.decrypt_data(row["email"])
                row["azienda_id"] = (
                    self.vault.decrypt_data(row["azienda_id"])
                    if row["azienda_id"]
                    else None
                )
                users.append(src.domain.Utente(**row))
            except Exception as e:
                print(f"DEBUG - Errore decifrazione record in list_all: {e}")
                continue
        return users
