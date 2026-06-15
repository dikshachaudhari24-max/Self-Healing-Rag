from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from app.core.settings import Settings
from app.models.schemas import AnalyzeResponse, BiasFlag, SentimentScore, TranscriptTurn


@dataclass
class AnalysisResult:
    sentiment_scores: list[SentimentScore]
    bias_flags: list[BiasFlag]
    engagement_score: float
    summary_stats: dict[str, float | int | str]


class AnalysisService:
    async def analyze(self, transcript: list[TranscriptTurn], role: str) -> AnalyzeResponse:
        raise NotImplementedError


class HeuristicAnalysisService(AnalysisService):
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def analyze(self, transcript: list[TranscriptTurn], role: str) -> AnalyzeResponse:
        sentiment_scores = self._score_sentiment(transcript)
        bias_flags = self._detect_bias(transcript)
        engagement_score = self._score_engagement(transcript)
        summary_stats = {
            "role": role,
            "candidate_turns": sum(1 for turn in transcript if turn.speaker == "candidate"),
            "interviewer_turns": sum(1 for turn in transcript if turn.speaker == "interviewer"),
            "flagged_turns": len(bias_flags),
        }
        return AnalyzeResponse(
            sentiment_scores=sentiment_scores,
            bias_flags=bias_flags,
            engagement_score=engagement_score,
            summary_stats=summary_stats,
        )

    def _score_sentiment(self, transcript: list[TranscriptTurn]) -> list[SentimentScore]:
        positive_words = {"good", "great", "excited", "confident", "strong"}
        negative_words = {"worried", "bad", "stress", "difficult", "confused"}
        scores: list[SentimentScore] = []
        for turn in transcript:
            if turn.speaker != "candidate":
                continue
            text = turn.text.lower()
            positive_hits = sum(word in text for word in positive_words)
            negative_hits = sum(word in text for word in negative_words)
            if positive_hits > negative_hits:
                label = "positive"
                score = min(1.0, 0.5 + 0.1 * positive_hits)
            elif negative_hits > positive_hits:
                label = "negative"
                score = min(1.0, 0.5 + 0.1 * negative_hits)
            else:
                label = "neutral"
                score = 0.5
            scores.append(SentimentScore(turn_index=turn.turn_index or 0, label=label, score=round(score, 2)))
        return scores

    def _detect_bias(self, transcript: list[TranscriptTurn]) -> list[BiasFlag]:
        bias_keywords = {
            "age": ["how old", "age", "young", "old enough"],
            "family": ["married", "children", "kids", "family planning"],
            "gendered": ["guys", "girls", "man up"],
            "legal": ["religion", "race", "pregnant", "disability"],
        }
        flags: list[BiasFlag] = []
        for turn in transcript:
            if turn.speaker != "interviewer":
                continue
            lowered = turn.text.lower()
            for bias_type, phrases in bias_keywords.items():
                for phrase in phrases:
                    if phrase in lowered:
                        flags.append(
                            BiasFlag(
                                phrase=phrase,
                                bias_type=bias_type,
                                confidence=0.74,
                                suggestion="Reframe the question around role-relevant competencies.",
                                turn_index=turn.turn_index or 0,
                            )
                        )
                        break
        return flags

    def _score_engagement(self, transcript: list[TranscriptTurn]) -> float:
        candidate_turns = [turn for turn in transcript if turn.speaker == "candidate"]
        if not candidate_turns:
            return 0.0
        word_counts = [len(turn.text.split()) for turn in candidate_turns]
        avg_length = sum(word_counts) / len(word_counts)
        diversity = len({word.lower() for turn in candidate_turns for word in turn.text.split()})
        ratio = len(candidate_turns) / max(1, sum(1 for turn in transcript if turn.speaker == "interviewer"))
        raw_score = min(10.0, (avg_length / 10.0) + diversity / 25.0 + ratio * 2.0)
        return round(raw_score, 2)


def create_analysis_service(settings: Settings) -> AnalysisService:
    return HeuristicAnalysisService(settings)
