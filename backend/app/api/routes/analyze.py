from fastapi import APIRouter, Depends

from app.core.dependencies import get_analysis_service
from app.models.schemas import AnalyzeRequest, AnalyzeResponse
from app.services.analysis import AnalysisService

router = APIRouter(tags=["analyze"])


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_transcript(
    payload: AnalyzeRequest,
    analysis_service: AnalysisService = Depends(get_analysis_service),
) -> AnalyzeResponse:
    return await analysis_service.analyze(transcript=payload.transcript, role=payload.role)
