"""Thin wrapper around the Moss SDK - isolates retrieval timing from the rest of the
request handling, and gives one place to change if the SDK's API shifts.
"""

import os
import time

from moss import DocumentInfo, MossClient, QueryOptions

INDEX_NAME = "api-troubleshooting"
MODEL_ID = "moss-minilm"

_client: MossClient | None = None


def get_client() -> MossClient:
    global _client
    if _client is None:
        project_id = os.environ["MOSS_PROJECT_ID"]
        project_key = os.environ["MOSS_PROJECT_KEY"]
        _client = MossClient(project_id, project_key)
    return _client


async def seed_index(docs: list[dict]) -> None:
    """Creates (or recreates) the troubleshooting index from the curated doc set.
    Run once via scripts/seed_index.py, not on every server start.
    """
    client = get_client()
    documents = [
        DocumentInfo(id=d["id"], text=d["text"], metadata={"category": d["category"]})
        for d in docs
    ]
    await client.create_index(INDEX_NAME, documents, MODEL_ID)
    await client.load_index(INDEX_NAME)


async def search(query_text: str, top_k: int = 5) -> tuple[list[dict], float]:
    """Returns (results, retrieval_ms) - timing measured around only the Moss call,
    not JSON building or anything else, per the hackathon's latency-reporting requirement.
    """
    client = get_client()
    start = time.perf_counter()
    search_result = await client.query(INDEX_NAME, query_text, QueryOptions(top_k=top_k))
    retrieval_ms = (time.perf_counter() - start) * 1000

    results = [
        {
            "id": d.id,
            "text": d.text,
            "category": (d.metadata or {}).get("category"),
            "score": d.score,
        }
        for d in search_result.docs
    ]
    return results, retrieval_ms
