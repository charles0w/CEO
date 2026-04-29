from typing import Any
import time

import httpx

from config import settings
from services.llm_provider import BaseLLMProvider, ProviderTelemetry
from services.llm_tools import OLLAMA_TOOLS, build_system_prompt, invoke_tool

OLLAMA_MODELS_WITHOUT_TOOL_SUPPORT = (
    "gemma3:",
    "phi4:",
)
OLLAMA_TOOL_UNSUPPORTED_MARKER = "does not support tools"


class OllamaService(BaseLLMProvider):
    name = "ollama"

    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None,
        think: bool | str | None = None,
        max_tool_rounds: int | None = None,
        timeout: float | None = None,
        tools_enabled: bool | str | None = None,
    ):
        super().__init__()
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.model = model or settings.ollama_model
        self.think = settings.ollama_think if think is None else think
        self.max_tool_rounds = max_tool_rounds or settings.ollama_tool_iterations
        self.timeout = timeout or settings.ollama_timeout_seconds
        self.tools_setting = settings.ollama_tools_enabled if tools_enabled is None else tools_enabled
        self.tools_enabled = self._resolve_tools_enabled(
            self.tools_setting
        )
        self.tools_mode = self._resolve_tools_mode(self.tools_setting, self.tools_enabled)
        self.tool_fallback_triggered = False
        self.messages: list[dict[str, Any]] = []
        self._reset_messages()

    def _resolve_tools_enabled(self, value: bool | str | None) -> bool:
        if isinstance(value, bool):
            return value

        normalized = "" if value is None else str(value).strip().lower()
        if normalized in {"", "auto", "none", "null"}:
            model_name = self.model.strip().lower()
            return not model_name.startswith(OLLAMA_MODELS_WITHOUT_TOOL_SUPPORT)
        if normalized in {"true", "1", "yes", "on"}:
            return True
        if normalized in {"false", "0", "no", "off"}:
            return False
        raise ValueError(f"Invalid Ollama tools setting: {value!r}. Use true, false, or auto.")

    @staticmethod
    def _resolve_tools_mode(value: bool | str | None, tools_enabled: bool) -> str:
        if isinstance(value, bool):
            return "forced-enabled" if value else "forced-disabled"

        normalized = "" if value is None else str(value).strip().lower()
        if normalized in {"", "auto", "none", "null"}:
            return "auto-enabled" if tools_enabled else "auto-disabled"
        if normalized in {"true", "1", "yes", "on"}:
            return "forced-enabled"
        if normalized in {"false", "0", "no", "off"}:
            return "forced-disabled"
        return "invalid"

    @staticmethod
    def _is_tool_unsupported_error(error_detail: str) -> bool:
        return OLLAMA_TOOL_UNSUPPORTED_MARKER in error_detail.lower()

    def _disable_tools_after_fallback(self) -> None:
        self.tools_enabled = False
        self.tools_mode = "fallback-disabled"
        self.tool_fallback_triggered = True

    def health_details(self) -> dict[str, Any]:
        return {
            "ollama_base_url": self.base_url,
            "ollama_tools_enabled": self.tools_enabled,
            "ollama_tools_mode": self.tools_mode,
            "ollama_tool_fallback_triggered": self.tool_fallback_triggered,
        }

    def _reset_messages(self):
        self.messages = [{"role": "system", "content": build_system_prompt()}]

    def _chat_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": self.messages,
            "stream": False,
        }
        if self.tools_enabled:
            payload["tools"] = OLLAMA_TOOLS
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
                tools_enabled=self.tools_enabled,
                tool_fallback=self.tool_fallback_triggered,
                error=error,
            )
        )

    @staticmethod
    def _error_detail(exc: Exception) -> str:
        detail = str(exc).strip()
        if isinstance(exc, httpx.HTTPStatusError):
            response_text = exc.response.text.strip()
            if response_text:
                detail = f"{detail} - {response_text}" if detail else response_text
        if detail:
            return f"{exc.__class__.__name__}: {detail}"
        return exc.__class__.__name__

    async def send(self, message: str) -> str:
        self.messages.append({"role": "user", "content": message})
        started = time.perf_counter()
        rounds = 0
        tool_names: list[str] = []
        last_payload: dict[str, Any] | None = None

        async def run_chat_loop(client: httpx.AsyncClient) -> str:
            nonlocal rounds, tool_names, last_payload
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

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                try:
                    return await run_chat_loop(client)
                except httpx.HTTPError as exc:
                    error_detail = self._error_detail(exc)
                    if (
                        self.tools_enabled
                        and self.tools_mode == "auto-enabled"
                        and self._is_tool_unsupported_error(error_detail)
                    ):
                        self._disable_tools_after_fallback()
                        return await run_chat_loop(client)
                    raise
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
