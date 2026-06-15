from __future__ import annotations

from app.core.settings import Settings
from app.models.schemas import AnalyzeResponse, ReportResponse, TranscriptTurn


class ReportingService:
    async def build_report(
        self,
        interview_id: str,
        transcript: list[TranscriptTurn],
        analysis: AnalyzeResponse,
        role: str,
        candidate_name: str | None = None,
    ) -> ReportResponse:
        raise NotImplementedError


class MarkdownReportingService(ReportingService):
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def build_report(
        self,
        interview_id: str,
        transcript: list[TranscriptTurn],
        analysis: AnalyzeResponse,
        role: str,
        candidate_name: str | None = None,
    ) -> ReportResponse:
        fairness_score = max(0.0, 100.0 - (len(analysis.bias_flags) * 15.0) - ((10.0 - analysis.engagement_score) * 3.0))
        report_markdown = "\n".join(
            [
                f"# FairHire Interview Report",
                f"- Interview ID: {interview_id}",
                f"- Candidate: {candidate_name or 'Unknown'}",
                f"- Role: {role}",
                "",
                "## Executive Summary",
                f"This interview produced {len(transcript)} transcript turns and {len(analysis.bias_flags)} bias flags.",
                "",
                "## Bias Analysis",
                *(f"- {flag.bias_type}: `{flag.phrase}` -> {flag.suggestion}" for flag in analysis.bias_flags),
                "",
                "## Candidate Evaluation",
                "Candidate performance should be evaluated against the competencies defined for the role.",
                "",
                "## Interviewer Feedback",
                "Keep follow-up questions tied to competencies and avoid demographic assumptions.",
                "",
                f"## Fairness Score\n{fairness_score:.1f}/100",
            ]
        )
        return ReportResponse(report_markdown=report_markdown, fairness_score=round(fairness_score, 2), report_id=f"report_{interview_id}")


def create_reporting_service(settings: Settings) -> ReportingService:
    return MarkdownReportingService(settings)
