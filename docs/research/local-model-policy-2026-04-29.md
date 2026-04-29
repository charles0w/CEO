# CEO local model policy

Date: 2026-04-29
Status: current operating policy after first Ollama shortlist benchmark

## Current policy

Use `qwen2.5-coder:14b` as the default local Ollama model for full CEO testing.

Why:
- it is the only tested local model that completed the tool-enabled quick profile successfully
- it is much faster than `qwen3:8b`, `gemma3:12b`, and `phi4:14b` on comparable quick-profile runs
- it can use CEO's tool schema, which is required for Obsidian, GitHub, Codex/Claude-code delegation, and git operations

Use `phi4:14b` as the first raw-chat fallback.

Why:
- it matched Gemma's no-tools quick-profile score
- it was faster than Gemma in no-tools mode
- it is installed locally now

Do not use `qwen3:8b` as the first default on this machine.

Why:
- it matched `qwen2.5-coder:14b` on score but was dramatically slower
- it timed out on the local model selection case

Treat `gemma3:12b` as optional for later raw-chat retesting.

Why:
- it can answer direct Ollama prompts
- it rejects Ollama tool schemas
- it was slower than Phi in no-tools mode
- it is not currently installed locally after disk cleanup

## Current installed local models

As of the last check:
- `qwen2.5-coder:14b`
- `phi4:14b`

Removed during disk cleanup:
- `qwen3:8b`
- `gemma3:12b`

The removed models can be pulled again later. Their benchmark artifacts remain in `output/benchmarks/`.

## Runtime configuration

Recommended backend `.env` for local Ollama testing:

```env
LLM_PROVIDER=ollama
OLLAMA_MODEL=qwen2.5-coder:14b
OLLAMA_TOOLS_ENABLED=auto
```

`OLLAMA_TOOLS_ENABLED=auto` means:
- known tool-capable models, such as `qwen2.5-coder:14b`, send the Ollama tool schema
- known raw-chat-only model families, currently `phi4:*` and `gemma3:*`, skip the tool schema
- if an unknown auto-enabled model rejects tools with `does not support tools`, CEO retries once without tools and records the fallback in telemetry

## Benchmark references

Tool-enabled baseline:
- `output/benchmarks/20260428T123825+0000_ollama-qwen2.md`
- average score: `0.667`
- average latency: `16703.0 ms`

Phi no-tools fallback:
- `output/benchmarks/20260429T034810+0000_ollama-phi4-14b-tools-false.md`
- average score: `0.667`
- average latency: `43411.0 ms`

Gemma no-tools comparison:
- `output/benchmarks/20260428T215654+0000_ollama-gemma3-12b-tools-false.md`
- average score: `0.667`
- average latency: `61112.6 ms`

qwen3 comparison:
- `output/benchmarks/20260428T161736+0000_ollama-qwen3-8b.md`
- average score: `0.667`
- average latency: `80462.8 ms`

## Next evaluation steps

Completed:
- smoke tested `qwen2.5-coder:14b` through the WebSocket text path with real Ollama inference and TTS stubbed
- confirmed `/health` reports `qwen2.5-coder:14b` as `auto-enabled`
- confirmed `/health` reports `phi4:14b` as `auto-disabled`
- re-ran the structured-output case after the stricter JSON prompt change
- added a shared structured-output repair helper for fenced or prose-wrapped JSON objects
- installed the full backend runtime in a Python 3.11 virtual environment after the Python 3.13 environment hit a NumPy/faster-whisper import issue
- installed `ffmpeg` with Homebrew and confirmed it is available for faster-whisper
- validated real Edge TTS synthesis and a faster-whisper transcription round trip
- installed mobile dependencies with `npm install --legacy-peer-deps`
- fixed the mobile TypeScript issue caused by an invalid `TextInput` `color` prop
- validated the LAN `/health` and WebSocket path at `ws://10.0.16.70:8000/ws`
- added a configurable `TTS_TIMEOUT_SECONDS` guard so Edge TTS cannot hang a backend response indefinitely
- repaired the macOS Desktop/iCloud dataless checkout issue and documented the recovery path
- reinstalled mobile dependencies cleanly with `npm ci --legacy-peer-deps --no-audit`
- confirmed full `npx tsc --noEmit --pretty false` now passes
- fixed Expo Doctor actionable findings by adding a real app icon, adding `expo-font`, and aligning SDK 52 package versions
- reduced `npm audit --omit=dev --audit-level=moderate` from 17 findings to 0 with targeted npm overrides

Remaining:
1. Run the physical-device Expo Go test from Charles's phone on the same network.
2. Add more raw-chat-only families to the automatic capability map when discovered.
3. Use the structured-output repair helper in future app workflows that need machine-readable JSON.
4. Decide whether to keep `expo-av` for the current Expo SDK 52 app or schedule a larger migration to `expo-audio`.
