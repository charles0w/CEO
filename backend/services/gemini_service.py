import asyncio
import time

from google import genai
from google.genai import types
from config import settings
from services.llm_provider import BaseLLMProvider, ProviderTelemetry
from services.llm_tools import GEMINI_TOOLS, build_system_prompt


class GeminiService(BaseLLMProvider):
    name = "gemini"

    def __init__(self, model: str | None = None):
        super().__init__()
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is required when LLM_PROVIDER=gemini.")
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model = model or settings.gemini_model
        self._new_chat()

    def _new_chat(self):
        self.chat = self.client.chats.create(
            model=self.model,
            config=types.GenerateContentConfig(
                system_instruction=build_system_prompt(),
                tools=GEMINI_TOOLS,
            ),
        )

    @staticmethod
    def _usage_value(usage_metadata, attribute: str) -> int | None:
        if usage_metadata is None:
            return None
        value = getattr(usage_metadata, attribute, None)
        if isinstance(usage_metadata, dict):
            value = usage_metadata.get(attribute, value)
        return int(value) if isinstance(value, int) else None

    @staticmethod
    def _finish_reason(response) -> str | None:
        candidates = getattr(response, "candidates", None) or []
        if not candidates:
            return None
        value = getattr(candidates[0], "finish_reason", None)
        return str(value) if value not in (None, "") else None

    async def send(self, message: str) -> str:
        loop = asyncio.get_event_loop()
        started = time.perf_counter()
        try:
            response = await loop.run_in_executor(None, self.chat.send_message, message)
            text = response.text or "[No response]"
            usage = getattr(response, "usage_metadata", None)
            self._record_telemetry(
                ProviderTelemetry(
                    provider=self.name,
                    model=self.model,
                    duration_ms=round((time.perf_counter() - started) * 1000, 1),
                    response_chars=len(text),
                    response_words=len(text.split()),
                    prompt_tokens=self._usage_value(usage, "prompt_token_count"),
                    completion_tokens=self._usage_value(usage, "candidates_token_count"),
                    total_tokens=self._usage_value(usage, "total_token_count"),
                    finish_reason=self._finish_reason(response),
                )
            )
            return text
        except Exception as e:
            error_text = f"CEO Error: {e}"
            self._record_telemetry(
                ProviderTelemetry(
                    provider=self.name,
                    model=self.model,
                    duration_ms=round((time.perf_counter() - started) * 1000, 1),
                    response_chars=len(error_text),
                    response_words=len(error_text.split()),
                    error=str(e),
                )
            )
            return error_text

    def reset(self) -> str:
        self._clear_telemetry()
        self._new_chat()
        return "Conversation cleared. Ready for your next command, Boss."
