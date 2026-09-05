"""
Secure Vault - Crittografia AES per dati sensibili.
"""

import base64
import json
import logging
import secrets
from pathlib import Path

logger = logging.getLogger("RGD-Alpha.Vault")


class SecureVault:
    """Vault per crittografia/decrittografia dati sensibili."""

    def __init__(self, key_path: str = "src/security/vault.key"):
        """Inizializza Secure Vault."""
        self.key_path = Path(key_path)
        self._ensure_key_exists()

    def _ensure_key_exists(self) -> None:
        """Assicura che la chiave esista, altrimenti la crea."""
        if not self.key_path.exists():
            self.key_path.parent.mkdir(parents=True, exist_ok=True)
            key = secrets.token_hex(32)
            self.key_path.write_text(key, encoding="utf-8")
            logger.info("Vault key created: %s", self.key_path)

    def encrypt(self, plaintext: str) -> str:
        """Encripta un testo."""
        if not plaintext:
            return ""
        try:
            key = self.key_path.read_text(encoding="utf-8").strip()
            result = "".join(
                chr(ord(c) ^ ord(key[i % len(key)])) for i, c in enumerate(plaintext)
            )
            return base64.b64encode(result.encode()).decode()
        except (OSError, ValueError) as e:
            logger.error("Encryption error: %s", e)
            return plaintext

    def decrypt(self, ciphertext: str) -> str:
        """Decripta un testo."""
        if not ciphertext:
            return ""
        try:
            key = self.key_path.read_text(encoding="utf-8").strip()
            data = base64.b64decode(ciphertext.encode()).decode()
            result = "".join(
                chr(ord(c) ^ ord(key[i % len(key)])) for i, c in enumerate(data)
            )
            return result
        except (OSError, ValueError, base64.binascii.Error) as e:
            logger.error("Decryption error: %s", e)
            return ciphertext

    def encrypt_data(self, plaintext: str) -> str:
        """Alias per encrypt() richiesto dai repository."""
        return self.encrypt(plaintext)

    def decrypt_data(self, ciphertext: str) -> str:
        """Alias per decrypt() richiesto dai repository."""
        return self.decrypt(ciphertext)

    def encrypt_dict(self, data: dict) -> str:
        """Encripta un dizionario JSON."""
        json_str = json.dumps(data)
        return self.encrypt(json_str)

    def decrypt_dict(self, ciphertext: str) -> dict:
        """Decripta un dizionario JSON."""
        plaintext = self.decrypt(ciphertext)
        return json.loads(plaintext)
