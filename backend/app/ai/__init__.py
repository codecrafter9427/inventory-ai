"""AI provider factory — DemoAIProvider by default; optional Ollama stub."""

from app.ai.demo import DemoAIProvider
from app.ai.ollama import OllamaAIProvider
from app.ai.provider import AIProvider
from app.config import get_settings


def get_ai_provider() -> AIProvider:
    settings = get_settings()
    if settings.ai_provider.lower() == "ollama":
        return OllamaAIProvider(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
        )
    return DemoAIProvider()


__all__ = ["AIProvider", "DemoAIProvider", "OllamaAIProvider", "get_ai_provider"]
