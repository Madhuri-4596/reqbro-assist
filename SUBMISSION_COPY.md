# Submission copy

## One-line pitch

ReqBro Assist uses Moss as a millisecond evidence layer that lets AI diagnose
API failures only when retrieved documentation and the observed error agree.

## Short description

API errors are ambiguous, and generic AI assistants often jump from a status
code to a confident fix. ReqBro Assist redacts common secrets, retrieves curated
troubleshooting evidence with Moss, verifies the integrity and signal match of
that evidence, and then asks OpenAI for a citation-backed explanation. If no
source supports the diagnosis, it abstains and skips the model call.

## What makes it different

- Moss is part of the decision path, not a decorative search box.
- A deterministic gate blocks unsupported or altered retrieval content.
- Every retrieved source remains visible; cited and uncited evidence are
  distinguished honestly.
- Vague failures produce an abstention instead of a fabricated root cause.
- The UI exposes retrieval, model and end-to-end latency separately.
- The submitted endpoint is never called and suggested fixes are never applied.

## Verified proof points

- Real public GitHub 401 case: one supporting citation from five trusted Moss
  results, with a grounded diagnosis.
- Vague 500 case: diagnosis withheld, OpenAI skipped, result returned in about
  9 ms in one observed run.
- Nineteen curated troubleshooting notes.
- Seventeen credential-free safety regression tests passing.
- No application database retention.

## Links

- Live application: https://reqbro-assist-production.up.railway.app
- Repository: https://github.com/Madhuri-4596/reqbro-assist
- PRD: `PRD.md`
- Architecture: `ARCHITECTURE.md`
- Evidence: `SUBMISSION_EVIDENCE.md`

