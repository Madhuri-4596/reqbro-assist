from pydantic import BaseModel, Field, field_validator


class DebugRequest(BaseModel):
    method: str
    endpoint: str = Field(min_length=1)
    status_code: str = Field(min_length=1)
    error_message: str | None = None
    request_body: str | None = None
    response_body: str | None = None

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
