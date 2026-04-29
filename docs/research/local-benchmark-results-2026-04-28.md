# CEO local benchmark results

Date: 2026-04-28
Status: first four-model quick-profile comparison captured; Phi selected as first raw-chat fallback

## Scope of this pass

This pass started with the only model that was already installed locally:
- `qwen2.5-coder:14b`

It now also includes comparison runs against:
- `qwen3:8b`
- `gemma3:12b`
- `phi4:14b`

The broader target comparison set is:
- `qwen3:8b`
- `gemma3:12b`
- `phi4:14b`

At the time of this note:
- `qwen3:8b` has now been benchmarked
- `gemma3:12b` has now been installed and benchmarked through both the tool-enabled and no-tools Ollama paths
- `phi4:14b` has now been installed and benchmarked through both the tool-enabled and no-tools Ollama paths

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

## gemma3:12b tool-enabled compatibility run

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

## gemma3:12b no-tools raw-chat quick-profile run

After the compatibility failure above, the Ollama provider and benchmark harness were updated to support disabling tool schemas.

Command used:

```bash
cd backend
python3 -m benchmarks.run_llm_bench \
  --provider ollama \
  --model gemma3:12b \
  --profile quick \
  --tools false \
  --output-dir ../output/benchmarks
```

Artifacts:

- `output/benchmarks/20260428T215654+0000_ollama-gemma3-12b-tools-false.json`
- `output/benchmarks/20260428T215654+0000_ollama-gemma3-12b-tools-false.md`

Aggregate result:
- average score: `0.667`
- average latency: `61112.6 ms`

Case breakdown:
- `git_safety_protocol`: score `1.0`, latency `32406.0 ms`
- `structured_rollout_json`: score `0.0`, latency `119123.2 ms`
- `local_model_selection`: score `1.0`, latency `31808.7 ms`

Telemetry observations:
- all three cases completed in a single raw-chat round with `tool_call_count=0`
- the structured JSON case generated `1004` eval tokens and took about `119s`
- the two passing cases were much faster, around `32s` each

What Gemma did well in no-tools mode:
- correctly described the required git safety protocol and named `get_git_status_and_diff()`
- gave a clear local-model selection answer with a `Default first pick:` line
- ran successfully without the Ollama tool-schema rejection

What Gemma did poorly in no-tools mode:
- failed the strict JSON benchmark by returning a fenced, verbose JSON-style response instead of compact strict JSON
- was much slower than `qwen2.5-coder:14b` on the comparable quick profile
- cannot call CEO tools in this mode, so it is a raw-chat fallback candidate rather than a full assistant backend

## phi4:14b installation and disk note

`phi4:14b` was not installed at the start of this pass.
The first pull failed because the machine had only about `325 MB` free on `/System/Volumes/Data`.

To make room:
- removed local `qwen3:8b`
- removed local `gemma3:12b`
- kept local `qwen2.5-coder:14b`, because it is still the best full tool-enabled local baseline

After cleanup:
- free disk increased to about `13 GB`
- `phi4:14b` pulled successfully
- `ollama list` showed `phi4:14b` and `qwen2.5-coder:14b` installed

The removed models are still represented by saved benchmark artifacts and can be pulled again later.

## phi4:14b tool-enabled compatibility run

Command used:

```bash
cd backend
python3 -m benchmarks.run_llm_bench \
  --provider ollama \
  --model phi4:14b \
  --profile quick \
  --output-dir ../output/benchmarks
```

Artifacts:

- `output/benchmarks/20260429T034755+0000_ollama-phi4-14b.json`
- `output/benchmarks/20260429T034755+0000_ollama-phi4-14b.md`

Aggregate result:
- average score: `0.167`
- average latency: `71.6 ms`

Observed Ollama error:

```text
{"error":"registry.ollama.ai/library/phi4:14b does not support tools"}
```

Interpretation:
- `phi4:14b` has the same tool-schema limitation as `gemma3:12b`
- it cannot be used as a full CEO local backend unless tools are disabled or routed elsewhere
- the non-zero score is a heuristic artifact from the error text, not real model quality

## phi4:14b no-tools raw-chat quick-profile run

Command used:

```bash
cd backend
python3 -m benchmarks.run_llm_bench \
  --provider ollama \
  --model phi4:14b \
  --profile quick \
  --tools false \
  --output-dir ../output/benchmarks
```

Artifacts:

- `output/benchmarks/20260429T034810+0000_ollama-phi4-14b-tools-false.json`
- `output/benchmarks/20260429T034810+0000_ollama-phi4-14b-tools-false.md`

Aggregate result:
- average score: `0.667`
- average latency: `43411.0 ms`

Case breakdown:
- `git_safety_protocol`: score `1.0`, latency `47457.4 ms`
- `structured_rollout_json`: score `0.0`, latency `51989.5 ms`
- `local_model_selection`: score `1.0`, latency `30786.2 ms`

Telemetry observations:
- all three cases completed in a single raw-chat round with `tool_call_count=0`
- the structured JSON case generated `411` eval tokens and took about `52s`
- `phi4:14b` was faster than `gemma3:12b` in no-tools mode on the same quick profile

What Phi did well in no-tools mode:
- followed the git safety protocol and named `get_git_status_and_diff()`
- produced a clear `Default first pick:` answer for local model selection
- matched Gemma's no-tools score while running faster overall

What Phi did poorly in no-tools mode:
- failed strict JSON output by returning fenced, verbose, partially off-target JSON-style content
- cannot call CEO tools in this mode
- is still much slower than `qwen2.5-coder:14b` on the comparable quick profile

Current local-provider ranking from this pass:
- `qwen2.5-coder:14b` is still the best current full-CEO local default candidate because it handles the tool-enabled path and is much faster than the alternatives tested so far
- `phi4:14b` is the best current no-tools/raw-chat candidate because it matches Gemma's score and is faster on this quick profile
- `gemma3:12b` remains a viable no-tools/raw-chat candidate, but Phi is the better first raw-chat fallback so far
- `qwen3:8b` is not a good first default on this machine/config because it matched `qwen2.5-coder:14b` on score but was much slower and timed out on one quick-profile case

## Immediate next action

1. Treat `qwen2.5-coder:14b` as the current Ollama default for full CEO tool-enabled testing.
2. Treat `phi4:14b` as the current first no-tools/raw-chat fallback.
3. Test real voice/TTS dependencies after installing the full backend requirements.
4. Test the mobile app against the LAN WebSocket URL.
5. Add more raw-chat-only families to the automatic Ollama capability map as they are discovered.
6. Decide whether CEO should add JSON fence-stripping for structured-output workflows.
