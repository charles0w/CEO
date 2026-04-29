# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What CEO Is

CEO is Charles's personal AI assistant ("Jarvis but called CEO"). It runs a Python/FastAPI server on the Desktop and a React Native (Expo) mobile app. The runtime LLM provider is configurable: Gemini 2.0 Flash is the hosted path, and Ollama is the local-first path. Current local default: `qwen2.5-coder:14b` with `OLLAMA_TOOLS_ENABLED=auto`. Claude tokens are reserved for development via Claude Code CLI, not as the app's runtime brain.

## Running the Backend

Windows:

```batch
cd backend
start.bat          # creates venv, installs deps, starts server
# or manually:
.venv\Scripts\uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

macOS/Linux:

```bash
cd backend
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Server runs on `http://0.0.0.0:8000`. WebSocket endpoint: `ws://localhost:8000/ws` locally, or `ws://<desktop-lan-ip>:8000/ws` from the mobile app.

First run: Whisper downloads the `base` model (~145 MB) from HuggingFace automatically.

Prerequisite: `ffmpeg` must be installed and in PATH (required by faster-whisper). Use `winget install ffmpeg` on Windows or `brew install ffmpeg` on macOS.

## Running the Mobile App

```bash
cd mobile
npm install --legacy-peer-deps
npx expo start          # scan QR code with Expo Go app
npx expo start --android
npx expo start --ios
```

In the app's Settings screen, set the server URL to `ws://<desktop-lan-ip>:8000/ws`.

For remote access outside the home network: run `ngrok http 8000` on the Desktop and use the `wss://` URL from ngrok.

## Validation

Prefer the stable non-iCloud checkout at `/Users/newuser/dev/CEO` for Git, npm, and validation work. The Desktop checkout can be converted into macOS `compressed,dataless` placeholders by iCloud.

```bash
cd /Users/newuser/dev/CEO
./scripts/validate.sh
```

`scripts/validate.sh` runs backend compile checks, structured-output parser smoke tests, mobile production audit, TypeScript, Expo dependency/config checks, Expo Doctor, and web export. The current accepted Expo Doctor warning is `expo-av` being marked unmaintained; treat migration to `expo-audio` as a deliberate larger change.

## Architecture

```text
CEO/
├── backend/
│   ├── main.py                    # FastAPI app - WebSocket /ws, REST /health /transcribe /speak
│   ├── config.py                  # Pydantic settings from .env
│   ├── benchmarks/                # Local/hosted LLM benchmark harness
│   ├── services/
│   │   ├── llm_service.py         # Provider selection and health details
│   │   ├── llm_provider.py        # Shared provider interface + telemetry
│   │   ├── llm_tools.py           # Shared system prompt and tool registry
│   │   ├── gemini_service.py      # Gemini 2.0 Flash + Automatic Function Calling (AFC)
│   │   ├── ollama_service.py      # Ollama chat + tool loop + auto tool capability routing
│   │   ├── structured_output.py   # Shared JSON object extraction/repair helper
│   │   ├── voice_service.py       # faster-whisper (STT) + edge-tts (TTS)
│   │   ├── obsidian_service.py    # Read/write C:/Users/charl/Desktop/obi-secondbrain
│   │   ├── github_service.py      # PyGithub - repos, issues, file content
│   │   └── claude_code_service.py # Subprocess calls to `claude --print` + git safety gate
│   └── .env                       # API keys - gitignored, never commit
└── mobile/
    ├── App.tsx                    # Root - screen state (chat | settings)
    └── src/
        ├── screens/ChatScreen.tsx     # Main UI: messages, voice button, text input
        ├── screens/SettingsScreen.tsx # Configure server URL (persisted in AsyncStorage)
        ├── components/MessageBubble.tsx
        ├── components/VoiceButton.tsx # Hold-to-record with pulse animation
        └── hooks/useWebSocket.ts      # WebSocket with auto-reconnect
```

## WebSocket Message Protocol

Client -> Server:

```json
{ "type": "text", "content": "your message" }
{ "type": "voice", "audio": "<base64 m4a>" }
{ "type": "reset" }
```

Server -> Client:

```json
{ "type": "transcription", "text": "..." }
{ "type": "response", "text": "...", "audio": "<base64 mp3 or null>" }
```

## LLM Providers And Tools

`gemini_service.py` uses Gemini Automatic Function Calling: Python functions are passed directly as tools.

`ollama_service.py` uses OpenAI-style tool schemas against Ollama chat. `OLLAMA_TOOLS_ENABLED=auto` sends tools for known tool-capable models such as `qwen2.5-coder:14b`, skips tools for known raw-chat-only families such as `phi4:*` and `gemma3:*`, and retries once without tools if an unknown auto-enabled model rejects tool schemas.

The shared tools are: `list_obsidian_notes`, `read_obsidian_note`, `write_obsidian_note`, `search_obsidian_vault`, `list_github_repos`, `get_github_repo_info`, `list_github_issues`, `get_github_file`, `run_claude_code`, `get_git_status_and_diff`, `git_commit`, `git_push`.

## Git Safety Protocol

CEO's system prompt enforces: always call `get_git_status_and_diff()` first, present a summary to Charles, get explicit confirmation, then call `git_commit()` or `git_push()`. Never skip this.

## Key Config

| Variable | Default | Purpose |
|---|---|---|
| `LLM_PROVIDER` | `gemini` | Runtime provider: `gemini` or `ollama` |
| `GEMINI_API_KEY` | - | Required when `LLM_PROVIDER=gemini` |
| `GEMINI_MODEL` | `gemini-2.0-flash` | Gemini runtime model |
| `OLLAMA_BASE_URL` | `http://localhost:11434/api` | Ollama API base URL |
| `OLLAMA_MODEL` | `qwen2.5-coder:14b` | Recommended local full-tool model |
| `OLLAMA_TOOLS_ENABLED` | `auto` | Tool routing: `auto`, `true`, or `false` |
| `GITHUB_TOKEN` | empty | GitHub API access |
| `OBSIDIAN_VAULT_PATH` | `C:/Users/charl/Desktop/obi-secondbrain` | Vault location |
| `WHISPER_MODEL` | `base` | STT model size (tiny/base/small) |
| `TTS_VOICE` | `en-US-GuyNeural` | edge-tts voice |
| `TTS_TIMEOUT_SECONDS` | `30` | TTS network timeout guard |
