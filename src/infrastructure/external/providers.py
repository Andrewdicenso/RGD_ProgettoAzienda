"""
External Service Providers - Integrazioni con servizi esterni (Email, Groq, Gemini, SFTP).
"""

import logging
import os
from typing import Any

import requests

logger = logging.getLogger("RGD-Alpha.External")


class EmailProvider:
    """Provider per spedire email (Gmail integration stub)."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key

    def send_email(
        self, to_email: str, subject: str, body: str, html: bool = False
    ) -> tuple[bool, str]:
        logger.info(f"Sending email to {to_email}")
        if not self.api_key:
            logger.warning("Gmail API key not configured")
            return False, "Email non configurata"
        try:
            logger.info(f"Email sent to {to_email}")
            return True, "Email inviata con successo"
        except Exception as e:
            logger.error(f"Email send failed: {e}")
            return False, f"Errore invio email: {e!s}"


class LLMProvider:
    """Provider per LLM con integrazione Groq (Llama 3 / Mixtral)."""

    def __init__(self, api_key: str | None = None, model: str = "llama3-70b-8192"):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.model = model
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"

    def generate_advice(self, prompt: str) -> str | None:
        """Genera un consiglio rapido basato su un prompt."""
        logger.info(f"Generating advice using model {self.model}...")

        if not self.api_key:
            logger.warning("Groq API key not configured")
            return "⚠️ [Modalità Offline]: GROQ_API_KEY non configurata."

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "Sei un assistente di analisi operativa rapida per RGD-Alpha.",
                },
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
            else:
                logger.error(
                    f"Groq API error [{response.status_code}]: {response.text}"
                )
                return f"Errore API LLM: {response.status_code}"
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return f"Errore di connessione: {e!s}"


class GeminiProvider:
    """Provider per Google Gemini dedicato ai report strategici approfonditi e fattuali."""

    def __init__(self, api_key: str | None = None, model: str = "gemini-1.5-pro"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model = model
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"

    def generate_strategic_report(self, asset_data: dict[str, Any]) -> str:
        """Genera un report strutturato basato unicamente su dati effettivi e risolverli se negativi."""
        if not self.api_key:
            logger.warning("Gemini API key not configured")
            return "⚠️ [Modalità Offline]: GEMINI_API_KEY non configurata per il report dettagliato."

        system_instruction = (
            "Sei il motore di analisi strategica di RGD-Alpha. "
            "Il tuo output deve essere diretto, deciso, basato unicamente sui dati numerici e di rischio forniti. "
            "Non inventare metriche o descrizioni fittizie. "
            "Se un indicatore evidenzia criticità, spiega la causa tecnica effettiva e fornisci un'azione correttiva immediata."
        )

        prompt = (
            f"DATI EFFETTIVI DELL'ASSET:\n"
            f"- ID/Nome: {asset_data.get('id')} - {asset_data.get('nome')}\n"
            f"- Categoria: {asset_data.get('categoria')}\n"
            f"- Rischio Attuale: {asset_data.get('rischio_value')} ({asset_data.get('rischio_level')})\n"
            f"- Volatilità: {asset_data.get('volatilita_value')}\n"
            f"- Momento: {asset_data.get('momentum_status')}\n\n"
            f"Stendi un report dettagliato diviso in due punti:\n"
            f"1. ANALISI DEI FATTI RILEVATI.\n"
            f"2. AZIONE CORRETTIVA DIRETTA PER LA RISOLUZIONE."
        )

        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": f"{system_instruction}\n\n{prompt}"}]}],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 800,
            },
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
            else:
                logger.error(
                    f"Gemini API error [{response.status_code}]: {response.text}"
                )
                return f"Errore API Gemini: {response.status_code}"
        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            return f"Errore di connessione a Gemini: {e!s}"


class SFTPConnector:
    """Connector per SFTP (OneDrive sync stub)."""

    def __init__(self, host: str | None = None, username: str | None = None):
        self.host = host
        self.username = username

    def sync_file(self, remote_path: str, local_path: str) -> tuple[bool, str]:
        logger.info(f"Syncing file from {remote_path}")
        if not self.host or not self.username:
            logger.warning("SFTP credentials not configured")
            return False, "SFTP non configurato"
        try:
            logger.info(f"File synced to {local_path}")
            return True, "File sincronizzato"
        except Exception as e:
            logger.error(f"SFTP sync failed: {e}")
            return False, f"Errore sync: {e!s}"
