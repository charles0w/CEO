import asyncio
from google import genai
from google.genai import types
from config import settings
from services.llm_provider import BaseLLMProvider
from services.llm_tools import GEMINI_TOOLS, build_system_prompt


class GeminiService(BaseLLMProvider):
    name = "gemini"

    def __init__(self, model: str | None = None):
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

    async def send(self, message: str) -> str:
        loop = asyncio.get_event_loop()
        try:
            response = await loop.run_in_executor(None, self.chat.send_message, message)
            return response.text or "[No response]"
        except Exception as e:
            return f"CEO Error: {e}"

    def reset(self) -> str:
        self._new_chat()
        return "Conversation cleared. Ready for your next command, Boss."
