# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## What CEO Is

CEO is Charles's personal AI assistant ("Jarvis but called CEO"). It runs a Python/FastAPI server on the Desktop and a React Native (Expo) mobile app. The LLM brain is **Gemini 2.0 Flash** (not Codex — Codex tokens are reserved for development via Codex CLI).

## Running the Backend

```batch
cd backend
start.bat          # Windows: creates venv, installs deps, starts server
# or manually:
.venv\Scripts\uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Server runs on `http://0.0.0.0:8000`. WebSocket endpoint: `ws://localhost:8000/ws`.

**First run:** Whisper downloads the `base` model (~145 MB) from HuggingFace automatically.

**Prerequisite:** `ffmpeg` must be installed and in PATH (required by faster-whisper). Install via `winget install ffmpeg`.

## Running the Mobile App

```bash
cd mobile
npm install
npx expo start          # scan QR code with Expo Go app
npx expo start --android
npx expo start --ios
```

In the app's Settings screen, set the server URL to `ws://<desktop-lan-ip>:8000/ws`.

For remote access (outside home network): run `ngrok http 8000` on the Desktop and use the `wss://` URL from ngrok.

## Architecture

```
CEO/
├── backend/
│   ├── main.py                    # FastAPI app — WebSocket /ws, REST /health /transcribe /speak
│   ├── config.py                  # Pydantic settings from .env
│   ├── services/
│   │   ├── gemini_service.py      # Gemini 2.0 Flash + Automatic Function Calling (AFC)
│   │   ├── voice_service.py       # faster-whisper (STT) + edge-tts (TTS)
│   │   ├── obsidian_service.py    # Read/write C:/Users/charl/Desktop/obi-secondbrain
│   │   ├── github_service.py      # PyGithub — repos, issues, file content
│   │   └── claude_code_service.py # Subprocess calls to `Codex --print` + git safety gate
│   └── .env                       # API keys — gitignored, never commit
└── mobile/
    ├── App.tsx                    # Root — screen state (chat | settings)
    └── src/
        ├── screens/ChatScreen.tsx     # Main UI: messages, voice button, text input
        ├── screens/SettingsScreen.tsx # Configure server URL (persisted in AsyncStorage)
        ├── components/MessageBubble.tsx
        ├── components/VoiceButton.tsx # Hold-to-record with pulse animation
        └── hooks/useWebSocket.ts      # WebSocket with auto-reconnect
```

## WebSocket Message Protocol

Client → Server:
```json
{ "type": "text", "content": "your message" }
{ "type": "voice", "audio": "<base64 m4a>" }
{ "type": "reset" }
```

Server → Client:
```json
{ "type": "transcription", "text": "..." }
{ "type": "response", "text": "...", "audio": "<base64 mp3 or null>" }
```

## Gemini Function Calling (AFC)

`gemini_service.py` uses Automatic Function Calling — Python functions are passed directly as tools. Gemini calls them automatically mid-conversation. The tools are: `list/read/write/search_obsidian`, `list/get_repo/list_issues/get_file_github`, `run_claude_code`, `get_git_status_and_diff`, `git_commit`, `git_push`.

## Git Safety Protocol

CEO's system prompt enforces: always call `get_git_status_and_diff()` first, present a summary to Charles, get explicit confirmation, then call `git_commit()` or `git_push()`. Never skip this.

## Key Config

| Variable | Default | Purpose |
|---|---|---|
| `GEMINI_API_KEY` | — | Required |
| `GITHUB_TOKEN` | empty | GitHub API access |
| `OBSIDIAN_VAULT_PATH` | `C:/Users/charl/Desktop/obi-secondbrain` | Vault location |
| `WHISPER_MODEL` | `base` | STT model size (tiny/base/small) |
| `TTS_VOICE` | `en-US-GuyNeural` | edge-tts voice |
