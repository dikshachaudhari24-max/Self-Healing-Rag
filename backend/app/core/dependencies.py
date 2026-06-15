from functools import lru_cache

from app.core.settings import get_settings
from app.repositories.sessions import SessionRepository, create_session_repository
from app.services.analysis import AnalysisService, create_analysis_service
from app.services.reporting import ReportingService, create_reporting_service
from app.services.suggestions import SuggestionService, create_suggestion_service
from app.services.transcription import TranscriptionService, create_transcription_service


@lru_cache(maxsize=1)
def get_session_repository() -> SessionRepository:
    return create_session_repository(get_settings())


@lru_cache(maxsize=1)
def get_transcription_service() -> TranscriptionService:
    return create_transcription_service(get_settings())


@lru_cache(maxsize=1)
def get_analysis_service() -> AnalysisService:
    return create_analysis_service(get_settings())


@lru_cache(maxsize=1)
def get_suggestion_service() -> SuggestionService:
    return create_suggestion_service(get_settings())


@lru_cache(maxsize=1)
def get_reporting_service() -> ReportingService:
    return create_reporting_service(get_settings())
