# ReqBro Assist — Architecture

## System diagram

```mermaid
flowchart TB
    subgraph Client["Browser (judge/user)"]
        UI["Single-page UI<br/>index.html + app.js<br/><i>no framework, no build step</i>"]
    end

    subgraph Server["FastAPI backend (one Railway service)"]
        API["/api/debug<br/>(POST)"]
        Redact["redact.py<br/>strips Authorization/Cookie/API-key headers,<br/>password/token/secret JSON fields,<br/>Bearer/Basic/vendor-key patterns"]
        MossClient["moss_client.py<br/>wraps MossClient.query()<br/>times retrieval only"]
        LLM["llm.py<br/>OpenAI gpt-4o-mini call<br/>times AI generation only"]
    end

    subgraph MossCloud["Moss (usemoss.dev)"]
        Index["api-troubleshooting index<br/>20 curated documents<br/>401 / 403 / 400+422 / 429 / 500<br/><b>loaded into the FastAPI process<br/>at startup - queries run locally,<br/>not as a cloud round-trip per query</b>"]
    end

    subgraph OpenAICloud["OpenAI API"]
        Model["gpt-4o-mini<br/>chat completion,<br/>JSON-structured response"]
    end

    UI -- "1. POST method, endpoint,<br/>status, error, bodies" --> API
    API -- "2." --> Redact
    Redact -- "3. redacted text" --> MossClient
    MossClient -- "4. semantic query" --> Index
    Index -- "5. top-k docs + relevance scores" --> MossClient
    MossClient -- "6. retrieved docs" --> LLM
    LLM -- "7. explanation prompt +<br/>retrieved docs as evidence" --> Model
    Model -- "8. structured JSON:<br/>meaning, cause, checks,<br/>fix, cited source ids,<br/>needs_more_info /<br/>insufficient_evidence" --> LLM
    LLM -- "9. explanation +<br/>retrieval_ms + ai_ms + total_ms" --> API
    API -- "10. JSON response" --> UI
```

## Where data is stored

**Nowhere, on ReqBro Assist's own infrastructure.** The backend has no
database and no logging of submitted content (the only server-side log
line is a startup-failure warning containing an SDK error message, never
user input — see `app/main.py`). Each request is processed in memory and
discarded once the response is returned.

Redacted request/response text *is* sent onward to two third parties as
part of generating the result, and is subject to their own policies:

- **Moss** — receives the redacted query text to run semantic search.
  Their retention policy for query text was not confirmed as of this
  writing.
- **OpenAI** — receives the redacted request details and retrieved
  document text as the prompt. OpenAI's default API policy retains
  inputs/outputs up to 30 days for abuse monitoring (not for training),
  unless the account has Zero Data Retention enabled.

Sensitive data (`Authorization` headers, API keys, passwords, tokens,
`Bearer`/`Basic` scheme values, common vendor key prefixes) is stripped
**before** step 3 above — before anything reaches either third party.

## Why the index loads at server startup, not per-request

Moss's query model runs the actual vector search **locally, in-process**
against an index that has been loaded into memory — this is what makes
sub-millisecond-scale retrieval possible in principle (no network round
trip per query). This was confirmed directly against the installed SDK
(not assumed from docs): calling `query()` against an index that hasn't
been `load_index()`-ed first raises `Index 'api-troubleshooting' is not
loaded`. Accordingly, the FastAPI app calls `load_index()` once in a
`lifespan` startup hook (`app/main.py`), and the one-time
`scripts/seed_index.py` script is only responsible for *creating* and
populating the index, not for making it queryable by the running server
process.

## Component responsibilities

| File | Responsibility |
|---|---|
| `app/static/index.html`, `app.js`, `examples.js` | UI: form, example buttons, result rendering, loading/error states |
| `app/main.py` | HTTP layer: request validation, orchestrates redact → retrieve → explain, assembles timing, serves the static frontend |
| `app/redact.py` | Strips sensitive data from free-text input before it leaves the process |
| `app/moss_client.py` | Wraps the Moss SDK; isolates retrieval timing from the rest of the request |
| `app/llm.py` | Builds the explanation prompt, calls OpenAI, isolates AI timing, parses the structured JSON result |
| `app/models.py` | Request/response schemas (Pydantic) — also where input validation lives (blank endpoint/status rejected) |
| `app/data/docs.py` | The curated 19-document knowledge base, source of truth for what gets indexed |
| `scripts/seed_index.py` | One-time script to create/populate the Moss index from `docs.py` |

## Deployment topology

One deployable service (FastAPI, serving both the API and the static
frontend from the same origin) on Railway. No separate frontend hosting,
no CORS configuration needed, one URL for judges to visit.


## September 15 hardening update

Endpoint URLs now pass through the same best-effort redaction as error and body
fields. Coverage includes common URL/form credentials, indented headers and
nested JSON secrets; it is not a guarantee for arbitrary sensitive text.

The implemented flow is redaction -> Moss retrieval -> deterministic evidence
gate -> optional model call -> strict schema/citation validation -> result.
The gate requires an explicit error/response signal and an unchanged note from
the checked-in corpus. Sparse inputs, no matches, changed retrieved notes and
uncited answers produce conservative states rather than a specific diagnosis.
These controls reduce risk; they do not establish universal prompt-injection
resistance or independently prove that model prose is correct.

All retrieved notes remain visible with trust/citation labels. Links identify
the repository's curated notes honestly. Provider exceptions are not displayed
verbatim. Request field lengths and method/status values are bounded.

The credential-free regression suite passes 17 tests using provider mocks.
Real provider performance and deployed operation remain unmeasured. The original
example-case checks should not be interpreted as live model or Moss validation.
The UI discloses application behavior separately from hosting/provider policies;
no blanket claim that data is never retained anywhere is made.
