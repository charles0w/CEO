from typing import TYPE_CHECKING

from services.llm_provider import BaseLLMProvider
from config import settings

if TYPE_CHECKING:
    from services.gemini_service import GeminiService
    from services.ollama_service import OllamaService


def create_provider(
    provider: str | None = None,
    model: str | None = None,
    base_url: str | None = None,
    think: bool | str | None = None,
    timeout: float | None = None,
    max_tool_rounds: int | None = None,
    tools_enabled: bool | str | None = None,
) -> BaseLLMProvider:
    provider_name = (provider or settings.llm_provider).strip().lower()
    if provider_name == "gemini":
        from services.gemini_service import GeminiService

        return GeminiService(model=model)
    if provider_name == "ollama":
        from services.ollama_service import OllamaService

        return OllamaService(
            model=model,
            base_url=base_url,
            think=think,
            timeout=timeout,
            max_tool_rounds=max_tool_rounds,
            tools_enabled=tools_enabled,
        )
    raise ValueError(
        f"Unsupported LLM_PROVIDER '{provider or settings.llm_provider}'. Expected 'gemini' or 'ollama'."
    )


class LLMService:
    def __init__(self):
        self.provider: BaseLLMProvider = create_provider()

    @property
    def provider_name(self) -> str:
        return self.provider.name

    @property
    def provider_model(self) -> str | None:
        return getattr(self.provider, "model", None)

    async def send(self, message: str) -> str:
        return await self.provider.send(message)

    def last_telemetry(self) -> dict | None:
        telemetry = self.provider.get_last_telemetry()
        return telemetry.to_dict() if telemetry else None

    def reset(self) -> str:
        return self.provider.reset()
