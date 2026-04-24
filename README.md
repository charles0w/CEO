# CEO — Personal AI Assistant

CEO is a Jarvis-style personal AI assistant that runs locally on your Desktop. Talk to it via voice or text from your phone or browser. Powered by Gemini 2.0 Flash.

---

## Prerequisites

- **Python 3.10+** — for the backend
- **Node.js 18+** — for the mobile/web app
- **ffmpeg** — required by the voice transcription engine

```
winget install ffmpeg
```

- **Gemini API key** — free tier at [aistudio.google.com](https://aistudio.google.com)

---

## Setup

### 1. Backend

```bash
cd backend
copy .env.example .env
# Edit .env and fill in your GEMINI_API_KEY
```

Then start the server (double-click or run in terminal):

```batch
start.bat
```

This creates a virtual environment, installs dependencies, and starts the server at `http://0.0.0.0:8000`.

> **First run:** Whisper downloads the `base` STT model (~145 MB) automatically.

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

To find your Desktop IP: open Command Prompt → run `ipconfig` → look for **IPv4 Address** under your WiFi adapter.

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
GEMINI_API_KEY=your_key_here
GITHUB_TOKEN=                          # optional — for GitHub integration
OBSIDIAN_VAULT_PATH=C:/Users/charl/Desktop/obi-secondbrain
WHISPER_MODEL=base                     # tiny | base | small
TTS_VOICE=en-US-GuyNeural
```

---

## Architecture

```
CEO/
├── backend/
│   ├── main.py                    # FastAPI — WebSocket /ws
│   ├── config.py                  # Settings from .env
│   └── services/
│       ├── gemini_service.py      # Gemini 2.0 Flash brain + tool calling
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
