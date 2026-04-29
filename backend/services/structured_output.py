import json
from dataclasses import dataclass
from typing import Any


@dataclass
class JsonObjectResult:
    data: dict[str, Any] | None
    valid: bool
    repaired: bool
    missing_keys: list[str]
    error: str | None = None


def extract_json_object_text(text: str) -> str | None:
    stripped = text.strip()
    if not stripped:
        return None

    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        candidate = "\n".join(lines).strip()
        return candidate or None

    start = stripped.find("{")
    end = stripped.rfind("}")
    if start != -1 and end > start:
        return stripped[start : end + 1]
    return None


def parse_json_object(
    text: str,
    required_keys: list[str] | None = None,
    *,
    allow_repair: bool = True,
) -> JsonObjectResult:
    required_keys = required_keys or []

    def build_result(data: Any, *, repaired: bool) -> JsonObjectResult:
        if not isinstance(data, dict):
            return JsonObjectResult(
                data=None,
                valid=False,
                repaired=repaired,
                missing_keys=list(required_keys),
                error=f"Expected object, got {type(data).__name__}",
            )
        missing = [key for key in required_keys if key not in data]
        return JsonObjectResult(
            data=data,
            valid=not missing,
            repaired=repaired,
            missing_keys=missing,
        )

    try:
        return build_result(json.loads(text), repaired=False)
    except json.JSONDecodeError as exc:
        if not allow_repair:
            return JsonObjectResult(
                data=None,
                valid=False,
                repaired=False,
                missing_keys=list(required_keys),
                error=str(exc),
            )

    candidate = extract_json_object_text(text)
    if not candidate or candidate == text.strip():
        return JsonObjectResult(
            data=None,
            valid=False,
            repaired=False,
            missing_keys=list(required_keys),
            error="No JSON object found.",
        )

    try:
        return build_result(json.loads(candidate), repaired=True)
    except json.JSONDecodeError as exc:
        return JsonObjectResult(
            data=None,
            valid=False,
            repaired=True,
            missing_keys=list(required_keys),
            error=str(exc),
        )
