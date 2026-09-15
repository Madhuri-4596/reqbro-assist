from pydantic import BaseModel


class DebugRequest(BaseModel):
    method: str
    endpoint: str
    status_code: str
    error_message: str | None = None
    request_body: str | None = None
    response_body: str | None = None


class Source(BaseModel):
    id: str
    category: str | None
    score: float
    snippet: str


class DebugResponse(BaseModel):
    meaning: str
    likely_cause: str
    what_to_check: list[str]
    suggested_fix: str
    needs_more_info: bool
    clarifying_question: str | None
    sources: list[Source]
    retrieval_ms: float
    ai_ms: float
    total_ms: float


class ErrorResponse(BaseModel):
    error: str
    stage: str  # "redaction" | "retrieval" | "ai" | "unknown"
