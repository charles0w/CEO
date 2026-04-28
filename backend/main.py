import asyncio
import base64
import json
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from services.llm_service import LLMService
from services.voice_service import VoiceService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [CEO] %(message)s")
log = logging.getLogger("CEO")

llm = LLMService()
voice = VoiceService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    if llm.provider_model:
        log.info("CEO is online using %s (%s).", llm.provider_name, llm.provider_model)
    else:
        log.info("CEO is online using %s.", llm.provider_name)
    yield
    log.info("CEO shutting down.")


app = FastAPI(title="CEO — Personal AI Assistant", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ConnectionManager:
    def __init__(self):
        self.connections: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.connections.append(ws)
        log.info(f"Client connected ({len(self.connections)} active)")

    def disconnect(self, ws: WebSocket):
        self.connections.discard(ws) if hasattr(self.connections, 'discard') else (
            self.connections.remove(ws) if ws in self.connections else None
        )
        log.info(f"Client disconnected ({len(self.connections)} active)")

    async def send(self, ws: WebSocket, data: dict):
        await ws.send_text(json.dumps(data))


manager = ConnectionManager()


@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        greeting = "CEO online. What do you need, Boss?"
        audio = await voice.synthesize(greeting)
        await manager.send(websocket, {
            "type": "response",
            "text": greeting,
            "audio": base64.b64encode(audio).decode(),
        })

        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)

            if msg.get("type") == "reset":
                text = llm.reset()
                await manager.send(websocket, {"type": "response", "text": text, "audio": None})
                continue

            if msg.get("type") == "voice":
                audio_bytes = base64.b64decode(msg["audio"])
                loop = asyncio.get_event_loop()
                user_text = await loop.run_in_executor(None, voice.transcribe, audio_bytes)
                await manager.send(websocket, {"type": "transcription", "text": user_text})
            elif msg.get("type") == "text":
                user_text = msg.get("content", "").strip()
            else:
                continue

            if not user_text:
                continue

            log.info(f"User: {user_text}")
            response_text = await llm.send(user_text)
            log.info(f"CEO: {response_text[:120]}")
            telemetry = llm.last_telemetry()
            if telemetry:
                log.info("LLM telemetry: %s", json.dumps(telemetry, sort_keys=True))

            response_audio = await voice.synthesize(response_text)
            await manager.send(websocket, {
                "type": "response",
                "text": response_text,
                "audio": base64.b64encode(response_audio).decode(),
            })

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        log.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


@app.get("/health")
async def health():
    return {
        "status": "online",
        "connections": len(manager.connections),
        "llm_provider": llm.provider_name,
        "llm_model": llm.provider_model,
    }


@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    audio_bytes = await file.read()
    loop = asyncio.get_event_loop()
    text = await loop.run_in_executor(None, voice.transcribe, audio_bytes)
    return {"text": text}


@app.post("/speak")
async def speak(text: str):
    audio = await voice.synthesize(text)
    return Response(content=audio, media_type="audio/mpeg")
