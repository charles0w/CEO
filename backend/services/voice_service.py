import asyncio
import os
import tempfile
from config import settings


class VoiceService:
    def __init__(self):
        self._whisper = None

    def _model(self):
        if self._whisper is None:
            from faster_whisper import WhisperModel
            self._whisper = WhisperModel(settings.whisper_model, device="cpu", compute_type="int8")
        return self._whisper

    def transcribe(self, audio_bytes: bytes) -> str:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio_bytes)
            tmp = f.name
        try:
            segments, _ = self._model().transcribe(tmp, language="en", beam_size=5)
            return " ".join(s.text for s in segments).strip() or "[No speech detected]"
        finally:
            os.unlink(tmp)

    async def synthesize(self, text: str) -> bytes:
        import edge_tts
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            tmp = f.name
        try:
            await asyncio.wait_for(
                edge_tts.Communicate(text, settings.tts_voice).save(tmp),
                timeout=settings.tts_timeout_seconds,
            )
            with open(tmp, "rb") as f:
                return f.read()
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)
