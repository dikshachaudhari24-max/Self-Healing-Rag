from fastapi import APIRouter, Depends

from app.core.dependencies import get_suggestion_service
from app.models.schemas import SuggestRequest, SuggestResponse
from app.services.suggestions import SuggestionService

router = APIRouter(tags=["suggest"])


@router.post("/suggest", response_model=SuggestResponse)
async def suggest_followups(
    payload: SuggestRequest,
    suggestion_service: SuggestionService = Depends(get_suggestion_service),
) -> SuggestResponse:
    return await suggestion_service.suggest(
        recent_exchanges=payload.recent_exchanges,
        role=payload.role,
        competencies_covered=payload.competencies_covered,
    )
