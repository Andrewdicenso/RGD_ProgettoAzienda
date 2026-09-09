from .base_model import AIModelInterface
from .provider_groq import GroqAIProvider

# from .provider_gemini import GeminiAIProvider  # Eventuale import futuro o esistente


class AIFactory:
    """Factory per creare istanze di modelli AI in modo disaccoppiato."""

    @staticmethod
    def get_provider(provider_name: str = "gemini") -> AIModelInterface | None:
        """
        Restituisce il provider richiesto basandosi sulla configurazione.
        """
        providers = {
            # "gemini": GeminiAIProvider,  # Decommenta quando disponibile
            "groq": GroqAIProvider,
        }

        provider_class = providers.get(provider_name.lower())

        if provider_class:
            return provider_class()

        # Fallback di sicurezza
        return GroqAIProvider()
