from ...config import Settings
from .base import AIProvider, LocalEvidenceProvider
from .gemini_provider import GeminiProvider
from .openai_provider import OpenAIProvider


def create_ai_provider(settings: Settings) -> AIProvider:
    if settings.ai_provider == "openai":
        return OpenAIProvider(settings)
    if settings.ai_provider == "local":
        return LocalEvidenceProvider()
    return GeminiProvider(settings)
