from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

SpeakerLabel = Literal["interviewer", "candidate"]


class TranscriptTurnResponse(BaseModel):
    speaker: SpeakerLabel
    text: str
    start: float | None = None
    end: float | None = None


class TranscriptTurn(BaseModel):
    speaker: SpeakerLabel
    text: str
    start: float | None = None
    end: float | None = None
    turn_index: int | None = None


class UploadResponse(BaseModel):
    interview_id: str
    transcript: list[TranscriptTurnResponse]


class TranscriptRowCreate(BaseModel):
    interview_id: str
    speaker: SpeakerLabel
    text: str
    timestamp_start: float
    turn_index: int


class WhisperSegment(BaseModel):
    text: str
    start: float | None = None
    end: float | None = None


class WhisperTranscript(BaseModel):
    text: str = ""
    segments: list[WhisperSegment] = Field(default_factory=list)


class AnalyzeRequest(BaseModel):
    interview_id: str
    transcript: list[TranscriptTurn]
    role: str


class SentimentScore(BaseModel):
    turn_index: int
    label: Literal["positive", "negative", "neutral"]
    score: float


class BiasFlag(BaseModel):
    phrase: str
    bias_type: str
    confidence: float
    suggestion: str
    turn_index: int


class AnalyzeResponse(BaseModel):
    sentiment_scores: list[SentimentScore]
    bias_flags: list[BiasFlag]
    engagement_score: float
    summary_stats: dict[str, float | int | str]


class SuggestRequest(BaseModel):
    interview_id: str
    recent_exchanges: list[TranscriptTurn]
    role: str
    competencies_covered: list[str] = Field(default_factory=list)


class SuggestResponse(BaseModel):
    suggestions: list[str]
    competency_tags: list[str]


class ReportRequest(BaseModel):
    interview_id: str


class ReportResponse(BaseModel):
    report_markdown: str
    fairness_score: float
    report_id: str


class SessionStatus(str, Enum):
    pending = "pending"
    active = "active"
    completed = "completed"


class InterviewSessionCreate(BaseModel):
    interviewer_id: str | None = None
    candidate_name: str
    role: str
    status: SessionStatus = SessionStatus.pending


class InterviewSessionRecord(BaseModel):
    id: str
    interviewer_id: str | None = None
    candidate_name: str
    role: str
    status: SessionStatus
    created_at: str | None = None


class SessionListResponse(BaseModel):
    sessions: list[InterviewSessionRecord]
