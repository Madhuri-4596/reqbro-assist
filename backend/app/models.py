from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Literal


class DebugRequest(BaseModel):
    method: Literal['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS']
    endpoint: str = Field(min_length=1, max_length=2048)
    status_code: str = Field(pattern=r'^[45]\d{2}$')
    error_message: str | None = Field(default=None, max_length=8000)
    request_body: str | None = Field(default=None, max_length=16000)
    response_body: str | None = Field(default=None, max_length=16000)

    @field_validator("endpoint", "status_code")
    @classmethod
    def not_just_whitespace(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("cannot be blank")
        return v.strip()


class Source(BaseModel):
    id: str
    category: str | None
    score: float
    snippet: str
    cited: bool
    url: str | None = None
    trusted: bool = False


class Explanation(BaseModel):
    model_config = ConfigDict(strict=True, extra='forbid')
    meaning: str
    likely_cause: str
    what_to_check: list[str]
    suggested_fix: str
    source_ids: list[str]
    needs_more_info: bool
    insufficient_evidence: bool
    clarifying_question: str | None


class DebugResponse(BaseModel):
    meaning: str
    likely_cause: str
    what_to_check: list[str]
    suggested_fix: str
    needs_more_info: bool
    insufficient_evidence: bool
    clarifying_question: str | None
    sources: list[Source]
    retrieval_ms: float
    ai_ms: float
    total_ms: float
    data_retained: bool = False


class ErrorResponse(BaseModel):
    error: str
    stage: str  # "redaction" | "retrieval" | "ai" | "unknown"
