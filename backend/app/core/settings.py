from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "FairHire API"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])

    openai_api_key: str | None = None
    whisper_provider: Literal["openai", "local"] = "openai"
    groq_api_key: str | None = None
    qdrant_url: str | None = None
    qdrant_api_key: str | None = None
    supabase_url: str | None = None
    supabase_service_role_key: str | None = None
    supabase_anon_key: str | None = None

    whisper_model: str = "whisper-1"
    local_whisper_command: str | None = None
    sentiment_model: str = "cardiffnlp/twitter-roberta-base-sentiment-latest"
    bias_model: str = "d4data/bias-detection-model"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    qdrant_collection: str = "fairhire_knowledge_base"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> list[str] | object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @property
    def real_transcription_enabled(self) -> bool:
        return self.whisper_provider == "openai" and bool(self.openai_api_key)

    @property
    def local_transcription_enabled(self) -> bool:
        return self.whisper_provider == "local" and bool(self.local_whisper_command)

    @property
    def real_groq_enabled(self) -> bool:
        return bool(self.groq_api_key)

    @property
    def real_supabase_enabled(self) -> bool:
        return bool(self.supabase_url and self.supabase_service_role_key)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
