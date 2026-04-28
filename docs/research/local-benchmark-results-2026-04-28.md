# CEO local benchmark results

Date: 2026-04-28
Status: first real Ollama baseline captured

## Scope of this pass

This pass used the new benchmark harness against the only model that was already installed locally at the time:
- `qwen2.5-coder:14b`

The target comparison set remains:
- `qwen3:8b`
- `gemma3:12b`
- `phi4:14b`

Those models were not yet benchmarked in this pass because they were not already present locally and the first pull was too slow to complete before the initial baseline loop finished.

## Command used

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

## Result artifacts

- `output/benchmarks/20260428T123825+0000_ollama-qwen2.json`
- `output/benchmarks/20260428T123825+0000_ollama-qwen2.md`

## Summary

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

## Immediate next action

1. Finish pulling `qwen3:8b`.
2. Run the same 3-case subset against `qwen3:8b`.
3. If `qwen3:8b` clearly beats this baseline on both latency and behavior, use it as the provisional first local default for CEO testing.
4. Continue with `gemma3:12b` and `phi4:14b` after that.
