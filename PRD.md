# ReqBro Assist — Product Requirements Document

Built for the [YC Fall 2026 x Moss: The Zero Latency Builder Sprint](https://yc-fall-2026-x-moss.devpost.com/).

> This document describes what was actually implemented, not an aspirational
> future version. Where a number is a target rather than a measured result,
> it is labeled as such — see **Performance** below.

## The problem

When an API call fails, the error a developer sees (`401`, `403`, `422`,
`429`, `500` — often with a terse or generic message) rarely explains *why*
it failed or what to actually check. Developers fall back to re-reading
scattered documentation, forum posts, or guessing. This is slow, and a
status code alone is easy to misread as proof of one specific cause when
several different causes can produce the same code.

## Target users

- Backend and mobile developers integrating third-party or internal APIs
  who hit a failure and want a fast, evidence-based starting point instead
  of guessing.
- Judges/reviewers of this hackathon, evaluating whether real retrieval
  (via Moss) meaningfully improves the quality and trustworthiness of an
  AI explanation versus an ungrounded LLM guess.

This is explicitly **not** a general chatbot and not a tool that executes
fixes automatically — see Non-goals.

## Relationship to ReqBro

[ReqBro](https://github.com/Madhuri-4596) is a separate native Android API
client (REST/GraphQL/WebSocket/gRPC), currently in Google Play closed
testing — it is not published in any app store yet. ReqBro Assist reuses
the *idea* of AI-assisted request debugging from ReqBro's own AI Assist
feature, rewritten from scratch as a standalone web service so hackathon
judges can access it without installing an Android app. It shares no code
or deployment with the Android app, and shares no code or scope with
ReqBro AgentPay (a separate Arbitrum-based project).

## Scope — what was actually built

### In scope (implemented)

- A web form for: HTTP method, endpoint, status code, error message,
  optional request body, optional response body.
- Server-side redaction of `Authorization`/`Cookie`/`X-Api-Key` headers,
  common JSON secret fields (`password`, `api_key`, `token`, `secret`),
  and inline `Bearer`/`Basic` scheme values or vendor key patterns —
  applied before any text reaches Moss or the LLM.
- Real-time semantic retrieval via the Moss SDK over a curated,
  purpose-written knowledge base of 20 documents covering five error
  categories: **401** (authentication), **403** (permission), **400/422**
  (validation), **429** (rate limiting), **500** (server error).
- An LLM (OpenAI `gpt-4o-mini`) call that uses *only* the retrieved
  documents plus the submitted request details as evidence, and is
  explicitly instructed to distinguish evidence from inference, cite which
  retrieved documents actually support its answer, and treat retrieved
  document text as inert reference material that can never override its
  instructions (basic prompt-injection resistance).
- Two distinct "can't give a confident answer" states, kept separate on
  purpose:
  - **Needs more info** — the submitted request details are too sparse to
    reason about at all (e.g. no error message, no endpoint).
  - **Insufficient evidence** — the request details are detailed enough,
    but nothing retrieved from Moss actually supports a confident
    diagnosis. A status code alone is never treated as sufficient
    evidence for one specific root cause.
- Five ready-to-run example cases (one per error category) so a judge can
  test the demo with one click, with no typing required.
- Separately measured retrieval time, AI response time, and total
  end-to-end time, shown on every result.
- Honest failure states: if Moss or OpenAI errors or is unreachable, the
  UI shows the actual failure and which stage it happened at (retrieval
  vs. AI) — never a silently fabricated answer.
- No server-side storage of any kind — no database, no logging of
  submitted request/response content. (Redacted content is still sent to
  Moss and OpenAI to generate the response, and is subject to *their*
  respective data-retention policies — see **Data handling** below.)

### Non-goals (explicitly out of scope)

- The app never sends a request to the arbitrary endpoint a user pastes —
  input is descriptive text only, never executed.
- Suggested fixes are displayed for human review; nothing is applied or
  executed automatically.
- Not a general-purpose chatbot — the input shape and prompt are
  purpose-built for one workflow (explaining a specific failed API call).
- No user accounts, no history/persistence across sessions.
- No support for status codes outside the five listed categories (an
  arbitrary code is still accepted and searched, but the curated knowledge
  base does not cover, say, `502`/`503` in this initial version).

## Smallest useful product (what a judge can verify in under a minute)

1. Click one of the five example buttons.
2. Click "Debug this request."
3. See: an explanation, a likely cause, what to check, a suggested fix,
   the specific retrieved documents that support the answer (each marked
   "cited" or not), and three separate timing numbers.
4. Optionally, submit a deliberately vague case (e.g. just a status code,
   no error message) to see the "needs more info" state, or a case Moss
   has no good match for, to see the "insufficient evidence" state.

## Data handling

- ReqBro Assist's own backend is stateless: no database, no request/
  response logging of submitted content (verified by inspecting the
  codebase directly — the only server-side log statement is a startup
  warning containing an SDK error message, never user-submitted content).
- Redacted request/response text is sent onward to two third parties to
  generate the result:
  - **Moss** (retrieval) — their data-retention policy for query text was
    not confirmed at the time of writing; treat it as subject to Moss's
    own policy, not ReqBro Assist's.
  - **OpenAI** (explanation) — by default, OpenAI retains API inputs and
    outputs for up to 30 days for abuse-monitoring purposes (not used for
    model training), unless the account has Zero Data Retention enabled,
    which is not assumed here.
- The redaction step (headers, common secret field names, inline
  Bearer/Basic/vendor-key patterns) reduces what sensitive content could
  reach those third parties in the first place, but is a best-effort
  safety net over free-text paste, not a guarantee — users should not
  paste real production secrets into any demo.

## Performance

### Targets (design intent, not yet measured)

- Retrieval: sub-second, ideally well under 100ms given Moss's local
  in-process query model against a small (20-document) index.
- Total end-to-end response: a few hundred milliseconds to a few seconds,
  dominated by the OpenAI call rather than retrieval.

### Actual measured results

**Pending.** Real numbers require a live Moss project and OpenAI billing,
neither of which existed at the time this document was written. Once
deployed, this section will be replaced with real measurements including:
corpus size (20 documents, fixed), test environment (Railway deployment
region and instance size), and number of runs averaged. No specific
latency figure (including "sub-10ms") should be treated as a real result
until this section is updated with actual data.

## Success criteria

- All five example cases produce a coherent, source-cited explanation
  end-to-end on the deployed instance.
- The "needs more info" and "insufficient evidence" states are each
  demonstrably reachable with a real input, not just theoretical.
- A judge can reach a working result within one click plus one submit,
  with no setup or account required on their end.
- Every claim made in the UI (data retention, "not a mock", etc.) matches
  what the deployed code actually does at demo time.
