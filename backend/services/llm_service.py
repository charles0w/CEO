from services.gemini_service import GeminiService
from services.llm_provider import BaseLLMProvider
from services.ollama_service import OllamaService
from config import settings


class LLMService:
    def __init__(self):
        provider = settings.llm_provider.strip().lower()
        if provider == "gemini":
            self.provider: BaseLLMProvider = GeminiService()
        elif provider == "ollama":
            self.provider = OllamaService()
        else:
            raise ValueError(
                f"Unsupported LLM_PROVIDER '{settings.llm_provider}'. Expected 'gemini' or 'ollama'."
            )

    @property
    def provider_name(self) -> str:
        return self.provider.name

    async def send(self, message: str) -> str:
        return await self.provider.send(message)

    def reset(self) -> str:
        return self.provider.reset()
