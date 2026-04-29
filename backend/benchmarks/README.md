# CEO benchmark harness

This benchmark harness compares CEO LLM providers and model variants using a fixed set of CEO-oriented cases.

## What it measures

- end-to-end latency per case
- response size
- a small heuristic score based on required content or JSON validity
- full raw outputs for later manual review

This is not a substitute for human evaluation. It is a repeatable screening tool for narrowing model candidates.

## Available cases

Run:

```bash
cd backend
python -m benchmarks.run_llm_bench --list-cases
```

## Single-target runs

Ollama example:

```bash
cd backend
python -m benchmarks.run_llm_bench --provider ollama --model qwen2.5-coder:14b
```

Gemini example:

```bash
cd backend
python -m benchmarks.run_llm_bench --provider gemini --model gemini-2.0-flash
```

Mock provider example for harness validation:

```bash
cd backend
python -m benchmarks.run_llm_bench --provider mock
```

## Multi-target runs

Use the example target file as a starting point, then edit the model names to match what is actually available in your local Ollama installation.

```bash
cd backend
python -m benchmarks.run_llm_bench --targets-file benchmarks/targets.research-shortlist.example.json
```

Quick profile example:

```bash
cd backend
python -m benchmarks.run_llm_bench --provider ollama --model qwen2.5-coder:14b --profile quick
```

Runtime override example:

```bash
cd backend
python -m benchmarks.run_llm_bench --provider ollama --model qwen2.5-coder:14b --profile quick --timeout 180 --think false
```

No-tools example for Ollama models that reject tool schemas:

```bash
cd backend
python -m benchmarks.run_llm_bench --provider ollama --model gemma3:12b --profile quick --tools false
```

Tool-compatibility probe for models normally routed as no-tools:

```bash
cd backend
python -m benchmarks.run_llm_bench --provider ollama --model phi4:14b --profile quick --tools true
```

Target-file variant example:

```bash
cd backend
python -m benchmarks.run_llm_bench --targets-file benchmarks/targets.qwen3-variants.example.json --profile quick
```

The `quick` profile runs:
- `git_safety_protocol`
- `structured_rollout_json`
- `local_model_selection`

Use it for first-pass comparison when the full repo-grounded prompt set is too slow.
Use the runtime overrides when you need to compare provider configuration variants without editing `backend/.env`.
By default, `OLLAMA_TOOLS_ENABLED=auto` disables tool schemas for known raw-chat-only Ollama models such as `gemma3:*` and `phi4:*`.
Use `--tools false` to force raw chat, or `--tools true` to intentionally probe tool compatibility.

## Outputs

Results are written under:

```text
output/benchmarks/
```

Each run generates:

- a JSON file with the raw responses and heuristic check results
- provider telemetry in the JSON when the backend exposes it
- a Markdown summary table for quick review

## Recommended workflow

1. Pull the local models you want to compare with Ollama.
2. Run the same benchmark set across all candidates.
3. Review the JSON/Markdown outputs.
4. Add human preference notes before changing the default provider or model.
