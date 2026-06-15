from __future__ import annotations

from io import BytesIO

from app.core.settings import Settings
from app.models.schemas import TranscriptTurn


class TranscriptionService:
    async def transcribe(self, audio_bytes: bytes, filename: str | None, interview_id: str, role: str) -> list[TranscriptTurn]:
        raise NotImplementedError


class MockTranscriptionService(TranscriptionService):
    async def transcribe(self, audio_bytes: bytes, filename: str | None, interview_id: str, role: str) -> list[TranscriptTurn]:
        return [
            TranscriptTurn(speaker="interviewer", text="Can you walk me through a project you're proud of?", start=0.0, end=4.2, turn_index=1),
            TranscriptTurn(speaker="candidate", text="I led a small analytics project and improved reporting accuracy.", start=4.2, end=9.5, turn_index=2),
            TranscriptTurn(speaker="interviewer", text="What made that project successful?", start=9.5, end=12.1, turn_index=3),
            TranscriptTurn(speaker="candidate", text="The team stayed aligned and I broke the problem into clear steps.", start=12.1, end=17.0, turn_index=4),
        ]


class OpenAIWhisperTranscriptionService(TranscriptionService):
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def transcribe(self, audio_bytes: bytes, filename: str | None, interview_id: str, role: str) -> list[TranscriptTurn]:
        if not self._settings.real_transcription_enabled:
            return await MockTranscriptionService().transcribe(audio_bytes, filename, interview_id, role)

        try:
            from openai import AsyncOpenAI
        except ImportError:
            return await MockTranscriptionService().transcribe(audio_bytes, filename, interview_id, role)

        client = AsyncOpenAI(api_key=self._settings.openai_api_key)
        buffer = BytesIO(audio_bytes)
        upload_name = filename or f"{interview_id}.audio"
        try:
            transcription = await client.audio.transcriptions.create(
                file=(upload_name, buffer),
                model=self._settings.whisper_model,
            )
            text = getattr(transcription, "text", str(transcription))
        except Exception:
            return await MockTranscriptionService().transcribe(audio_bytes, filename, interview_id, role)

        return [
            TranscriptTurn(speaker="interviewer", text=text, start=0.0, end=None, turn_index=1),
        ]


def create_transcription_service(settings: Settings) -> TranscriptionService:
    return OpenAIWhisperTranscriptionService(settings)
