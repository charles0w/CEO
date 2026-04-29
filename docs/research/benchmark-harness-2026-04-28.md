# CEO benchmark harness notes

Date: 2026-04-28
Status: benchmark harness added before first real local-model comparison

## What was added

A reusable benchmark harness now exists under `backend/benchmarks/`.

Files:
- `backend/benchmarks/run_llm_bench.py`
- `backend/benchmarks/cases.py`
- `backend/benchmarks/targets.research-shortlist.example.json`
- `backend/benchmarks/README.md`

Related backend changes:
- `backend/services/llm_service.py` now supports provider overrides for benchmark runs
- `backend/services/gemini_service.py` accepts an optional model override
- `backend/services/ollama_service.py` accepts model/base-url overrides and safer error handling
- `backend/config.py` resolves `backend/.env` more reliably for benchmark execution
- `README.md` now includes benchmark usage instructions

## Harness goals

This harness is not meant to be a complete automatic judge of model quality.
Its purpose is to give CEO a repeatable screening tool for local and hosted model candidates.

What it captures:
- per-case latency
- response size
- heuristic score based on required content or JSON validity
- raw model outputs for later manual review

## Current case set

The first case set is CEO-specific rather than benchmark-generic.

It covers:
- architecture understanding
- git safety behavior
- code review / bug spotting
- implementation planning
- structured JSON output
- local model selection reasoning

## Design decisions

1. The harness uses fixed benchmark cases instead of free-form prompts.
2. Results are written to `output/benchmarks/` as both JSON and Markdown.
3. A `mock` provider exists so the harness can be validated without depending on a real model runtime.
4. Provider creation is lazy, so listing cases or running `mock` does not require Gemini packages to be installed.
5. The case suite reads repo files directly so the prompts stay grounded in the actual codebase.

## Validation completed

Validation run on 2026-04-28:
- `python3 -m py_compile backend/config.py backend/services/*.py backend/benchmarks/*.py`
- `cd backend && python3 -m benchmarks.run_llm_bench --list-cases`
- `cd backend && python3 -m benchmarks.run_llm_bench --provider mock --limit 3 --output-dir /tmp/ceo-bench-test`

Observed result:
- the harness listed all expected cases
- the mock provider completed a benchmark run and produced JSON + Markdown outputs

## Important limitation before real benchmarking

At the time this note was written, the local machine only had this Ollama model installed:
- `qwen2.5-coder:14b`

The planned first comparison targets are still:
- `qwen3:8b`
- `gemma3:12b`
- `phi4:14b`

Those need to be pulled locally before the first real benchmark pass.

## Next step

1. Pull the first three Ollama benchmark targets.
2. Run the harness across all three.
3. Save the benchmark outputs and an analysis note in the repo.
4. Pick the strongest first default candidate for CEO local testing.

## Iteration 2: practical improvements after the first live run

After the first real Ollama baseline, two usability issues became clear:
- long runs produced no progress output until the target finished
- the lighter 3-case subset had to be selected manually

Changes made after that observation:
- added per-case progress logging in `backend/benchmarks/run_llm_bench.py`
- added a built-in `--profile quick` option for the lighter comparison subset
- documented the quick profile in `backend/benchmarks/README.md`

Validation for this iteration:
- `python3 -m py_compile backend/benchmarks/*.py`
- `cd backend && python3 -m benchmarks.run_llm_bench --provider mock --profile quick --output-dir /tmp/ceo-bench-quick`

## Iteration 3: provider telemetry and runtime visibility

The next bottleneck after the first benchmark pass was observability.
Average latency alone was not enough to compare local-model behavior with any confidence.

Changes made in this iteration:
- added a shared `ProviderTelemetry` structure in `backend/services/llm_provider.py`
- `GeminiService` now records per-request duration, response size, token counts when available, and finish reason
- `OllamaService` now records per-request duration, response size, tool-call count, tool names, tool-loop rounds, and Ollama eval/load timing fields when returned by the API
- `main.py` now logs per-request LLM telemetry and exposes both `llm_provider` and `llm_model` on `/health`
- `backend/benchmarks/run_llm_bench.py` now stores `provider_telemetry` alongside each benchmark result
- `backend/benchmarks/README.md` and the root `README.md` were updated to mention the new visibility

Why this matters:
- benchmark comparisons now preserve provider-native metadata instead of only outer-wall-clock timing
- live backend runs can confirm which provider and model actually answered each request
- Ollama tool-loop behavior is now measurable instead of inferred from raw text alone

Validation for this iteration:
- `python3 -m py_compile backend/main.py`
- `python3 -m py_compile backend/config.py`
- `python3 -m py_compile backend/services/*.py`
- `python3 -m py_compile backend/benchmarks/*.py`
- `cd backend && python3 -m benchmarks.run_llm_bench --provider mock --profile quick --output-dir /tmp/ceo-bench-telemetry-2`

Observed validation result:
- the mock benchmark completed successfully
- the JSON output now includes `provider_telemetry` per case
- the telemetry payload at minimum includes provider, model, and response size, with richer fields available for real providers

## Iteration 4: normalize blank Ollama timeout errors

The first `qwen3:8b` quick-profile run revealed a concrete logging defect:
- a timeout-style Ollama failure could surface as `CEO Error: Ollama request failed:` with an empty suffix
- the matching telemetry record could store `error: ""`

Change made in this iteration:
- `backend/services/ollama_service.py` now normalizes exception details so blank-message failures still report their exception class, for example `ReadTimeout`

Why this matters:
- future benchmark failures will be easier to classify without reading surrounding logs
- timeout regressions can be separated from model-quality failures in the saved benchmark artifacts

## Iteration 5: benchmark runtime-override support

The `qwen3:8b` timeout result also exposed a workflow gap:
- the harness could compare models, but not configuration variants of the same model
- changing timeout or think behavior required editing shared app settings

Changes made in this iteration:
- `backend/benchmarks/run_llm_bench.py` now accepts `--think`, `--timeout`, and `--max-tool-rounds`
- target JSON files can now carry the same fields per target
- `backend/services/llm_service.py` now passes those overrides through to `OllamaService`
- added `backend/benchmarks/targets.qwen3-variants.example.json` for side-by-side config testing
- updated benchmark docs with single-run and target-file examples for config variants

Why this matters:
- the next `qwen3:8b` rerun can distinguish model weakness from runtime misconfiguration
- later local comparisons can test safer time budgets without mutating `backend/.env`

## Iteration 6: Ollama HTTP error bodies and tool compatibility

The first `gemma3:12b` benchmark attempt showed another observability gap:
- Ollama HTTP status failures surfaced as generic `400 Bad Request` messages
- the benchmark needed the response body to distinguish model incompatibility from server failure

Change made in this iteration:
- `backend/services/ollama_service.py` now appends the Ollama response body to `HTTPStatusError` details when available

Validation and finding:
- `python3 -m py_compile backend/services/ollama_service.py`
- `cd backend && python3 -m benchmarks.run_llm_bench --provider ollama --model gemma3:12b --profile quick --output-dir ../output/benchmarks`

Observed result:
- `gemma3:12b` is installed and works through direct `ollama run`
- the current CEO tool-enabled Ollama chat path is rejected for `gemma3:12b`
- Ollama returned `{"error":"registry.ollama.ai/library/gemma3:12b does not support tools"}`

Why this matters:
- the harness can now classify this as a capability mismatch instead of a vague model failure
- CEO needs a no-tools/raw-chat path before non-tool local models can be benchmarked fairly

## Iteration 7: no-tools Ollama benchmark mode

The `gemma3:12b` compatibility result made the next requirement concrete:
- some Ollama models can answer normal chat prompts but reject tool schemas entirely
- the harness needed a way to compare those models without pretending they are broken

Changes made in this iteration:
- `backend/services/ollama_service.py` now accepts a `tools_enabled` override
- `backend/services/llm_service.py` passes the override through provider creation
- `backend/config.py` now exposes `OLLAMA_TOOLS_ENABLED` for backend runtime configuration
- `backend/benchmarks/run_llm_bench.py` now accepts `--tools false`
- benchmark target JSON files can use either `tools` or `tools_enabled`
- `README.md`, `backend/.env.example`, and `backend/benchmarks/README.md` document the no-tools path

Validation:
- `python3 -m py_compile backend/config.py backend/services/llm_service.py backend/services/ollama_service.py backend/benchmarks/run_llm_bench.py`
- `cd backend && python3 -m benchmarks.run_llm_bench --provider mock --profile quick --tools false --output-dir /tmp/ceo-bench-tools-flag`

First real no-tools run:
- `cd backend && python3 -m benchmarks.run_llm_bench --provider ollama --model gemma3:12b --profile quick --tools false --output-dir ../output/benchmarks`

Observed result:
- `gemma3:12b` scored `0.667` in no-tools mode
- it passed `git_safety_protocol` and `local_model_selection`
- it failed `structured_rollout_json` by returning a verbose fenced JSON-style answer instead of strict JSON

Why this matters:
- CEO can now separately evaluate full tool-capable local models and raw-chat local models
- `gemma3:12b` should not be treated as a full CEO backend yet, but it remains useful for raw local chat testing

## Iteration 8: shortlist defaults after Phi comparison

The first Phi pass completed the initial local shortlist:
- `phi4:14b` rejects Ollama tool schemas
- `phi4:14b` matches Gemma's no-tools score on the quick profile
- `phi4:14b` is faster than Gemma in no-tools mode on this machine
- `qwen2.5-coder:14b` remains the only tested local model that completed the tool-enabled quick profile successfully

Changes made after that result:
- default Ollama model examples now use `qwen2.5-coder:14b`
- `backend/benchmarks/targets.research-shortlist.example.json` now treats `qwen2.5-coder:14b` as the tool-enabled baseline
- the same target file marks both `phi4:14b` and `gemma3:12b` as no-tools benchmark targets

Why this matters:
- the default local path should optimize for a working CEO assistant before optimizing for raw model preference
- raw-chat models remain useful, but they need explicit no-tools routing until CEO has capability-aware provider selection

## Iteration 9: automatic Ollama tool capability routing

After both `gemma3:12b` and `phi4:14b` rejected tool schemas, manual `--tools false` was no longer enough.

Changes made in this iteration:
- `OLLAMA_TOOLS_ENABLED` now defaults to `auto`
- `OllamaService` automatically disables tool schemas for known raw-chat-only Ollama model families
- the first no-tool families are `gemma3:*` and `phi4:*`
- benchmarks can still force `--tools true` when intentionally probing compatibility

Validation:
- `python3 -m py_compile backend/config.py backend/services/llm_service.py backend/services/ollama_service.py backend/benchmarks/run_llm_bench.py`
- `cd backend && python3 -m benchmarks.run_llm_bench --provider mock --profile quick --tools true --output-dir /tmp/ceo-bench-tools-true`
- `cd backend && python3 -m benchmarks.run_llm_bench --provider ollama --model phi4:14b --case local_model_selection --output-dir /tmp/ceo-phi-auto-route-check`

Observed validation result:
- `phi4:14b` ran without passing `--tools false`
- the run avoided the previous Ollama `400 Bad Request` tool-schema error
- the `local_model_selection` case scored `1.0`

Why this matters:
- selecting `phi4:14b` or `gemma3:12b` no longer fails immediately just because the global tool setting was left enabled
- `qwen2.5-coder:14b` still keeps tools enabled by default
- future model discoveries can be added to one capability list instead of scattered through benchmark commands

## Iteration 10: health visibility and dynamic tool fallback

The next operational gap was runtime visibility.
It was not enough for the provider to choose a tool mode internally; `/health` also needed to expose the resolved mode so a running backend can be checked quickly.

Changes made in this iteration:
- `LLMService` now exposes provider-specific health details
- `/health` now includes Ollama tool routing details when the active provider is Ollama
- `OllamaService` telemetry now records `tools_enabled` and `tool_fallback`
- unknown auto-enabled Ollama models that reject tools with `does not support tools` retry once without tools
- explicit forced tool probes still surface the error instead of silently falling back

Validation:
- `python3 -m py_compile backend/main.py backend/config.py backend/services/llm_provider.py backend/services/llm_service.py backend/services/ollama_service.py backend/benchmarks/run_llm_bench.py`
- fake Ollama client test: first request rejected tools, second request retried without tools and returned `fallback ok`
- provider health check showed `qwen2.5-coder:14b` as `auto-enabled` and `phi4:14b`/`gemma3:12b` as `auto-disabled`
- FastAPI `/health` route test showed `qwen2.5-coder:14b` as `auto-enabled`
- FastAPI `/health` route test showed `phi4:14b` as `auto-disabled`
- WebSocket text-flow smoke test with TTS stubbed returned `WS smoke ok` through real `qwen2.5-coder:14b` Ollama inference

Why this matters:
- backend health checks now reveal whether CEO is running full tool-capable mode or raw-chat mode
- new model families can fail softer in app usage while still being diagnosable in benchmark probes
- telemetry now preserves whether a response came from tool-enabled mode or fallback raw-chat mode

## Iteration 11: stricter structured-output benchmark prompt

The Phi and Gemma no-tools benchmark runs both failed `structured_rollout_json` in the same way:
- the models returned JSON-like content inside markdown fences
- the benchmark requires strict JSON that can be parsed directly with `json.loads`

Change made in this iteration:
- the structured-output benchmark case now explicitly says not to use markdown fences
- it also states that the first character must be `{` and the last character must be `}`
- JSON evaluation now records whether an otherwise strict-failed response is repairable by removing a markdown fence or extracting the outer JSON object

Validation:
- `python3 -m py_compile backend/benchmarks/cases.py`
- `cd backend && python3 -m benchmarks.run_llm_bench --provider mock --case structured_rollout_json --output-dir /tmp/ceo-structured-repair-check`
- `cd backend && python3 -m benchmarks.run_llm_bench --provider ollama --model qwen2.5-coder:14b --case structured_rollout_json --output-dir /tmp/ceo-qwen-structured-strict-check`
- `cd backend && python3 -m benchmarks.run_llm_bench --provider ollama --model phi4:14b --case structured_rollout_json --output-dir /tmp/ceo-phi-structured-strict-check`

Observed validation result:
- `qwen2.5-coder:14b` still scored `1.0` on strict JSON after the prompt change
- `phi4:14b` still scored `0.0` because it returned fenced JSON
- Phi's fenced JSON was repairable after stripping the markdown fence, which confirms the remaining problem is output wrapping rather than missing required keys

Why this matters:
- future structured-output runs should separate model JSON weakness from ambiguity in the prompt
- the benchmark still scores strict parseability instead of forgiving fenced JSON
