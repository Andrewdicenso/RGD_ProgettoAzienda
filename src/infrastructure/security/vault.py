"""
Secure Vault - Crittografia sicura con Fernet (AES).
"""

import json
import logging
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger("RGD-Alpha.Vault")


class SecureVault:
    """Vault per crittografia/decrittografia dati sensibili tramite Fernet."""

    def __init__(self, key_path: str = "src/infrastructure/security/vault.key"):
        """Inizializza Secure Vault."""
        self.key_path = Path(key_path)
        self._ensure_key_exists()

    def _ensure_key_exists(self) -> None:
        """Assicura che la chiave esista, altrimenti la crea."""
        if not self.key_path.exists():
            self.key_path.parent.mkdir(parents=True, exist_ok=True)
            key = Fernet.generate_key()
            self.key_path.write_bytes(key)
            logger.info("Vault key created: %s", self.key_path)

    def _get_fernet(self) -> Fernet:
        """Legge la chiave e restituisce un'istanza Fernet."""
        key = self.key_path.read_bytes()
        return Fernet(key)

    def encrypt(self, plaintext: str) -> str:
        """Cripta un testo in modo sicuro."""
        if not plaintext:
            return ""
        try:
            f = self._get_fernet()
            return f.encrypt(plaintext.encode("utf-8")).decode("utf-8")
        except Exception as e:
            logger.error("Encryption error: %s", e)
            raise

    def decrypt(self, ciphertext: str) -> str:
        """Decripta un testo in modo sicuro."""
        if not ciphertext:
            return ""
        try:
            f = self._get_fernet()
            return f.decrypt(ciphertext.encode("utf-8")).decode("utf-8")
        except (Exception, InvalidToken) as e:
            logger.error("Decryption error: %s", e)
            raise

    def encrypt_data(self, plaintext: str) -> str:
        """Alias per encrypt() richiesto dai repository."""
        return self.encrypt(plaintext)

    def decrypt_data(self, ciphertext: str) -> str:
        """Alias per decrypt() richiesto dai repository."""
        return self.decrypt(ciphertext)

    def encrypt_dict(self, data: dict) -> str:
        """Cripta un dizionario JSON."""
        json_str = json.dumps(data)
        return self.encrypt(json_str)

    def decrypt_dict(self, ciphertext: str) -> dict:
        """Decripta un dizionario JSON."""
        plaintext = self.decrypt(ciphertext)
        return json.loads(plaintext)
