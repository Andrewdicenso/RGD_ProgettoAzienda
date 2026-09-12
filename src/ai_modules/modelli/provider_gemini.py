import os
from typing import Any

from .base_model import AIModelInterface

try:
    import google.generativeai as genai  # type: ignore[reportMissingImports]
    from google.generativeai import types  # type: ignore[reportMissingImports]
except ImportError:  # pragma: no cover
    genai = None  # type: ignore[assignment]
    types = None  # type: ignore[assignment]


class GeminiEnterpriseProvider(AIModelInterface):
    def __init__(self):
        super().__init__()
        if genai is None:
            raise ImportError(
                "The 'google-genai' package is required. Install it with: pip install google-genai"
            )

        api_key = os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=api_key)

    def analyze(self, data: dict[str, Any]) -> str | None:
        """Implementa l'analisi dei dati richiesta dall'interfaccia."""
        prompt = f"Analizza i seguenti dati aziendali e fornisci un insight: {data}"
        return self._generate(prompt)

    def generate_advice(self, context: str) -> str | None:
        """Implementa la generazione di consigli operativi richiesta dall'interfaccia."""
        return self._generate(context)

    def _generate(self, prompt: str) -> str | None:
        try:
            if types is None:
                raise ImportError("The 'google-genai' package is required.")

            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    max_output_tokens=1024,
                ),
            )
            return response.text
        except Exception as e:
            self.log_ai_error("GeminiAPIError", str(e))
            return None
