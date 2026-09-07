import os

try:
    from google import genai  # type: ignore[reportMissingImports]
    from google.genai import types  # type: ignore[reportMissingImports]
except ImportError:  # pragma: no cover - dependency is optional at type-check time
    genai = None  # type: ignore[assignment]
    types = None  # type: ignore[assignment]


class GeminiEnterpriseProvider:
    def __init__(self):
        if genai is None:
            raise ImportError(
                "The 'google-genai' package is required. Install it with: pip install google-genai"
            )

        api_key = os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=api_key)

    def generate_strategic_insight(self, prompt: str) -> str:
        if types is None:
            raise ImportError(
                "The 'google-genai' package is required. Install it with: pip install google-genai"
            )

        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=1024,
            ),
        )
        return response.text
