import time
from pathlib import Path
from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from . import moss_client
from .llm import LlmError, explain
from .models import DebugRequest, DebugResponse, Source
from .redact import redact_all, redact
from .evidence import matching_docs, trusted_docs, fallback, SOURCE_URL


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Moss queries run locally against an in-process loaded index (that's how it hits
    # sub-10ms - no network round trip per query), so the index must be loaded once
    # here at server startup, not just in the one-time seed script.
    try:
        await moss_client.get_client().load_index(moss_client.INDEX_NAME)
    except Exception as e:
        print("WARNING: Moss index is unavailable; check server configuration.")
    yield


app = FastAPI(title="ReqBro Assist", lifespan=lifespan)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "detail": {
                "error": "Check the method, endpoint, error status (400-599), and input length limits.",
                "stage": "validation",
            }
        },
    )


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.post("/api/debug", response_model=DebugResponse)
async def debug(req: DebugRequest):
    total_start = time.perf_counter()

    endpoint, error_message, request_body, response_body = redact_all(
        req.endpoint, req.error_message, req.request_body, req.response_body
    )

    query_text = f"{req.method} {endpoint} returned {req.status_code}. {error_message or ''}".strip()

    try:
        docs, retrieval_ms = await moss_client.search(query_text, top_k=5)
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail={"error": "Documentation search is temporarily unavailable. Please try again later.", "stage": "retrieval"},
        ) from e

    usable = matching_docs(docs, req.status_code, error_message, response_body)
    sparse = not (error_message or '').strip() and not (response_body or '').strip()
    ai_ms = 0.0
    if sparse or not usable:
        result = fallback(sparse)
    else:
        try:
            result, ai_ms = await explain(
                method=req.method, endpoint=endpoint, status_code=req.status_code,
                error_message=error_message, request_body=request_body,
                response_body=response_body, retrieved_docs=usable,
            )
        except LlmError as e:
            raise HTTPException(status_code=502, detail={
                "error": "The explanation service could not produce a usable answer. Please try again later.",
                "stage": "ai"}) from e
        # Missing citations or an abstention cannot coexist with a displayed diagnosis.
        if (not result.get('source_ids') or result.get('needs_more_info')
                or result.get('insufficient_evidence')):
            result = fallback(bool(result.get('needs_more_info')))

    total_ms = (time.perf_counter() - total_start) * 1000

    # Always show what was actually retrieved and considered, whether or not the model
    # cited it - "cited" records the model's references, not an independent proof of support,
    # rather than silently hiding low-relevance docs that were still part of retrieval.
    cited_ids = set(result.get("source_ids") or [])
    trusted_ids = {d["id"] for d in trusted_docs(docs)}
    sources = [
        Source(
            id=d["id"],
            category=d["category"],
            score=d["score"],
            snippet=redact(d["text"])[:220],
            url=SOURCE_URL if d["id"] in trusted_ids else None,
            trusted=d["id"] in trusted_ids,
            cited=d["id"] in cited_ids,
        )
        for d in docs
    ]

    return DebugResponse(
        meaning=result.get("meaning", ""),
        likely_cause=result.get("likely_cause", ""),
        what_to_check=result.get("what_to_check", []),
        suggested_fix=result.get("suggested_fix", ""),
        needs_more_info=result.get("needs_more_info", False),
        insufficient_evidence=result.get("insufficient_evidence", False),
        clarifying_question=result.get("clarifying_question"),
        sources=sources,
        retrieval_ms=round(retrieval_ms, 1),
        ai_ms=round(ai_ms, 1),
        total_ms=round(total_ms, 1),
        data_retained=False,
    )


# Serve the frontend as static files - one deployable service, one URL for judges.
app.mount("/", StaticFiles(directory=Path(__file__).parent / "static", html=True), name="static")
