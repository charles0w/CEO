# CEO — Personal AI Assistant

CEO is a Jarvis-style personal AI assistant that runs locally on your Desktop. Talk to it via voice or text from your phone or browser. The backend can use either Gemini or a local Ollama model.

---

## Prerequisites

- **Python 3.10+** — for the backend
- **Node.js 18+** — for the mobile/web app
- **ffmpeg** — required by the voice transcription engine

```bash
# Windows
winget install ffmpeg

# macOS
brew install ffmpeg
```

- **Gemini API key** — required only when `LLM_PROVIDER=gemini`
- **Ollama** — required only when `LLM_PROVIDER=ollama`

---

## Setup

### 1. Backend

```bash
cd backend
# Windows: copy .env.example .env
# macOS/Linux: cp .env.example .env
# Edit .env and choose a provider:
# - Gemini: set LLM_PROVIDER=gemini and fill in GEMINI_API_KEY
# - Ollama: set LLM_PROVIDER=ollama and make sure Ollama is running locally
```

Then start the server.

```batch
start.bat
```

On macOS/Linux:

```bash
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

This creates a virtual environment, installs dependencies, and starts the server at `http://0.0.0.0:8000`.

> **First run:** Whisper downloads the `base` STT model (~145 MB) automatically.
>
> **If using Ollama:** pull a model first, for example `ollama pull qwen2.5-coder:14b`.

### 2. Mobile / Web App

```bash
cd mobile
npm install --legacy-peer-deps
npx expo start          # scan QR code with Expo Go on your phone
npx expo start --web    # open in browser at http://localhost:8081
```

### 3. Connect the App to the Backend

In the app, tap the **settings icon** (top right) and set the server URL:

| Where you are | URL format |
|---|---|
| Same network (home/office) | `ws://<desktop-ip>:8000/ws` |
| Remote (outside network) | `wss://xxxx.ngrok-free.app/ws` |

To find your Desktop IP:
- Windows: run `ipconfig` and look for **IPv4 Address** under your WiFi adapter.
- macOS: run `ipconfig getifaddr en0`.

For remote access: install [ngrok](https://ngrok.com) and run `ngrok http 8000` on your Desktop.

---

## Features

- **Voice conversation** — hold the mic button, speak, release to send
- **Text chat** — type commands directly
- **Obsidian vault** — read, write, and search your notes at `obi-secondbrain`
- **GitHub** — list repos, view issues, read file contents (set `GITHUB_TOKEN` in `.env`)
- **Claude Code** — CEO can invoke Claude Code CLI on your behalf for dev tasks
- **Git safety gate** — CEO always shows a diff and asks for confirmation before any commit or push

---

## Configuration (`backend/.env`)

```env
LLM_PROVIDER=gemini                  # gemini | ollama
GEMINI_API_KEY=your_key_here         # required only for Gemini
GEMINI_MODEL=gemini-2.0-flash
OLLAMA_BASE_URL=http://localhost:11434/api
OLLAMA_MODEL=qwen2.5-coder:14b
OLLAMA_THINK=
OLLAMA_TOOLS_ENABLED=auto
GITHUB_TOKEN=                          # optional — for GitHub integration
OBSIDIAN_VAULT_PATH=C:/Users/charl/Desktop/obi-secondbrain
WHISPER_MODEL=base                     # tiny | base | small
TTS_VOICE=en-US-GuyNeural
TTS_TIMEOUT_SECONDS=30
```

## Benchmarking local models

The repo includes a benchmark harness for comparing local and hosted model variants with the same CEO-oriented case set.

Single-target example:

```bash
cd backend
python -m benchmarks.run_llm_bench --provider ollama --model qwen3:8b
```

Config-variant example:

```bash
cd backend
python -m benchmarks.run_llm_bench --provider ollama --model qwen2.5-coder:14b --profile quick --timeout 180 --think false
```

No-tools example for Ollama models that reject tool schemas:

```bash
cd backend
python -m benchmarks.run_llm_bench --provider ollama --model gemma3:12b --profile quick --tools false
```

Multi-target example:

```bash
cd backend
python -m benchmarks.run_llm_bench --targets-file benchmarks/targets.research-shortlist.example.json
```

Results are written under `output/benchmarks/`. See `backend/benchmarks/README.md` for details.

When the backend is running, `/health` now reports both `llm_provider` and `llm_model`, and the server logs per-request LLM telemetry for latency and response size.
For Ollama, `/health` also reports the resolved tool mode, including `ollama_tools_enabled`, `ollama_tools_mode`, and whether a tool fallback has been triggered.

---

## Validation

Use the stable non-iCloud checkout for validation:

```bash
cd /Users/newuser/dev/CEO
./scripts/validate.sh
```

The script runs backend Python compile checks, the structured-output parser smoke test, production npm audit, mobile TypeScript, Expo dependency/config checks, Expo Doctor, and a web export. The mobile app is on Expo SDK 54 (`expo@54.x`), React 19.1, and React Native 0.81; Expo Doctor is expected to pass cleanly.

---

## Architecture

```
CEO/
├── backend/
│   ├── main.py                    # FastAPI — WebSocket /ws
│   ├── config.py                  # Settings from .env
│   └── services/
│       ├── llm_service.py         # Provider selection
│       ├── llm_provider.py        # Provider interface
│       ├── llm_tools.py           # Shared system prompt + tool registry
│       ├── gemini_service.py      # Gemini backend
│       ├── ollama_service.py      # Ollama backend + tool loop
│       ├── structured_output.py   # JSON object extraction/repair helper
│       ├── voice_service.py       # faster-whisper (STT) + edge-tts (TTS)
│       ├── obsidian_service.py    # Obsidian vault read/write/search
│       ├── github_service.py      # GitHub API via PyGithub
│       └── claude_code_service.py # Claude Code CLI + git operations
└── mobile/
    ├── App.tsx
    └── src/
        ├── screens/ChatScreen.tsx
        ├── screens/SettingsScreen.tsx
        ├── components/            # MessageBubble, VoiceButton
        └── hooks/useWebSocket.ts  # Auto-reconnecting WebSocket
```
