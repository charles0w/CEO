from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]


def _excerpt(path: str, start: int, end: int) -> str:
    lines = (REPO_ROOT / path).read_text(encoding="utf-8").splitlines()
    sliced = lines[start - 1:end]
    numbered = [f"{idx + start}: {line}" for idx, line in enumerate(sliced)]
    return "\n".join(numbered)


def _short_file(path: str, max_lines: int = 80) -> str:
    lines = (REPO_ROOT / path).read_text(encoding="utf-8").splitlines()
    numbered = [f"{idx + 1}: {line}" for idx, line in enumerate(lines[:max_lines])]
    return "\n".join(numbered)


def _markdown_section(path: str, heading: str) -> str:
    lines = (REPO_ROOT / path).read_text(encoding="utf-8").splitlines()
    start = None
    for idx, line in enumerate(lines):
        if line.strip() == heading:
            start = idx
            break
    if start is None:
        raise ValueError(f"Heading {heading!r} not found in {path}")

    end = len(lines)
    for idx in range(start + 1, len(lines)):
        if lines[idx].startswith("## ") and idx > start:
            end = idx
            break
    return "\n".join(lines[start:end])


@dataclass
class BenchmarkCase:
    case_id: str
    category: str
    title: str
    prompt: str
    must_include: list[str] = field(default_factory=list)
    include_any_groups: list[list[str]] = field(default_factory=list)
    json_required_keys: list[str] = field(default_factory=list)

    def evaluate(self, response: str) -> dict[str, Any]:
        lowered = response.lower()
        checks: list[bool] = []
        details: dict[str, Any] = {
            "must_include": {},
            "include_any_groups": [],
            "json": None,
        }

        for term in self.must_include:
            hit = term.lower() in lowered
            details["must_include"][term] = hit
            checks.append(hit)

        for group in self.include_any_groups:
            hit = any(term.lower() in lowered for term in group)
            details["include_any_groups"].append({"terms": group, "hit": hit})
            checks.append(hit)

        if self.json_required_keys:
            json_result = {"valid": False, "missing_keys": list(self.json_required_keys)}
            try:
                parsed = json.loads(response)
                if isinstance(parsed, dict):
                    missing = [key for key in self.json_required_keys if key not in parsed]
                    json_result = {"valid": True, "missing_keys": missing}
                    checks.append(not missing)
                else:
                    checks.append(False)
            except json.JSONDecodeError:
                checks.append(False)
            details["json"] = json_result

        score = 1.0 if not checks else sum(1 for item in checks if item) / len(checks)
        return {
            "score": round(score, 3),
            "details": details,
        }


def build_cases() -> list[BenchmarkCase]:
    return [
        BenchmarkCase(
            case_id="repo_message_flow",
            category="architecture",
            title="Explain the current message flow",
            prompt=(
                "You are evaluating the CEO assistant backend.\n\n"
                "Using the repo excerpts below, summarize the end-to-end flow for a text message in exactly 6 bullets. "
                "You must mention provider selection, the shared tool registry, and voice/audio output.\n\n"
                "[backend/main.py excerpt]\n"
                f"{_excerpt('backend/main.py', 1, 120)}\n\n"
                "[backend/services/llm_service.py]\n"
                f"{_short_file('backend/services/llm_service.py', 80)}\n\n"
                "[backend/services/llm_tools.py excerpt]\n"
                f"{_excerpt('backend/services/llm_tools.py', 1, 90)}"
            ),
            must_include=["provider", "tool", "audio"],
        ),
        BenchmarkCase(
            case_id="git_safety_protocol",
            category="safety",
            title="Follow the git safety protocol",
            prompt=(
                "I changed files and I want CEO to commit and push them for me.\n"
                "What exact protocol must CEO follow first? Keep the answer to 4 bullets."
            ),
            must_include=["get_git_status_and_diff", "confirm"],
        ),
        BenchmarkCase(
            case_id="connection_manager_bug_review",
            category="code-review",
            title="Spot the bug in ConnectionManager.disconnect",
            prompt=(
                "Review this code and identify the main bug or behavioral risk. "
                "Then propose the smallest safe fix in 2-4 bullets.\n\n"
                "[backend/main.py ConnectionManager excerpt]\n"
                f"{_excerpt('backend/main.py', 24, 42)}"
            ),
            include_any_groups=[["discard", "list"], ["remove", "set"]],
        ),
        BenchmarkCase(
            case_id="provider_telemetry_plan",
            category="implementation-plan",
            title="Plan benchmark telemetry work",
            prompt=(
                "You are planning the next engineering step for CEO.\n"
                "Give a concrete 5-step plan to benchmark multiple local models in this repo. "
                "Mention latency, tool-call success, fallback behavior, and where results should be stored."
            ),
            must_include=["latency", "tool", "fallback", "output/benchmarks"],
        ),
        BenchmarkCase(
            case_id="structured_rollout_json",
            category="structured-output",
            title="Return rollout advice as strict JSON",
            prompt=(
                "Return JSON only. No prose.\n"
                "Provide an object with exactly these keys: "
                "provider, model_candidates, metrics, rollout_risks.\n"
                "The values should describe how to evaluate a first local provider for CEO."
            ),
            json_required_keys=["provider", "model_candidates", "metrics", "rollout_risks"],
        ),
        BenchmarkCase(
            case_id="local_model_selection",
            category="model-selection",
            title="Choose the first Ollama benchmark targets",
            prompt=(
                "Use the research excerpt below to pick the first 3 Ollama models CEO should benchmark on Apple Silicon. "
                "Give one sentence of justification for each. End with a line that starts exactly with 'Default first pick:'.\n\n"
                "[docs/research/llm-landscape-2026-04.md excerpt]\n"
                f"{_markdown_section('docs/research/llm-landscape-2026-04.md', '### Recommended local model shortlist for first benchmarks')}"
            ),
            must_include=["default first pick:"],
            include_any_groups=[["qwen", "gemma", "mistral", "gpt-oss", "phi", "devstral"]],
        ),
    ]
