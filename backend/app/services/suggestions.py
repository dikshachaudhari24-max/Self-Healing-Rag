from __future__ import annotations

from app.core.settings import Settings
from app.models.schemas import SuggestResponse, TranscriptTurn


class SuggestionService:
    async def suggest(self, recent_exchanges: list[TranscriptTurn], role: str, competencies_covered: list[str]) -> SuggestResponse:
        raise NotImplementedError


class TemplateSuggestionService(SuggestionService):
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def suggest(self, recent_exchanges: list[TranscriptTurn], role: str, competencies_covered: list[str]) -> SuggestResponse:
        role_name = role.strip().lower() or "the role"
        existing_competencies = [item.strip() for item in competencies_covered if item.strip()]
        suggestions = [
            f"What would success look like in this {role_name} context, and how would you measure it?",
            f"Can you give a concrete example that shows depth in one of the key competencies for this {role_name} role?",
            f"What trade-offs did you consider, and how did you decide which path best fit the role requirements?",
        ]
        competency_tags = existing_competencies[:3] or ["role-fit", "problem-solving", "communication"]
        return SuggestResponse(suggestions=suggestions, competency_tags=competency_tags)


def create_suggestion_service(settings: Settings) -> SuggestionService:
    return TemplateSuggestionService(settings)
