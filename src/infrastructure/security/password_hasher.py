"""
Password Hasher - Gestione password con bcrypt.
"""

import bcrypt


class PasswordHasher:
    """Wrapper per bcrypt hashing."""

    def __init__(self, rounds: int = 12):
        """
        Inizializza PasswordHasher.

        Args:
            rounds: Numero di rounds bcrypt (default 12)
        """
        self.rounds = rounds

    def hash_password(self, password: str) -> str:
        """
        Hashra una password.

        Args:
            password: Password in chiaro

        Returns:
            Password hashata
        """
        salt = bcrypt.gensalt(rounds=self.rounds)
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    def verify_password(self, password: str, password_hash: str) -> bool:
        """
        Verifica una password.

        Args:
            password: Password in chiaro
            password_hash: Hash della password

        Returns:
            True se corrispondente
        """
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
