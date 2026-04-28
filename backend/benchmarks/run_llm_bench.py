import argparse
import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from typing import Any


BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# Make backend/.env resolution work with the existing config module.
os.chdir(BACKEND_ROOT)

from benchmarks.cases import BenchmarkCase, build_cases
from services.llm_provider import BaseLLMProvider, ProviderTelemetry
from services.llm_service import create_provider


@dataclass
class BenchmarkTarget:
    provider: str
    model: str | None = None
    label: str | None = None
    base_url: str | None = None
    think: bool | str | None = None
    timeout: float | None = None
    max_tool_rounds: int | None = None
    tools_enabled: bool | None = None

    @property
    def display_name(self) -> str:
        parts = [self.provider]
        if self.model:
            parts.append(self.model)
        if self.label:
            parts.append(self.label)
        if self.think is not None:
            parts.append(f"think={self.think}")
        if self.timeout is not None:
            parts.append(f"timeout={self.timeout}")
        if self.max_tool_rounds is not None:
            parts.append(f"tool_rounds={self.max_tool_rounds}")
        if self.tools_enabled is not None:
            parts.append(f"tools={str(self.tools_enabled).lower()}")
        return " / ".join(parts)


class MockProvider(BaseLLMProvider):
    name = "mock"

    def __init__(self, model: str | None = None):
        super().__init__()
        self.model = model or "mock"

    async def send(self, message: str) -> str:
        lowered = message.lower()
        if "json only" in lowered:
            response = json.dumps(
                {
                    "provider": "ollama",
                    "model_candidates": ["qwen3:8b", "gemma3:12b", "phi4:14b"],
                    "metrics": ["latency", "tool-call success", "fallback rate"],
                    "rollout_risks": ["tool regression", "higher latency", "model load failures"],
                }
            )
        elif "get_git_status_and_diff" in lowered or "commit and push" in lowered:
            response = (
                "- Call get_git_status_and_diff first.\n"
                "- Summarize the changed files and risks.\n"
                "- Ask for explicit confirmation before commit or push.\n"
                "- Only proceed after Charles confirms."
            )
        elif "connectionmanager" in lowered or "disconnect" in lowered:
            response = (
                "- The code tries to use discard on a list, which is a set method.\n"
                "- That makes the disconnect path brittle and confusing.\n"
                "- Use a plain remove guard for the list or change the collection to a set.\n"
            )
        elif "output/benchmarks" in lowered:
            response = (
                "1. Define the benchmark cases and target models.\n"
                "2. Record latency for every run.\n"
                "3. Capture tool-call success and fallback behavior.\n"
                "4. Save the full outputs under output/benchmarks.\n"
                "5. Compare results before changing the default provider."
            )
        elif "default first pick:" in lowered:
            response = (
                "- Qwen3 because it balances local quality and reasoning.\n"
                "- Gemma 3 because it is local-friendly and efficient.\n"
                "- Phi-4 because it is a strong lightweight baseline.\n"
                "Default first pick: qwen3:8b"
            )
        else:
            response = (
                "- Provider selection happens in llm_service.py.\n"
                "- The shared tool registry lives in llm_tools.py.\n"
                "- main.py receives the text message over WebSocket.\n"
                "- The provider generates a response and may call tools.\n"
                "- voice_service.py synthesizes audio from the text response.\n"
                "- The response and audio are sent back to the client."
            )
        self._record_telemetry(
            ProviderTelemetry(
                provider=self.name,
                model=self.model,
                response_chars=len(response),
                response_words=len(response.split()),
            )
        )
        return response

    def reset(self) -> str:
        self._clear_telemetry()
        return "Conversation cleared. Ready for your next command, Boss."


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run CEO benchmark cases against one or more LLM targets.")
    parser.add_argument("--provider", choices=["gemini", "ollama", "mock"], help="Provider to benchmark.")
    parser.add_argument("--model", help="Model name override for the provider.")
    parser.add_argument("--base-url", help="Base URL override for providers that use HTTP APIs.")
    parser.add_argument(
        "--think",
        help="Optional Ollama think override. Use true/false for booleans or pass a provider-specific string.",
    )
    parser.add_argument("--timeout", type=float, help="Optional provider timeout override in seconds.")
    parser.add_argument("--max-tool-rounds", type=int, help="Optional Ollama tool-loop limit override.")
    parser.add_argument(
        "--tools",
        help="Optional Ollama tools override. Use false to benchmark raw chat for models that do not support tools.",
    )
    parser.add_argument("--targets-file", help="JSON file with a list of benchmark targets.")
    parser.add_argument("--list-cases", action="store_true", help="List available benchmark cases and exit.")
    parser.add_argument(
        "--profile",
        choices=["quick", "full"],
        default="full",
        help="Named benchmark profile. 'quick' runs the light comparison subset.",
    )
    parser.add_argument("--case", action="append", help="Run only the specified case id. May be repeated.")
    parser.add_argument("--limit", type=int, help="Run only the first N selected cases.")
    parser.add_argument("--repeat", type=int, default=1, help="Repeat each case this many times per target.")
    parser.add_argument(
        "--output-dir",
        default=str(REPO_ROOT / "output" / "benchmarks"),
        help="Directory for JSON and Markdown benchmark outputs.",
    )
    return parser.parse_args()


def sanitize_filename(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-").lower()


def parse_boolish(value: Any) -> bool | str | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    lowered = str(value).strip().lower()
    if lowered in {"", "none", "null"}:
        return None
    if lowered in {"true", "1", "yes", "on"}:
        return True
    if lowered in {"false", "0", "no", "off"}:
        return False
    return value


def parse_optional_bool(value: Any, name: str) -> bool | None:
    parsed = parse_boolish(value)
    if parsed in (True, False, None):
        return parsed
    raise SystemExit(f"{name} must be true or false, got {value!r}.")


def load_targets(args: argparse.Namespace) -> list[BenchmarkTarget]:
    if args.targets_file:
        data = json.loads(Path(args.targets_file).read_text(encoding="utf-8"))
        return [
            BenchmarkTarget(
                provider=item["provider"],
                model=item.get("model"),
                label=item.get("label"),
                base_url=item.get("base_url"),
                think=parse_boolish(item.get("think")),
                timeout=item.get("timeout"),
                max_tool_rounds=item.get("max_tool_rounds"),
                tools_enabled=parse_optional_bool(item.get("tools_enabled", item.get("tools")), "tools"),
            )
            for item in data
        ]

    if not args.provider:
        raise SystemExit("Either --provider or --targets-file is required.")

    return [
        BenchmarkTarget(
            provider=args.provider,
            model=args.model,
            base_url=args.base_url,
            think=parse_boolish(args.think),
            timeout=args.timeout,
            max_tool_rounds=args.max_tool_rounds,
            tools_enabled=parse_optional_bool(args.tools, "--tools"),
        )
    ]


def select_cases(args: argparse.Namespace) -> list[BenchmarkCase]:
    cases = build_cases()
    if args.profile == "quick" and not args.case:
        quick_ids = {"git_safety_protocol", "structured_rollout_json", "local_model_selection"}
        cases = [case for case in cases if case.case_id in quick_ids]
    if args.case:
        wanted = set(args.case)
        cases = [case for case in cases if case.case_id in wanted]
    if args.limit is not None:
        cases = cases[: args.limit]
    return cases


def list_cases() -> None:
    for case in build_cases():
        print(f"{case.case_id:28} {case.category:20} {case.title}")


def current_commit() -> str | None:
    try:
        return (
            subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=True,
            )
            .stdout.strip()
        )
    except Exception:
        return None


def instantiate_provider(target: BenchmarkTarget) -> BaseLLMProvider:
    if target.provider == "mock":
        return MockProvider(model=target.model)
    return create_provider(
        provider=target.provider,
        model=target.model,
        base_url=target.base_url,
        think=target.think,
        timeout=target.timeout,
        max_tool_rounds=target.max_tool_rounds,
        tools_enabled=target.tools_enabled,
    )


async def run_target(
    target: BenchmarkTarget,
    cases: list[BenchmarkCase],
    repeat: int,
) -> dict[str, Any]:
    provider = instantiate_provider(target)
    results: list[dict[str, Any]] = []

    for case in cases:
        for attempt in range(1, repeat + 1):
            print(f"  Case {case.case_id} (attempt {attempt}/{repeat})...")
            provider.reset()
            started = time.perf_counter()
            error = None
            response = ""
            try:
                response = await provider.send(case.prompt)
            except Exception as exc:  # pragma: no cover - defensive runtime guard
                error = str(exc)
            elapsed_ms = round((time.perf_counter() - started) * 1000, 1)
            telemetry = provider.get_last_telemetry()

            evaluation = case.evaluate(response) if not error else {"score": 0.0, "details": {"error": error}}
            results.append(
                {
                    "case_id": case.case_id,
                    "title": case.title,
                    "category": case.category,
                    "attempt": attempt,
                    "latency_ms": elapsed_ms,
                    "char_count": len(response),
                    "word_count": len(response.split()),
                    "score": evaluation["score"],
                    "error": error,
                    "response": response,
                    "checks": evaluation["details"],
                    "provider_telemetry": telemetry.to_dict() if telemetry else None,
                }
            )
            status = f"score={evaluation['score']} latency_ms={elapsed_ms}"
            if error:
                status += f" error={error}"
            print(f"    done: {status}")

    avg_score = round(sum(item["score"] for item in results) / len(results), 3) if results else 0.0
    avg_latency = round(sum(item["latency_ms"] for item in results) / len(results), 1) if results else 0.0
    return {
        "target": {
            "provider": target.provider,
            "model": target.model,
            "label": target.label,
            "base_url": target.base_url,
            "think": target.think,
            "timeout": target.timeout,
            "max_tool_rounds": target.max_tool_rounds,
            "tools_enabled": target.tools_enabled,
            "display_name": target.display_name,
        },
        "summary": {
            "case_count": len(cases),
            "repeat": repeat,
            "result_count": len(results),
            "average_score": avg_score,
            "average_latency_ms": avg_latency,
        },
        "results": results,
    }


def write_outputs(output_dir: Path, bundle: dict[str, Any]) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = bundle["run"]["timestamp_utc"].replace(":", "").replace("-", "")
    label = sanitize_filename(bundle["run"]["label"])
    base = output_dir / f"{timestamp}_{label}"
    json_path = base.with_suffix(".json")
    md_path = base.with_suffix(".md")

    json_path.write_text(json.dumps(bundle, indent=2), encoding="utf-8")

    lines = [
        "# CEO Benchmark Run",
        "",
        f"- Timestamp (UTC): {bundle['run']['timestamp_utc']}",
        f"- Git commit: {bundle['run'].get('git_commit') or 'unknown'}",
        f"- Cases: {bundle['run']['case_count']}",
        "",
    ]

    for target_bundle in bundle["targets"]:
        target = target_bundle["target"]
        summary = target_bundle["summary"]
        lines.extend(
            [
                f"## {target['display_name']}",
                "",
                f"- Average score: {summary['average_score']}",
                f"- Average latency ms: {summary['average_latency_ms']}",
                f"- Results: {summary['result_count']}",
                "",
                "| Case | Category | Attempt | Latency ms | Score | Error |",
                "|---|---|---:|---:|---:|---|",
            ]
        )
        for result in target_bundle["results"]:
            lines.append(
                f"| {result['case_id']} | {result['category']} | {result['attempt']} | "
                f"{result['latency_ms']} | {result['score']} | {result['error'] or ''} |"
            )
        lines.append("")

    md_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path, md_path


async def main() -> None:
    args = parse_args()
    if args.list_cases:
        list_cases()
        return

    cases = select_cases(args)
    if not cases:
        raise SystemExit("No benchmark cases selected.")

    targets = load_targets(args)
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    run_label = targets[0].display_name if len(targets) == 1 else f"{len(targets)}-targets"

    bundles = []
    for target in targets:
        print(f"Running target: {target.display_name}")
        bundles.append(await run_target(target, cases, args.repeat))

    bundle = {
        "run": {
            "timestamp_utc": timestamp,
            "git_commit": current_commit(),
            "case_count": len(cases),
            "cases": [case.case_id for case in cases],
            "label": run_label,
        },
        "targets": bundles,
    }

    json_path, md_path = write_outputs(Path(args.output_dir), bundle)
    print(f"Wrote JSON results: {json_path}")
    print(f"Wrote Markdown summary: {md_path}")


if __name__ == "__main__":
    asyncio.run(main())
