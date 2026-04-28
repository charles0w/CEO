# CEO local benchmark results

Date: 2026-04-28
Status: first three-model quick-profile comparison captured; Gemma tool-compatibility issue identified

## Scope of this pass

This pass started with the only model that was already installed locally:
- `qwen2.5-coder:14b`

It now also includes comparison runs against:
- `qwen3:8b`
- `gemma3:12b`

The broader target comparison set is:
- `qwen3:8b`
- `gemma3:12b`
- `phi4:14b`

At the time of this note:
- `qwen3:8b` has now been benchmarked
- `gemma3:12b` has now been installed and benchmarked through the current tool-enabled CEO Ollama path
- `phi4:14b` is still pending

## qwen2.5-coder quick-profile command

```bash
cd backend
python3 -m benchmarks.run_llm_bench \
  --provider ollama \
  --model qwen2.5-coder:14b \
  --case git_safety_protocol \
  --case structured_rollout_json \
  --case local_model_selection \
  --output-dir ../output/benchmarks
```

## qwen2.5-coder quick-profile artifacts

- `output/benchmarks/20260428T123825+0000_ollama-qwen2.json`
- `output/benchmarks/20260428T123825+0000_ollama-qwen2.md`
- `output/benchmarks/20260428T123433+0000_ollama-qwen2.json`
- `output/benchmarks/20260428T123433+0000_ollama-qwen2.md`

## qwen2.5-coder quick-profile summary

Model:
- `qwen2.5-coder:14b`

Aggregate result:
- average score: `0.667`
- average latency: `16703.0 ms`

Case breakdown:
- `git_safety_protocol`: score `1.0`, latency `13065.0 ms`
- `structured_rollout_json`: score `1.0`, latency `25300.5 ms`
- `local_model_selection`: score `0.0`, latency `11743.5 ms`

## What the model did well

1. It followed the git safety workflow correctly.
2. It returned valid JSON for the structured rollout prompt.
3. It was usable through Ollama with no runtime errors in the benchmark harness.

## What the model did poorly

1. It was slow for this narrow case set, especially on the structured JSON case.
2. It failed the local model selection prompt entirely.
3. On the failed case, it responded with what looked like a tool-call-like JSON object instead of answering the requested question.

## Interpretation

This is a meaningful baseline, but not a strong default local CEO candidate yet.

The main takeaways are:
- `qwen2.5-coder:14b` can satisfy instruction-following tasks in some areas.
- It is too slow to treat as an obvious first local default without stronger upside.
- The failure on `local_model_selection` suggests we should compare it against newer general-purpose local models before making any routing decision.

## Earlier full-profile exploratory run

Before switching to the lighter quick-profile loop, an earlier 6-case exploratory run was captured against the same model.

Command used:

```bash
cd backend
python3 -m benchmarks.run_llm_bench \
  --provider ollama \
  --model qwen2.5-coder:14b \
  --output-dir ../output/benchmarks
```

Artifacts:

- `output/benchmarks/20260428T123433+0000_ollama-qwen2.json`
- `output/benchmarks/20260428T123433+0000_ollama-qwen2.md`

Aggregate result:
- average score: `0.458`
- average latency: `36459.7 ms`

Case breakdown:
- `repo_message_flow`: score `0.0`, latency `120086.2 ms`
- `git_safety_protocol`: score `1.0`, latency `25696.5 ms`
- `connection_manager_bug_review`: score `0.0`, latency `6429.1 ms`
- `provider_telemetry_plan`: score `0.75`, latency `21398.4 ms`
- `structured_rollout_json`: score `1.0`, latency `31060.8 ms`
- `local_model_selection`: score `0.0`, latency `14087.0 ms`

Why this run matters:
- it shows the model was not just slow, but also inconsistent across a broader CEO-shaped task mix
- `repo_message_flow` hit an Ollama-side failure after a very long wait and returned `CEO Error: Ollama request failed:`
- `connection_manager_bug_review` and `local_model_selection` both produced tool-call-like JSON instead of answering directly
- this run is the main reason the harness was tightened around the `--profile quick` subset for faster screening

Interpretation of the broader run:
- `qwen2.5-coder:14b` is useful as a compatibility baseline, not a quality target
- it should remain in the comparison set, but it is unlikely to become the default local CEO model unless the newer candidates underperform badly

## qwen3 quick-profile comparison run

Command used:

```bash
cd backend
python3 -m benchmarks.run_llm_bench \
  --provider ollama \
  --model qwen3:8b \
  --profile quick \
  --output-dir ../output/benchmarks
```

Artifacts:

- `output/benchmarks/20260428T161736+0000_ollama-qwen3-8b.json`
- `output/benchmarks/20260428T161736+0000_ollama-qwen3-8b.md`

Aggregate result:
- average score: `0.667`
- average latency: `80462.8 ms`

Case breakdown:
- `git_safety_protocol`: score `1.0`, latency `73716.4 ms`
- `structured_rollout_json`: score `1.0`, latency `47614.6 ms`
- `local_model_selection`: score `0.0`, latency `120057.4 ms`

Telemetry observations:
- both passing cases completed in a single Ollama round with `tool_call_count=0`
- the failing case ran for about `120s`, which matches the configured `OLLAMA_TIMEOUT_SECONDS=120`
- the failure surfaced as `CEO Error: Ollama request failed:` with no additional error string, which means the current error formatting is not descriptive enough for timeout cases

Comparison against `qwen2.5-coder:14b` quick profile:
- average score was identical: `0.667` vs `0.667`
- average latency was dramatically worse: `80462.8 ms` vs `16703.0 ms`
- `qwen3:8b` was slower on every case
- `qwen3:8b` did not improve the failing `local_model_selection` case and instead timed out

Interpretation:
- `qwen3:8b` is not the first local default candidate for this machine and current Ollama configuration
- on this benchmark slice it delivered no quality gain over `qwen2.5-coder:14b` and imposed a much worse latency cost
- after this run, the next useful comparison was `gemma3:12b`, followed by `phi4:14b`

## gemma3:12b quick-profile compatibility run

Setup:
- pulled `gemma3:12b` into Ollama successfully
- `ollama list` reported `gemma3:12b` at about `8.1 GB`
- a direct sanity check with `ollama run gemma3:12b "Reply with exactly: gemma works"` returned `gemma works`

Command used:

```bash
cd backend
python3 -m benchmarks.run_llm_bench \
  --provider ollama \
  --model gemma3:12b \
  --profile quick \
  --output-dir ../output/benchmarks
```

Artifacts:

- `output/benchmarks/20260428T214837+0000_ollama-gemma3-12b.json`
- `output/benchmarks/20260428T214837+0000_ollama-gemma3-12b.md`

Aggregate result:
- average score: `0.167`
- average latency: `166.5 ms`

Case breakdown:
- `git_safety_protocol`: score `0.0`, latency `280.5 ms`
- `structured_rollout_json`: score `0.0`, latency `109.3 ms`
- `local_model_selection`: score `0.5`, latency `109.8 ms`

Important caveat:
- this is not a real model-quality score
- all benchmark responses were the same provider error instead of model answers
- the `0.5` score on `local_model_selection` came from the error text containing the word `gemma`, which satisfied one lexical heuristic

Observed Ollama error:

```text
{"error":"registry.ollama.ai/library/gemma3:12b does not support tools"}
```

Interpretation:
- `gemma3:12b` is installed correctly and can answer direct Ollama prompts
- the current CEO Ollama provider sends the tool schema on every chat request
- Ollama rejects tool-enabled chat requests for `gemma3:12b`
- `gemma3:12b` cannot be evaluated fairly or used as the default CEO provider until CEO has a no-tools/raw-chat mode or provider capability routing

Current local-provider ranking from this pass:
- `qwen2.5-coder:14b` is still the best current usable local default candidate because it handles the tool-enabled CEO path and completes the quick profile
- `qwen3:8b` is not a good first default on this machine/config because it matched `qwen2.5-coder:14b` on score but was much slower and timed out on one quick-profile case
- `gemma3:12b` is promising enough to keep testing, but it is blocked by tool compatibility in the current adapter

## Immediate next action

1. Add a no-tools/raw-chat benchmark path so non-tool Ollama models can be evaluated fairly.
2. Add provider capability routing so CEO does not send tools to models that reject tools.
3. Re-benchmark `gemma3:12b` in no-tools mode to measure raw answer quality.
4. Benchmark `phi4:14b` after that.
