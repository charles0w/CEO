from typing import Any

import httpx

from config import settings
from services.llm_provider import BaseLLMProvider
from services.llm_tools import OLLAMA_TOOLS, build_system_prompt, invoke_tool


class OllamaService(BaseLLMProvider):
    name = "ollama"

    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None,
        think: bool | str | None = None,
        max_tool_rounds: int | None = None,
        timeout: float | None = None,
    ):
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.model = model or settings.ollama_model
        self.think = settings.ollama_think if think is None else think
        self.max_tool_rounds = max_tool_rounds or settings.ollama_tool_iterations
        self.timeout = timeout or settings.ollama_timeout_seconds
        self.messages: list[dict[str, Any]] = []
        self._reset_messages()

    def _reset_messages(self):
        self.messages = [{"role": "system", "content": build_system_prompt()}]

    def _chat_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": self.messages,
            "tools": OLLAMA_TOOLS,
            "stream": False,
        }
        if self.think not in (None, ""):
            payload["think"] = self.think
        return payload

    @staticmethod
    def _normalize_assistant_message(message: dict[str, Any]) -> dict[str, Any]:
        normalized = {
            "role": message.get("role", "assistant"),
            "content": message.get("content", ""),
        }
        if message.get("thinking"):
            normalized["thinking"] = message["thinking"]
        if message.get("tool_calls"):
            normalized["tool_calls"] = message["tool_calls"]
        if message.get("images"):
            normalized["images"] = message["images"]
        return normalized

    async def send(self, message: str) -> str:
        self.messages.append({"role": "user", "content": message})

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                for _ in range(self.max_tool_rounds):
                    response = await client.post(f"{self.base_url}/chat", json=self._chat_payload())
                    response.raise_for_status()
                    payload = response.json()

                    assistant_message = self._normalize_assistant_message(payload.get("message") or {})
                    self.messages.append(assistant_message)

                    tool_calls = assistant_message.get("tool_calls") or []
                    if not tool_calls:
                        return assistant_message.get("content") or "[No response]"

                    for tool_call in tool_calls:
                        function = tool_call.get("function", {})
                        tool_name = function.get("name", "")
                        arguments = function.get("arguments")
                        result = invoke_tool(tool_name, arguments)
                        self.messages.append(
                            {
                                "role": "tool",
                                "tool_name": tool_name,
                                "content": result,
                            }
                        )

            return "CEO Error: Ollama tool loop exceeded the configured limit."
        except httpx.HTTPError as exc:
            return f"CEO Error: Ollama request failed: {exc}"
        except Exception as exc:  # pragma: no cover - defensive runtime guard
            return f"CEO Error: {exc}"

    def reset(self) -> str:
        self._reset_messages()
        return "Conversation cleared. Ready for your next command, Boss."
