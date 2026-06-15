import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.core.dependencies import get_transcription_service
from app.models.schemas import TranscriptTurnResponse, UploadResponse
from app.services.transcription import (
    EmptyTranscriptError,
    TranscriptionService,
    UnsupportedAudioFormatError,
    WhisperProviderError,
    is_supported_audio_file,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["upload"])


@router.post("/upload", response_model=UploadResponse)
async def upload_audio(
    audio_file: UploadFile | None = File(default=None),
    interview_id: str = Form(...),
    role: str = Form(...),
    transcription_service: TranscriptionService = Depends(get_transcription_service),
) -> UploadResponse:
    if audio_file is None:
        raise HTTPException(status_code=400, detail="Missing audio file")

    if not audio_file.filename:
        raise HTTPException(status_code=400, detail="Unsupported file format")

    if not is_supported_audio_file(audio_file.filename, audio_file.content_type):
        raise HTTPException(status_code=400, detail="Unsupported file format")

    logger.info("Upload received", extra={"interview_id": interview_id, "role": role, "filename": audio_file.filename})
    audio_bytes = await audio_file.read()

    try:
        transcript = await transcription_service.transcribe(
            audio_bytes=audio_bytes,
            filename=audio_file.filename,
            interview_id=interview_id,
            role=role,
        )
    except UnsupportedAudioFormatError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except EmptyTranscriptError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except WhisperProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    response_transcript = [
        TranscriptTurnResponse(speaker=turn.speaker, text=turn.text, start=turn.start, end=turn.end)
        for turn in transcript
    ]
    return UploadResponse(interview_id=interview_id, transcript=response_transcript)
