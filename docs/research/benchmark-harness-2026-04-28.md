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
