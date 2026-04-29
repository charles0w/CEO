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

## Iteration 12: shared structured-output repair helper

After Phi repeatedly returned valid JSON inside markdown fences, CEO needed a reusable repair path for future structured-output workflows.

Changes made in this iteration:
- added `backend/services/structured_output.py`
- added `extract_json_object_text()` for markdown-fenced or prose-wrapped JSON object extraction
- added `parse_json_object()` for strict parse first, optional repaired parse second, and required-key validation
- benchmark JSON diagnostics now use the shared helper for `repairable` detection while keeping strict scoring unchanged

Why this matters:
- app workflows can choose to accept repairable JSON without weakening the benchmark's strict score
- future structured-output code has one shared parser instead of ad hoc fence stripping

## Iteration 13: full runtime, mobile, and repo-health validation

After disk space was freed, the next practical step was to validate the real runtime path instead of only benchmark stubs.

Work completed in this iteration:
- refreshed Git metadata and rehydrated tracked macOS `dataless` placeholders from `HEAD` so status, diffs, and tests could read the repo normally
- installed full backend requirements into a Python 3.11 virtual environment after the previous Python 3.13 environment hit a NumPy/faster-whisper import problem
- installed `ffmpeg` with Homebrew for faster-whisper audio decoding
- validated Edge TTS synthesis with real network-backed `edge-tts`
- validated a full voice round trip: Edge TTS generated audio and faster-whisper transcribed it back successfully
- installed mobile dependencies with `npm install --legacy-peer-deps`
- ran `npx tsc --noEmit`, found an invalid React Native `TextInput` `color` prop, removed it, and confirmed TypeScript passes
- started the FastAPI backend on `0.0.0.0:8000` using `LLM_PROVIDER=ollama`, `OLLAMA_MODEL=qwen2.5-coder:14b`, and `OLLAMA_TOOLS_ENABLED=auto`
- validated LAN `/health` at `http://10.0.16.70:8000/health`
- validated the mobile WebSocket path programmatically at `ws://10.0.16.70:8000/ws`, including greeting, model response, and returned TTS audio
- updated app and README IP instructions to include both Windows and macOS
- updated `AGENTS.md` and `CLAUDE.md` so future coding-agent sessions see the provider-selectable Gemini/Ollama architecture and current local-first defaults
- added `TTS_TIMEOUT_SECONDS` so external Edge TTS calls cannot hang a backend response indefinitely

Observed validation results:
- `/health` reported `llm_provider=ollama`, `llm_model=qwen2.5-coder:14b`, and `ollama_tools_mode=auto-enabled`
- LAN WebSocket smoke returned `LAN mobile smoke ok` through the backend and produced response audio
- voice smoke returned the transcription `CEO Voice Smoke Test`
- mobile TypeScript now passes after removing the invalid prop
- after the later Settings screen IP-instruction edit, full project `tsc` reruns stalled under 60s/120s guards with no diagnostic output; direct TypeScript transpile checks for the touched `ChatScreen.tsx` and `SettingsScreen.tsx` files passed
- `npm audit --omit=dev` reported 17 vulnerabilities: 5 moderate and 12 high. The main affected transitive packages are `@xmldom/xmldom`, `postcss`, `tar`, and `uuid` through Expo CLI/config dependencies. No automatic fix was applied because npm proposes `npm audit fix --force`, which would install `expo@49.0.23` as a breaking change from the current Expo 52 stack

Remaining practical validation:
- run the same URL from the physical Expo Go app on Charles's phone while it is on the same network
- rerun full `npx tsc --noEmit` after the local Node/npm stall is resolved
- plan an Expo dependency upgrade/remediation pass before production distribution

## Iteration 14: mobile dependency health and iCloud checkout repair

The next practical blocker was the mobile validation stall and Expo dependency health.

Work completed in this iteration:
- diagnosed the full `npx tsc --noEmit` stall as a macOS Desktop/iCloud `compressed,dataless` placeholder problem affecting both tracked repo files and `mobile/node_modules`
- repaired the local checkout by cloning a fresh copy of `charles0w/CEO` to `/tmp/CEO-fresh`, restoring the Desktop checkout to the already-pushed `cbda28d` state, and then materializing tracked files by writing their bytes from the fresh clone
- removed and reinstalled `mobile/node_modules` with `npm ci --legacy-peer-deps --no-audit`
- confirmed full mobile TypeScript now completes with `npx tsc --noEmit --pretty false`
- ran `npx expo-doctor` and fixed the actionable SDK/config findings
- added `mobile/assets/icon.png` so `app.json` points at a real icon asset
- installed the SDK-compatible direct dependency `expo-font`
- aligned `@expo/vector-icons` to `~14.0.4`, the Expo SDK 52 expected version
- aligned `@react-native-async-storage/async-storage` to `1.23.1`, the Expo SDK 52 expected version
- added npm `overrides` for vulnerable transitive packages: `@xmldom/xmldom`, `postcss`, `tar`, and `uuid`

Validation after this iteration:
- `npm audit --omit=dev --audit-level=moderate` reports `found 0 vulnerabilities`
- `npx tsc --noEmit --pretty false` passes
- `npx expo install --check` reports dependencies are up to date
- `npx expo config --json` resolves the app config and icon path
- `npx expo export --platform web --output-dir /tmp/ceo-expo-web-export` succeeds
- `npx expo-doctor` now passes 16/17 checks; the only remaining warning is that `expo-av` is unmaintained according to React Native Directory metadata
- backend `py_compile` still passes after checkout repair

Remaining practical validation:
- run the physical Expo Go test from Charles's phone while it is on the same network
- the SDK/audio-stack decision was superseded by Iteration 16; keep any future audio-stack migration as a roadmap item only if Expo requirements or app behavior make it necessary

## Iteration 15: repeatable validation and reconnect hardening

After the mobile dependency pass, the next practical improvement was to make the validation process repeatable and reduce runtime edge cases in the app itself.

Changes made in this iteration:
- added `scripts/validate.sh` as the repo-level validation entrypoint
- added mobile npm scripts for TypeScript, production audit, Expo Doctor, and web export
- documented the validation workflow in `README.md`, `AGENTS.md`, and `CLAUDE.md`
- simplified backend `ConnectionManager.disconnect()` to use direct list removal instead of a list/set fallback expression
- rewrote the mobile WebSocket hook lifecycle so URL changes and unmounts cancel stale retry timers and ignore stale socket events

Validation:
- `./scripts/validate.sh`

Observed validation result:
- backend Python compile checks passed
- structured-output parser smoke test passed
- `npm audit --omit=dev --audit-level=moderate` reported `found 0 vulnerabilities`
- `npx tsc --noEmit --pretty false` passed
- `npx expo install --check` reported dependencies are up to date
- `npx expo config --json` resolved successfully
- at this point in the history, `npx expo-doctor` still reported only the known `expo-av` maintenance warning; Iteration 16 later removed this expected-warning exception
- `npx expo export --platform web --output-dir /tmp/ceo-expo-web-export` succeeded

## Iteration 16: Expo SDK 54 upgrade

The next practical upgrade was moving the mobile app from Expo SDK 52 to SDK 54 so the app can run on the current Expo Go / React Native stack instead of staying pinned to the older dependency set.

Research references used:
- Expo SDK upgrade guide: https://docs.expo.dev/workflow/upgrading-expo-sdk-walkthrough/
- Expo SDK 54 release notes: https://expo.dev/changelog/sdk-54

Changes made in this iteration:
- upgraded `expo` from the SDK 52 line to the SDK 54 line (`expo@54.x`)
- aligned SDK-managed dependencies with Expo SDK 54, including React 19.1, React Native 0.81.5, React Native Web 0.21, `expo-av` 16, `expo-file-system` 19, `expo-font` 14, `expo-linear-gradient` 15, `expo-status-bar` 3, and `@expo/vector-icons` 15
- ran Expo's recommended dependency repair flow with `npx expo install --fix`; npm hit peer-resolution conflicts, so the lockfile was finalized with `npm install --legacy-peer-deps --no-audit`
- updated `ChatScreen.tsx` to import the current recording base64 read path from `expo-file-system/legacy`, because SDK 54 exposes the new file-system API as the default package entrypoint while the old API remains available under the legacy subpath
- simplified `scripts/validate.sh` so Expo Doctor must now pass cleanly instead of tolerating the old SDK 52 `expo-av` maintenance warning
- updated `README.md`, `AGENTS.md`, and `CLAUDE.md` to describe SDK 54 as the current mobile stack

Validation after this iteration:
- `./scripts/validate.sh` passes end to end
- backend Python compile checks pass
- structured-output parser smoke test passes
- `npm audit --omit=dev --audit-level=moderate` reports `found 0 vulnerabilities`
- `npx tsc --noEmit --pretty false` passes
- `npx expo install --check` reports dependencies are up to date
- `npx expo config --json` resolves successfully
- `npx expo-doctor` reports 17/17 checks passed
- `npx expo export --platform web --output-dir /tmp/ceo-expo-web-export` succeeds

Remaining practical validation:
- run the physical-device Expo Go test from Charles's phone while it is on the same network
- keep the future audio-stack migration as a roadmap item only if Expo requirements or app behavior make it necessary
