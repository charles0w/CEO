from typing import Any
import time

import httpx

from config import settings
from services.llm_provider import BaseLLMProvider, ProviderTelemetry
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
        super().__init__()
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

    def _record_response_telemetry(
        self,
        *,
        text: str,
        duration_ms: float,
        payload: dict[str, Any] | None = None,
        tool_names: list[str] | None = None,
        rounds: int = 0,
        error: str | None = None,
    ) -> None:
        payload = payload or {}
        self._record_telemetry(
            ProviderTelemetry(
                provider=self.name,
                model=self.model,
                duration_ms=duration_ms,
                response_chars=len(text),
                response_words=len(text.split()),
                tool_call_count=len(tool_names or []),
                tool_names=tool_names or [],
                rounds=rounds,
                finish_reason=payload.get("done_reason"),
                prompt_eval_count=payload.get("prompt_eval_count"),
                eval_count=payload.get("eval_count"),
                total_duration_ns=payload.get("total_duration"),
                load_duration_ns=payload.get("load_duration"),
                prompt_eval_duration_ns=payload.get("prompt_eval_duration"),
                eval_duration_ns=payload.get("eval_duration"),
                error=error,
            )
        )

    @staticmethod
    def _error_detail(exc: Exception) -> str:
        detail = str(exc).strip()
        if detail:
            return f"{exc.__class__.__name__}: {detail}"
        return exc.__class__.__name__

    async def send(self, message: str) -> str:
        self.messages.append({"role": "user", "content": message})
        started = time.perf_counter()
        rounds = 0
        tool_names: list[str] = []
        last_payload: dict[str, Any] | None = None

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                for _ in range(self.max_tool_rounds):
                    rounds += 1
                    response = await client.post(f"{self.base_url}/chat", json=self._chat_payload())
                    response.raise_for_status()
                    payload = response.json()
                    last_payload = payload

                    assistant_message = self._normalize_assistant_message(payload.get("message") or {})
                    self.messages.append(assistant_message)

                    tool_calls = assistant_message.get("tool_calls") or []
                    if not tool_calls:
                        text = assistant_message.get("content") or "[No response]"
                        self._record_response_telemetry(
                            text=text,
                            duration_ms=round((time.perf_counter() - started) * 1000, 1),
                            payload=last_payload,
                            tool_names=tool_names,
                            rounds=rounds,
                        )
                        return text

                    for tool_call in tool_calls:
                        function = tool_call.get("function", {})
                        tool_name = function.get("name", "")
                        arguments = function.get("arguments")
                        if tool_name:
                            tool_names.append(tool_name)
                        result = invoke_tool(tool_name, arguments)
                        self.messages.append(
                            {
                                "role": "tool",
                                "tool_name": tool_name,
                                "content": result,
                            }
                        )

            error_text = "CEO Error: Ollama tool loop exceeded the configured limit."
            self._record_response_telemetry(
                text=error_text,
                duration_ms=round((time.perf_counter() - started) * 1000, 1),
                payload=last_payload,
                tool_names=tool_names,
                rounds=rounds,
                error=error_text,
            )
            return error_text
        except httpx.HTTPError as exc:
            error_detail = self._error_detail(exc)
            error_text = f"CEO Error: Ollama request failed: {error_detail}"
            self._record_response_telemetry(
                text=error_text,
                duration_ms=round((time.perf_counter() - started) * 1000, 1),
                payload=last_payload,
                tool_names=tool_names,
                rounds=rounds,
                error=error_detail,
            )
            return error_text
        except Exception as exc:  # pragma: no cover - defensive runtime guard
            error_detail = self._error_detail(exc)
            error_text = f"CEO Error: {error_detail}"
            self._record_response_telemetry(
                text=error_text,
                duration_ms=round((time.perf_counter() - started) * 1000, 1),
                payload=last_payload,
                tool_names=tool_names,
                rounds=rounds,
                error=error_detail,
            )
            return error_text

    def reset(self) -> str:
        self._clear_telemetry()
        self._reset_messages()
        return "Conversation cleared. Ready for your next command, Boss."
