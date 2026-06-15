from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.core.dependencies import get_transcription_service
from app.models.schemas import UploadResponse
from app.services.transcription import TranscriptionService

router = APIRouter(tags=["upload"])


@router.post("/upload", response_model=UploadResponse)
async def upload_audio(
    audio_file: UploadFile = File(...),
    interview_id: str = Form(...),
    role: str = Form(...),
    transcription_service: TranscriptionService = Depends(get_transcription_service),
) -> UploadResponse:
    if not audio_file.filename:
        raise HTTPException(status_code=400, detail="Unsupported file format")

    audio_bytes = await audio_file.read()
    transcript = await transcription_service.transcribe(
        audio_bytes=audio_bytes,
        filename=audio_file.filename,
        interview_id=interview_id,
        role=role,
    )
    return UploadResponse(interview_id=interview_id, transcript=transcript)
