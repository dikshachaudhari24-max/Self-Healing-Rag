from fastapi import APIRouter, Depends

from app.core.dependencies import get_reporting_service, get_session_repository
from app.models.schemas import AnalyzeResponse, ReportRequest, ReportResponse, TranscriptTurn
from app.repositories.sessions import SessionRepository
from app.services.reporting import ReportingService

router = APIRouter(tags=["report"])


@router.post("/report", response_model=ReportResponse)
async def generate_report(
    payload: ReportRequest,
    session_repository: SessionRepository = Depends(get_session_repository),
    reporting_service: ReportingService = Depends(get_reporting_service),
) -> ReportResponse:
    sessions = await session_repository.list_sessions()
    matching_session = next((session for session in sessions if session.id == payload.interview_id), None)
    role = matching_session.role if matching_session else "unknown"

    transcript: list[TranscriptTurn] = []
    analysis = AnalyzeResponse(sentiment_scores=[], bias_flags=[], engagement_score=0.0, summary_stats={})
    return await reporting_service.build_report(
        interview_id=payload.interview_id,
        transcript=transcript,
        analysis=analysis,
        role=role,
        candidate_name=matching_session.candidate_name if matching_session else None,
    )
