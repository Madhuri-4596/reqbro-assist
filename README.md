# ReqBro Assist

An AI debugging assistant for failed API requests. Paste a method, endpoint, status
code, and error (plus optional request/response bodies) and get: what the error
means, the likely cause, what to check, a suggested fix, and the documentation it
was based on — with real retrieval and AI latency shown.

Built for the [YC Fall 2026 x Moss: The Zero Latency Builder Sprint](https://yc-fall-2026-x-moss.devpost.com/).

This is a separate project from ReqBro (the Android API client) — it
reuses the idea of AI-assisted request debugging, rewritten as a standalone web
service so judges can access it without installing an app.

## How it works

1. Sensitive fields (Authorization headers, API keys, passwords, tokens) are
   redacted on a best-effort basis from the endpoint and pasted text before provider calls.
   Use synthetic examples: this does not remove all possible private data.
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

- A [Moss](https://moss.dev) project with access to the SDK and index. Check your account
  for current quotas and charges; no tier or credit balance is assumed.
- An [OpenAI](https://platform.openai.com) account with billing enabled (this app
  uses `gpt-4o-mini`; check current account pricing and set a usage budget).

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

To deploy on [Railway](https://railway.app) (deployment not yet verified):

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

## Verification and limitations

Run the credential-free regression suite from `backend`:

```bash
python -m unittest discover -s tests -v
```

17 tests cover credential formats, endpoint redaction before both providers,
validation limits, forged retrieved text, sparse/no-match inputs, source links,
conflicting abstentions, invalid model JSON and sanitized provider errors.
Provider requests are mocked: passing tests do not establish live retrieval,
model quality, injection-proof behavior or actual latency. Real credentials,
index seeding and an end-to-end deployment test are still required.

The server requires an error/response signal matching a curated pattern before
asking the model for a diagnosis. It excludes changed or unknown retrieved text
from model input, checks the output schema and citation IDs, and suppresses answers
without supporting citations. This conservative gate may abstain on valid cases;
matched keywords do not prove causality or defeat every prompt injection.
All retrieved notes remain visible. A "model cited" badge records the model's
reference, not independent verification of every claim. Source links point to
this repository's authored notes, not external API-provider documentation.

No user-requested endpoint is fetched and no suggested fix is executed. The
application does not intentionally persist request bodies. Hosting logs and
provider retention are separate; redaction cannot guarantee removal of arbitrary
personal information. `/api/health` is process liveness, not proof that providers
are ready. An AI timing of 0 means the evidence gate skipped the model.
