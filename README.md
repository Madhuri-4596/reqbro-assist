# ReqBro Assist

An AI debugging assistant for failed API requests. Paste a method, endpoint, status
code, and error (plus optional request/response bodies) and get: what the error
means, the likely cause, what to check, a suggested fix, and the documentation it
was based on — with real retrieval and AI latency shown.

Built for the [YC Fall 2026 x Moss: The Zero Latency Builder Sprint](https://yc-fall-2026-x-moss.devpost.com/).

This is a separate project from [ReqBro](../ReqBro) (the Android API client) — it
reuses the idea of AI-assisted request debugging, rewritten as a standalone web
service so judges can access it without installing an app.

## How it works

1. Sensitive fields (Authorization headers, API keys, passwords, tokens) are
   stripped from pasted text server-side before anything else happens.
2. The redacted error details are used to query a [Moss](https://docs.moss.dev/)
   index of curated API-troubleshooting documentation (semantic search, no
   traditional vector database).
3. The retrieved documentation + error details are sent to an LLM (OpenAI
   `gpt-4o-mini`), which explains the error, cites which retrieved docs it used,
   and asks a clarifying question instead of guessing if the details given are too
   sparse.
4. The UI shows the explanation, the cited sources, and three separately measured
   timings: Moss retrieval time, AI response time, and total request time.

## Setup

### 1. Accounts you need

- A [Moss](https://moss.dev) account — free tier ($5/month credit) is enough for
  this demo's dataset size (~20 documents).
- An [OpenAI](https://platform.openai.com) account with billing enabled (this app
  uses `gpt-4o-mini`, which costs fractions of a cent per request).

### 2. Install

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
```

### 3. Configure

```bash
cp .env.example .env
# then edit .env with your real MOSS_PROJECT_ID, MOSS_PROJECT_KEY, OPENAI_API_KEY
```

### 4. Seed the Moss index (one-time, re-run if `app/data/docs.py` changes)

```bash
python -m scripts.seed_index
```

### 5. Run locally

```bash
uvicorn app.main:app --reload
```

Open http://localhost:8000 — click one of the example buttons and hit "Debug
this."

## Deployment

Deployed on [Railway](https://railway.app):

1. Push this repo to GitHub.
2. Create a new Railway project from the GitHub repo, root directory `backend`.
3. Set `MOSS_PROJECT_ID`, `MOSS_PROJECT_KEY`, `OPENAI_API_KEY` as environment
   variables in the Railway dashboard (never commit real values).
4. Railway uses the included `Procfile` to run
   `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
5. Run `python -m scripts.seed_index` once (locally, pointed at the same Moss
   project) to populate the index the deployed app will query.

## Project structure

```
backend/
  app/
    main.py          FastAPI app, /api/debug endpoint
    models.py         Request/response schemas
    redact.py          Sensitive-data stripping
    moss_client.py     Moss SDK wrapper, retrieval timing
    llm.py              OpenAI call, explanation prompt
    data/docs.py         Curated troubleshooting knowledge base
    static/               Frontend (index.html, app.js, examples.js)
  scripts/seed_index.py  One-time Moss index seeding script
```

## Scope

Covers five error categories with curated documentation and ready-to-run examples:
401 (authentication), 403 (permission), 400/422 (validation), 429 (rate limiting),
500 (server error). When the pasted details are too sparse for a confident
diagnosis, the assistant asks a clarifying question instead of guessing.

## Testing performed

- Correct-answer cases for each of the five status code categories (see example
  buttons in the UI).
- Missing-information case (sparse input triggers a clarifying question, not a
  fabricated diagnosis).
- Sensitive-data redaction (Authorization headers, API keys, passwords, bearer
  tokens stripped before reaching Moss or the LLM — verified by inspecting the
  redacted text server-side).
- Service failure states (Moss or OpenAI unavailable/misconfigured surfaces an
  honest error message in the UI, not a silent failure or fabricated result).
