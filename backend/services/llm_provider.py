from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class ProviderTelemetry:
    provider: str
    model: str | None = None
    duration_ms: float | None = None
    response_chars: int = 0
    response_words: int = 0
    tool_call_count: int = 0
    tool_names: list[str] = field(default_factory=list)
    rounds: int | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    finish_reason: str | None = None
    prompt_eval_count: int | None = None
    eval_count: int | None = None
    total_duration_ns: int | None = None
    load_duration_ns: int | None = None
    prompt_eval_duration_ns: int | None = None
    eval_duration_ns: int | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        return {
            key: value
            for key, value in data.items()
            if value is not None and not (isinstance(value, list) and not value)
        }


class BaseLLMProvider(ABC):
    name: str

    def __init__(self):
        self._last_telemetry: ProviderTelemetry | None = None

    def get_last_telemetry(self) -> ProviderTelemetry | None:
        return self._last_telemetry

    def _record_telemetry(self, telemetry: ProviderTelemetry) -> None:
        self._last_telemetry = telemetry

    def _clear_telemetry(self) -> None:
        self._last_telemetry = None

    @abstractmethod
    async def send(self, message: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def reset(self) -> str:
        raise NotImplementedError
