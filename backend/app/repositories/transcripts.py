from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Protocol

from app.core.settings import Settings
from app.models.schemas import TranscriptRowCreate, TranscriptTurn

logger = logging.getLogger(__name__)


class TranscriptRepository(Protocol):
    async def store_transcript_rows(self, interview_id: str, transcript: list[TranscriptTurn]) -> list[TranscriptRowCreate]:
        ...


class InMemoryTranscriptRepository:
    def __init__(self) -> None:
        self._rows: list[TranscriptRowCreate] = []

    async def store_transcript_rows(self, interview_id: str, transcript: list[TranscriptTurn]) -> list[TranscriptRowCreate]:
        rows = [
            TranscriptRowCreate(
                interview_id=interview_id,
                speaker=turn.speaker,
                text=turn.text,
                timestamp_start=turn.start or 0.0,
                turn_index=turn.turn_index or index,
            )
            for index, turn in enumerate(transcript, start=1)
        ]
        self._rows.extend(rows)
        logger.info("Transcript stored in memory", extra={"interview_id": interview_id, "row_count": len(rows)})
        return rows


class SupabaseTranscriptRepository(InMemoryTranscriptRepository):
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

    async def store_transcript_rows(self, interview_id: str, transcript: list[TranscriptTurn]) -> list[TranscriptRowCreate]:
        client = self._get_client()
        rows = [
            TranscriptRowCreate(
                interview_id=interview_id,
                speaker=turn.speaker,
                text=turn.text,
                timestamp_start=turn.start or 0.0,
                turn_index=turn.turn_index or index,
            )
            for index, turn in enumerate(transcript, start=1)
        ]

        if client is None:
            return await super().store_transcript_rows(interview_id, transcript)

        payload = [row.model_dump() for row in rows]
        try:
            client.table("transcripts").insert(payload).execute()
        except Exception as exc:
            raise RuntimeError("Failed to store transcript rows in Supabase") from exc

        logger.info(
            "Transcript stored in Supabase",
            extra={
                "interview_id": interview_id,
                "row_count": len(rows),
                "stored_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        return rows


def create_transcript_repository(settings: Settings) -> TranscriptRepository:
    return SupabaseTranscriptRepository(settings) if settings.real_supabase_enabled else InMemoryTranscriptRepository()