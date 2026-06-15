from fastapi import APIRouter, Depends, status

from app.core.dependencies import get_session_repository
from app.models.schemas import InterviewSessionCreate, InterviewSessionRecord, SessionListResponse
from app.repositories.sessions import SessionRepository

router = APIRouter(tags=["sessions"])


@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(session_repository: SessionRepository = Depends(get_session_repository)) -> SessionListResponse:
    sessions = await session_repository.list_sessions()
    return SessionListResponse(sessions=sessions)


@router.post("/sessions", response_model=InterviewSessionRecord, status_code=status.HTTP_201_CREATED)
async def create_session(
    payload: InterviewSessionCreate,
    session_repository: SessionRepository = Depends(get_session_repository),
) -> InterviewSessionRecord:
    return await session_repository.create_session(payload)
