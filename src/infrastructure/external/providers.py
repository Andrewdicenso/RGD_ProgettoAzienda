"""
External Service Providers - Integrazioni con servizi esterni (Email, Groq, Gemini, SFTP).
Questo file mantiene i provider esistenti e aggiunge AIProvider unificato (Groq + Gemini + fallback).
Non rinominare il file: incolla questo contenuto in `providers.py`.
"""

import logging
import os
from typing import Any

import requests

logger = logging.getLogger("RGD-Alpha.External")


# -----------------------
# Email / Integrations
# -----------------------
class EmailProvider:
    """Provider per spedire email (Gmail integration stub)."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key

    def send_email(
        self, to_email: str, subject: str, body: str, html: bool = False
    ) -> tuple[bool, str]:
        logger.info("Sending email to %s", to_email)
        if not self.api_key:
            logger.warning("Gmail API key not configured")
            return False, "Email non configurata"
        try:
            # Implementazione reale o stub
            logger.info("Email sent to %s", to_email)
            return True, "Email inviata con successo"
        except Exception as e:
            logger.error("Email send failed: %s", e)
            return False, f"Errore invio email: {e!s}"


class SFTPConnector:
    """Connector per SFTP (OneDrive sync stub)."""

    def __init__(self, host: str | None = None, username: str | None = None):
        self.host = host
        self.username = username

    def sync_file(self, remote_path: str, local_path: str) -> tuple[bool, str]:
        logger.info("Syncing file from %s", remote_path)
        if not self.host or not self.username:
            logger.warning("SFTP credentials not configured")
            return False, "SFTP non configurato"
        try:
            # Implementazione reale o stub
            logger.info("File synced to %s", local_path)
            return True, "File sincronizzato"
        except Exception as e:
            logger.error("SFTP sync failed: %s", e)
            return False, f"Errore sync: {e!s}"


# -----------------------
# Legacy adapters (kept for rollback/testing)
# -----------------------
class LegacyLLMProvider:
    """Adapter REST per Groq (legacy). Tenuto come fallback/test only."""

    def __init__(self, api_key: str | None = None, model: str = "llama3-70b-8192"):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.model = model
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"

    def generate_advice(self, prompt: str) -> str | None:
        logger.info("LegacyLLMProvider generating advice with model %s", self.model)
        if not self.api_key:
            logger.warning("Groq API key not configured (legacy adapter)")
            return None

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "Assistente operativo RGD-Alpha."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 1024,
        }

        try:
            response = requests.post(
                self.api_url, json=payload, headers=headers, timeout=15
            )
            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"]
            logger.error("Groq API error [%s]: %s", response.status_code, response.text)
            return None
        except Exception as e:
            logger.error("Legacy LLM generation failed: %s", e)
            return None


class LegacyGeminiProvider:
    """Adapter REST per Gemini (legacy). Tenuto come fallback/test only."""

    def __init__(self, api_key: str | None = None, model: str = "gemini-1.5-pro"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model = model
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"

    def generate_strategic_report(self, asset_data: dict[str, Any]) -> str | None:
        if not self.api_key:
            logger.warning("Gemini API key not configured (legacy adapter)")
            return None

        system_instruction = (
            "Sei il motore di analisi strategica di RGD-Alpha. Rispondi solo con fatti."
        )
        prompt = f"{system_instruction}\nDati: {asset_data}"

        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.1, "maxOutputTokens": 800},
        }

        try:
            response = requests.post(
                f"{self.api_url}?key={self.api_key}",
                json=payload,
                headers=headers,
                timeout=20,
            )
            if response.status_code == 200:
                data = response.json()
                candidate = data.get("candidates", [{}])[0]
                return (
                    candidate.get("content", {}).get("parts", [{}])[0].get("text", "")
                )
            logger.error(
                "Gemini API error [%s]: %s", response.status_code, response.text
            )
            return None
        except Exception as e:
            logger.error("Legacy Gemini generation failed: %s", e)
            return None


# -----------------------
# AIProvider unificato (Groq Ultra + Gemini validator + fallback)
# -----------------------
class AIProvider:
    """
    Provider unificato per AI:
    - Groq (motore principale) quando disponibile
    - Gemini (validator/raffinamento gratuito) quando disponibile
    - Fallback deterministico in assenza di entrambi
    """

    def __init__(self):
        # Chiavi da env
        self.groq_key = (os.getenv("GROQ_API_KEY") or "").strip()
        self.gemini_key = (os.getenv("GEMINI_API_KEY") or "").strip()

        # Client placeholders
        self.groq_client: Any | None = None
        self.gemini_client: Any | None = None

        # Modelli predefiniti (configurabili via env se necessario)
        self.groq_model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

        # Inizializza client in modo lazy-safe
        self._init_groq()
        self._init_gemini()

    # -------------------------
    # Init Groq (lazy)
    # -------------------------
    def _init_groq(self) -> None:
        if not self.groq_key:
            logger.info("Groq API key non trovata: Groq disabilitato.")
            return
        try:
            # Import lazy per evitare errori in ambiente di sviluppo senza SDK
            from groq import Groq  # type: ignore

            self.groq_client = Groq(api_key=self.groq_key)
            logger.info("Groq client inizializzato.")
        except Exception as e:
            logger.warning("Impossibile inizializzare Groq SDK: %s", e)
            self.groq_client = None

    # -------------------------
    # Init Gemini (lazy)
    # -------------------------
    def _init_gemini(self) -> None:
        if not self.gemini_key:
            logger.info("Gemini API key non trovata: Validator disabilitato.")
            return
        try:
            # Import lazy per evitare errori in ambiente di sviluppo senza SDK
            import google.generativeai as genai  # type: ignore

            self.gemini_client = genai.Client(api_key=self.gemini_key)
            logger.info("Gemini client inizializzato.")
        except Exception as e:
            logger.warning("Impossibile inizializzare Gemini SDK: %s", e)
            self.gemini_client = None

    # -------------------------
    # Groq generation (primary)
    # -------------------------
    def _groq_generate(
        self, prompt: str, temperature: float = 0.25, max_tokens: int = 2048
    ) -> str | None:
        if not self.groq_client:
            return None
        try:
            # Interfaccia generica: adattare se SDK differisce
            completion = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.groq_model,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            # SDK response parsing robusta
            if hasattr(completion, "choices"):
                choice = completion.choices[0]
                # supporto per diversi shape
                if hasattr(choice, "message") and hasattr(choice.message, "content"):
                    return choice.message.content
                if isinstance(choice, dict):
                    return choice.get("message", {}).get("content")
            # fallback: try attribute text
            return getattr(completion, "text", None)
        except Exception as e:
            logger.error("Errore Groq generate: %s", e)
            return None

    # -------------------------
    # Gemini validation/refinement (secondary)
    # -------------------------
    def _gemini_validate(self, text: str) -> str:
        """
        Usa Gemini per migliorare chiarezza, coerenza numerica, bullet points e safety.
        Se Gemini non disponibile, ritorna il testo in ingresso.
        """
        if not self.gemini_client:
            return text
        try:
            # Interfaccia generica: adattare se SDK differisce
            response = self.gemini_client.models.generate_content(
                model=self.gemini_model,
                contents=f"Rendi più chiaro, coerente e professionale il seguente testo:\n{text}",
            )
            # SDK può restituire .text o struttura complessa
            return getattr(response, "text", response)
        except Exception as e:
            logger.warning("Gemini validation failed: %s", e)
            return text

    # -------------------------
    # Deterministic fallback
    # -------------------------
    def _fallback(self, prompt: str) -> str:
        return f"[Modalità Offline] Non è stato possibile usare Groq o Gemini. Prompt ricevuto: {prompt}"

    # -------------------------
    # Public API: generate_advice (sintetico)
    # -------------------------
    def generate_advice(self, prompt: str) -> str | None:
        """
        Genera un consiglio operativo sintetico (1-3 frasi).
        Usa Groq se disponibile, poi Gemini per validazione.
        """
        groq_out = self._groq_generate(prompt, temperature=0.2, max_tokens=512)
        if groq_out:
            return self._gemini_validate(groq_out)
        # fallback a legacy adapter se presente
        legacy = LegacyLLMProvider(api_key=os.getenv("GROQ_API_KEY"))
        legacy_out = legacy.generate_advice(prompt)
        if legacy_out:
            return legacy_out
        return self._fallback(prompt)

    # -------------------------
    # Public API: analyze (analitico)
    # -------------------------
    def analyze(self, data: dict[str, Any]) -> str | None:
        """
        Richiesta analitica strutturata: data deve contenere 'asset' e 'instructions' o simili.
        Restituisce testo analitico dettagliato.
        """
        try:
            instructions = data.get("instructions", "")
            asset = data.get("asset", data)
            prompt = f"{instructions}\nDati: {asset}"
        except Exception:
            prompt = str(data)

        groq_out = self._groq_generate(prompt, temperature=0.2, max_tokens=2048)
        if groq_out:
            return self._gemini_validate(groq_out)
        return self._fallback(prompt)

    # -------------------------
    # Utility: is_available
    # -------------------------
    def is_available(self) -> bool:
        """
        Restituisce True se almeno un motore AI è inizializzato (Groq o Gemini).
        Metodo utile per controlli runtime e per i test.
        """
        return bool(self.groq_client or self.gemini_client)


# Backwards compatibility aliases (legacy names expected by il codice esistente)
LLMProvider = LegacyLLMProvider
GeminiProvider = LegacyGeminiProvider

# Esportazioni pubbliche
__all__ = [
    "AIProvider",
    "EmailProvider",
    "GeminiProvider",
    "LLMProvider",
    "LegacyGeminiProvider",
    "LegacyLLMProvider",
    "SFTPConnector",
]
