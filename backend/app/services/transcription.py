from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from typing import Protocol

from app.core.settings import Settings
from app.models.schemas import TranscriptTurn, WhisperSegment, WhisperTranscript
from app.repositories.transcripts import TranscriptRepository

logger = logging.getLogger(__name__)

SUPPORTED_AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".webm"}
SUPPORTED_AUDIO_CONTENT_TYPES = {
    "audio/mpeg",
    "audio/mp3",
    "audio/wav",
    "audio/x-wav",
    "audio/mp4",
    "audio/m4a",
    "audio/x-m4a",
    "audio/x-mp4",
    "audio/webm",
    "video/webm",
    "application/octet-stream",
}


class UnsupportedAudioFormatError(ValueError):
    pass


class EmptyTranscriptError(ValueError):
    pass


class WhisperProviderError(RuntimeError):
    pass


class WhisperProvider(Protocol):
    async def transcribe(self, audio_bytes: bytes, filename: str) -> WhisperTranscript:
        ...


def is_supported_audio_file(filename: str | None, content_type: str | None = None) -> bool:
    if not filename:
        return False

    extension = Path(filename).suffix.lower()
    if extension not in SUPPORTED_AUDIO_EXTENSIONS:
        return False

    if content_type:
        normalized_content_type = content_type.split(";", 1)[0].strip().lower()
        if normalized_content_type not in SUPPORTED_AUDIO_CONTENT_TYPES:
            return False

    return True


class OpenAIWhisperProvider:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def transcribe(self, audio_bytes: bytes, filename: str) -> WhisperTranscript:
        if not self._settings.real_transcription_enabled:
            raise WhisperProviderError("OPENAI_API_KEY is required for the Whisper provider")

        try:
            from openai import AsyncOpenAI
        except ImportError as exc:
            raise WhisperProviderError("The openai package is not installed") from exc

        logger.info("Whisper request started", extra={"provider": "openai", "filename": filename})

        try:
            client = AsyncOpenAI(api_key=self._settings.openai_api_key)
            with tempfile.NamedTemporaryFile(suffix=Path(filename).suffix or ".audio", delete=False) as temp_file:
                temp_file.write(audio_bytes)
                temp_file.flush()
                temp_path = Path(temp_file.name)

            try:
                with temp_path.open("rb") as audio_file:
                    response = None
                    for extra_kwargs in (
                        {"response_format": "verbose_json", "timestamp_granularities": ["segment"]},
                        {"response_format": "verbose_json"},
                    ):
                        try:
                            response = await client.audio.transcriptions.create(
                                file=audio_file,
                                model=self._settings.whisper_model,
                                **extra_kwargs,
                            )
                            break
                        except TypeError:
                            continue

                if response is None:
                    raise WhisperProviderError("Whisper request could not be created")

                transcript = self._normalize_response(response)
            finally:
                temp_path.unlink(missing_ok=True)
        except WhisperProviderError:
            raise
        except Exception as exc:
            raise WhisperProviderError("OpenAI Whisper request failed") from exc

        logger.info("Whisper request completed", extra={"provider": "openai", "filename": filename, "segment_count": len(transcript.segments)})
        return transcript

    def _normalize_response(self, response: object) -> WhisperTranscript:
        if hasattr(response, "model_dump"):
            payload = response.model_dump()
        elif isinstance(response, dict):
            payload = response
        else:
            payload = {"text": getattr(response, "text", ""), "segments": getattr(response, "segments", [])}

        text = str(payload.get("text") or "").strip()
        raw_segments = payload.get("segments") or []
        segments: list[WhisperSegment] = []
        for segment in raw_segments:
            if hasattr(segment, "model_dump"):
                segment_payload = segment.model_dump()
            elif isinstance(segment, dict):
                segment_payload = segment
            else:
                segment_payload = {
                    "text": getattr(segment, "text", ""),
                    "start": getattr(segment, "start", None),
                    "end": getattr(segment, "end", None),
                }

            segment_text = str(segment_payload.get("text") or "").strip()
            if not segment_text:
                continue

            segments.append(
                WhisperSegment(
                    text=segment_text,
                    start=segment_payload.get("start"),
                    end=segment_payload.get("end"),
                )
            )

        if not segments and text:
            segments = [WhisperSegment(text=text, start=0.0, end=None)]

        return WhisperTranscript(text=text, segments=segments)


class LocalWhisperProvider:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def transcribe(self, audio_bytes: bytes, filename: str) -> WhisperTranscript:
        raise WhisperProviderError("Local Whisper provider is not configured yet")


def create_whisper_provider(settings: Settings) -> WhisperProvider:
    if settings.whisper_provider == "local":
        return LocalWhisperProvider(settings)
    return OpenAIWhisperProvider(settings)


class TranscriptionService:
    async def transcribe(self, audio_bytes: bytes, filename: str, interview_id: str, role: str) -> list[TranscriptTurn]:
        raise NotImplementedError


class WhisperTranscriptionService(TranscriptionService):
    def __init__(self, settings: Settings, whisper_provider: WhisperProvider, transcript_repository: TranscriptRepository) -> None:
        self._settings = settings
        self._whisper_provider = whisper_provider
        self._transcript_repository = transcript_repository

    async def transcribe(self, audio_bytes: bytes, filename: str, interview_id: str, role: str) -> list[TranscriptTurn]:
        if not is_supported_audio_file(filename, None):
            raise UnsupportedAudioFormatError("Unsupported file format")

        whisper_transcript = await self._whisper_provider.transcribe(audio_bytes=audio_bytes, filename=filename)
        transcript = self._normalize_turns(whisper_transcript)

        if not transcript:
            raise EmptyTranscriptError("Empty transcript returned by Whisper")

        await self._transcript_repository.store_transcript_rows(interview_id=interview_id, transcript=transcript)
        return transcript

    def _normalize_turns(self, transcript: WhisperTranscript) -> list[TranscriptTurn]:
        if not transcript.segments and transcript.text:
            segments = [WhisperSegment(text=transcript.text, start=0.0, end=None)]
        else:
            segments = transcript.segments

        turns: list[TranscriptTurn] = []
        for index, segment in enumerate(segments, start=1):
            speaker = "interviewer" if index % 2 == 1 else "candidate"
            turns.append(
                TranscriptTurn(
                    speaker=speaker,
                    text=segment.text.strip(),
                    start=segment.start,
                    end=segment.end,
                    turn_index=index,
                )
            )

        return turns


def create_transcription_service(settings: Settings, transcript_repository: TranscriptRepository) -> TranscriptionService:
    whisper_provider = create_whisper_provider(settings)
    return WhisperTranscriptionService(settings, whisper_provider, transcript_repository)