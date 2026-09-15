import time
from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from . import moss_client
from .llm import LlmError, explain
from .models import DebugRequest, DebugResponse, Source
from .redact import redact_all


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Moss queries run locally against an in-process loaded index (that's how it hits
    # sub-10ms - no network round trip per query), so the index must be loaded once
    # here at server startup, not just in the one-time seed script.
    try:
        await moss_client.get_client().load_index(moss_client.INDEX_NAME)
    except Exception as e:
        print(f"WARNING: could not load Moss index at startup: {e}")
    yield


app = FastAPI(title="ReqBro Assist", lifespan=lifespan)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.post("/api/debug", response_model=DebugResponse)
async def debug(req: DebugRequest):
    total_start = time.perf_counter()

    error_message, request_body, response_body = redact_all(
        req.error_message, req.request_body, req.response_body
    )

    query_text = f"{req.method} {req.endpoint} returned {req.status_code}. {error_message or ''}".strip()

    try:
        docs, retrieval_ms = await moss_client.search(query_text, top_k=5)
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail={"error": f"Moss retrieval failed: {e}", "stage": "retrieval"},
        ) from e

    try:
        result, ai_ms = await explain(
            method=req.method,
            endpoint=req.endpoint,
            status_code=req.status_code,
            error_message=error_message,
            request_body=request_body,
            response_body=response_body,
            retrieved_docs=docs,
        )
    except LlmError as e:
        raise HTTPException(
            status_code=502,
            detail={"error": str(e), "stage": "ai"},
        ) from e

    total_ms = (time.perf_counter() - total_start) * 1000

    source_ids = set(result.get("source_ids") or [])
    sources = [
        Source(id=d["id"], category=d["category"], score=d["score"], snippet=d["text"][:220])
        for d in docs
        if d["id"] in source_ids
    ] or [
        Source(id=d["id"], category=d["category"], score=d["score"], snippet=d["text"][:220])
        for d in docs[:3]
    ]

    return DebugResponse(
        meaning=result.get("meaning", ""),
        likely_cause=result.get("likely_cause", ""),
        what_to_check=result.get("what_to_check", []),
        suggested_fix=result.get("suggested_fix", ""),
        needs_more_info=result.get("needs_more_info", False),
        clarifying_question=result.get("clarifying_question"),
        sources=sources,
        retrieval_ms=round(retrieval_ms, 1),
        ai_ms=round(ai_ms, 1),
        total_ms=round(total_ms, 1),
    )


# Serve the frontend as static files - one deployable service, one URL for judges.
app.mount("/", StaticFiles(directory="app/static", html=True), name="static")
