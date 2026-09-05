"""
AI Provider Module - RGD-Alpha Enterprise.
Gestisce in modo difensivo e resiliente la connessione con i modelli di IA:
1. Google Gemini (Provider Primario)
2. Groq AI (Provider Secondario/Fallback)
3. Modalità Offline/Deterministica (Protezione da crash di rete o chiavi mancanti)
"""

import logging
import os
from typing import Any

from .base_model import AIModelInterface

logger = logging.getLogger("RGD-Alpha.AIProvider")


class GroqAIProvider(AIModelInterface):
    """
    Provider AI Multi-Engine ad alta affidabilità per RGD-Alpha Enterprise.
    Garantisce l'esecuzione continua dell'app anche in assenza di credenziali AI.
    """

    def __init__(self):
        super().__init__()

        # Pulizia e recupero delle chiavi d'ambiente
        self.gemini_key: str = (os.getenv("GEMINI_API_KEY") or "").strip()
        self.groq_key: str = (os.getenv("GROQ_API_KEY") or "").strip()

        self.client: Any = None
        self.provider_type: str | None = None
        self.model_name: str = "gemini-2.5-flash"

        # ------------------------------------------------------------------
        # 1. TENTATIVO INIZIALIZZAZIONE PRIMARIA: GOOGLE GEMINI
        # ------------------------------------------------------------------
        if self.gemini_key:
            try:
                from google import genai

                self.client = genai.Client(api_key=self.gemini_key)
                self.provider_type = "gemini"
                logger.info(
                    "✅ Provider AI Primario (Google Gemini) inizializzato con successo."
                )
            except Exception as e:
                logger.error(
                    f"⚠️ Errore durante l'inizializzazione del client Gemini: {e}"
                )
                self.client = None

        # ------------------------------------------------------------------
        # 2. TENTATIVO INIZIALIZZAZIONE SECONDARIA: GROQ AI
        # ------------------------------------------------------------------
        if not self.client and self.groq_key:
            try:
                from groq import Groq

                self.client = Groq(api_key=self.groq_key)
                self.provider_type = "groq"
                self.model_name = "llama-3.3-70b-versatile"
                logger.info(
                    "✅ Provider AI Secondario (Groq) inizializzato con successo."
                )
            except Exception as e:
                logger.error(
                    f"⚠️ Errore durante l'inizializzazione del client Groq: {e}"
                )
                self.client = None

        # ------------------------------------------------------------------
        # 3. FALLBACK OFFLINE / DETERMINISTICO
        # ------------------------------------------------------------------
        if not self.client:
            logger.warning(
                "ℹ️ Nessuna API Key (Gemini/Groq) valida configurata. "
                "Attivata modalità Fallback offline (Nessun blocco dell'applicazione)."
            )

    def analyze(self, data: dict[str, Any]) -> str | None:
        """
        Analizza i dati di business forniti e restituisce insight strategici.
        """
        if not self.client:
            return "Analisi AI non disponibile in modalità offline. Utilizzare il motore di calcolo deterministico."

        prompt = (
            "Sei il motore di intelligenza artificiale di RGD-Alpha, consulente B2B esperto in Risk Management e Business Intelligence per PMI.\n"
            f"Analizza i seguenti dati aziendali e identifica inefficienze, rischi operativi e sprechi: {data}"
        )

        try:
            if self.provider_type == "gemini":
                response = self.client.models.generate_content(
                    model=self.model_name, contents=prompt
                )
                return response.text

            elif self.provider_type == "groq":
                completion = self.client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model=self.model_name,
                    temperature=0.3,
                )
                return completion.choices[0].message.content

        except Exception as e:
            err_msg = (
                f"Errore durante l'analisi con il provider {self.provider_type}: {e}"
            )
            if hasattr(self, "log_ai_error"):
                self.log_ai_error("AI_ANALYSIS_ERROR", err_msg)
            else:
                logger.error(err_msg)
            return None

    def generate_advice(self, context: str) -> str | None:
        """
        Genera un consiglio operativo sintetico, scorrevole e azionabile per la War Room.
        """
        if not self.client:
            return None  # Ritorna None in modo che l'AnalysisService attivi l'algoritmo interno

        prompt = (
            "Agisci come un consulente aziendale senior specializzato in PMI italiane. "
            "Sii sintetico, diretto e usa un linguaggio professionale ma chiaro. "
            f"Fornisci un consiglio operativo su come recuperare margini e mitigare i rischi basandoti su: {context}"
        )

        try:
            if self.provider_type == "gemini":
                response = self.client.models.generate_content(
                    model=self.model_name, contents=prompt
                )
                return response.text

            elif self.provider_type == "groq":
                completion = self.client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model=self.model_name,
                    temperature=0.3,
                )
                return completion.choices[0].message.content

        except Exception as e:
            err_msg = f"Errore durante la generazione del consiglio con il provider {self.provider_type}: {e}"
            if hasattr(self, "log_ai_error"):
                self.log_ai_error("AI_ADVICE_ERROR", err_msg)
            else:
                logger.error(err_msg)
            return None


# Alias per la compatibilità con il Factory Pattern e la Dependency Injection
GroqProvider = GroqAIProvider
