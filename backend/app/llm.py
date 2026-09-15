"""OpenAI chat-completion call that turns retrieved doc chunks + the user's error
report into a structured explanation. Same provider ReqBro's own AI Assist uses.
"""

import json
import os
import time

import httpx

OPENAI_URL = "https://api.openai.com/v1/chat/completions"
MODEL = "gpt-4o-mini"

SYSTEM_PROMPT = """You are ReqBro Assist, an API debugging assistant. You are given:
- Details about a failed HTTP request (method, endpoint, status code, error message, optional bodies)
- A set of retrieved documentation snippets that may or may not be relevant

Using ONLY the retrieved snippets and the request details as your basis, respond with a JSON object with these exact keys:
- "meaning": one or two sentences on what this error means
- "likely_cause": the most probable cause given the specific details provided
- "what_to_check": a short list (as an array of strings) of concrete things to check
- "suggested_fix": a specific, actionable suggested correction - for review, not to be executed automatically
- "source_ids": an array of the "id" values (from the retrieved snippets) that actually support your answer
- "needs_more_info": true or false
- "clarifying_question": if needs_more_info is true, a specific question about what's missing; otherwise null

If the provided details are too sparse to give a confident diagnosis (e.g. no error message, no endpoint), set
needs_more_info to true and ask a specific clarifying question instead of guessing. Do not invent details that
weren't provided or supported by the retrieved snippets.

Respond with ONLY the JSON object, no other text."""


class LlmError(Exception):
    pass


async def explain(
    method: str,
    endpoint: str,
    status_code: str,
    error_message: str,
    request_body: str | None,
    response_body: str | None,
    retrieved_docs: list[dict],
) -> tuple[dict, float]:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise LlmError("OPENAI_API_KEY is not configured on the server.")

    docs_block = "\n\n".join(
        f"[id: {d['id']}] (category {d['category']}, relevance {d['score']:.2f})\n{d['text']}"
        for d in retrieved_docs
    ) or "(no relevant documentation was retrieved)"

    user_prompt = f"""Failed request:
- Method: {method}
- Endpoint: {endpoint}
- Status code: {status_code}
- Error message: {error_message or "(not provided)"}
- Request body: {request_body or "(not provided)"}
- Response body: {response_body or "(not provided)"}

Retrieved documentation:
{docs_block}"""

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.2,
    }

    start = time.perf_counter()
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            OPENAI_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
    ai_ms = (time.perf_counter() - start) * 1000

    if resp.status_code != 200:
        raise LlmError(f"OpenAI returned {resp.status_code}: {resp.text[:500]}")

    data = resp.json()
    try:
        content = data["choices"][0]["message"]["content"]
        parsed = json.loads(content)
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        raise LlmError(f"Could not parse OpenAI response: {e}") from e

    return parsed, ai_ms
