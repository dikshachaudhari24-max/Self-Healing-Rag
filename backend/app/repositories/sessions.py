from __future__ import annotations

from datetime import datetime, timezone
from typing import Protocol
from uuid import uuid4

from app.core.settings import Settings
from app.models.schemas import InterviewSessionCreate, InterviewSessionRecord, SessionStatus


class SessionRepository(Protocol):
    async def list_sessions(self) -> list[InterviewSessionRecord]:
        ...

    async def create_session(self, payload: InterviewSessionCreate) -> InterviewSessionRecord:
        ...


class InMemorySessionRepository:
    def __init__(self) -> None:
        self._sessions: list[InterviewSessionRecord] = []

    async def list_sessions(self) -> list[InterviewSessionRecord]:
        return list(self._sessions)

    async def create_session(self, payload: InterviewSessionCreate) -> InterviewSessionRecord:
        record = InterviewSessionRecord(
            id=str(uuid4()),
            interviewer_id=payload.interviewer_id,
            candidate_name=payload.candidate_name,
            role=payload.role,
            status=payload.status,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self._sessions.append(record)
        return record


class SupabaseSessionRepository(InMemorySessionRepository):
    def __init__(self, settings: Settings) -> None:
        super().__init__()
        self._settings = settings
        self._client = None

    def _get_client(self):
        if not self._settings.real_supabase_enabled:
            return None
        if self._client is None:
            from supabase import create_client

            self._client = create_client(self._settings.supabase_url, self._settings.supabase_service_role_key)
        return self._client

    async def list_sessions(self) -> list[InterviewSessionRecord]:
        client = self._get_client()
        if client is None:
            return await super().list_sessions()

        rows = client.table("interviews").select("id, interviewer_id, candidate_name, role, status, created_at").order("created_at", desc=True).execute().data
        return [
            InterviewSessionRecord(
                id=row["id"],
                interviewer_id=row.get("interviewer_id"),
                candidate_name=row["candidate_name"],
                role=row["role"],
                status=SessionStatus(row["status"]),
                created_at=row.get("created_at"),
            )
            for row in rows
        ]

    async def create_session(self, payload: InterviewSessionCreate) -> InterviewSessionRecord:
        client = self._get_client()
        if client is None:
            return await super().create_session(payload)

        row = (
            client.table("interviews")
            .insert(
                {
                    "interviewer_id": payload.interviewer_id,
                    "candidate_name": payload.candidate_name,
                    "role": payload.role,
                    "status": payload.status.value,
                }
            )
            .execute()
            .data[0]
        )
        return InterviewSessionRecord(
            id=row["id"],
            interviewer_id=row.get("interviewer_id"),
            candidate_name=row["candidate_name"],
            role=row["role"],
            status=SessionStatus(row["status"]),
            created_at=row.get("created_at"),
        )


def create_session_repository(settings: Settings) -> SessionRepository:
    return SupabaseSessionRepository(settings) if settings.real_supabase_enabled else InMemorySessionRepository()
