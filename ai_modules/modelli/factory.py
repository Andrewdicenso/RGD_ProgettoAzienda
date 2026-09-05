from .base_model import AIModelInterface
from .provider_groq import GroqAIProvider


class AIFactory:
    """Factory per creare istanze di modelli AI in modo disaccoppiato."""

    @staticmethod
    def get_provider(provider_name: str = "gemini") -> AIModelInterface | None:
        """
        Restituisce il provider richiesto basandosi sulla configurazione.
        Supporta 'gemini', 'groq' o valori di default.
        """

        providers = {
            "gemini": GroqAIProvider,
            "groq": GroqAIProvider,
            # In futuro: "openai": OpenAIProvider, "anthropic": ClaudeProvider
        }

        provider_class = providers.get(provider_name.lower())

        if provider_class:
            return provider_class()

        # Fallback di sicurezza: se il nome del provider non viene trovato, usa GroqAIProvider
        return GroqAIProvider()
