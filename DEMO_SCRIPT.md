# ReqBro Assist — 2-minute judging demo

## 0:00–0:15 — Hook

“A status code is not a diagnosis. ReqBro Assist helps developers understand
failed API requests, but refuses to guess when the evidence is weak.”

Show the product headline and the **Why Moss matters** strip.

## 0:15–0:35 — Architecture

“Sensitive values receive best-effort redaction first. Moss retrieves the most
relevant troubleshooting evidence. A deterministic gate checks that the note is
trusted and that the observed error contains a matching signal. Only then does
OpenAI explain the failure.”

## 0:35–1:10 — Grounded real case

Click **401 GitHub auth missing**, then **Analyze with ReqBro Assist**.

“This is a reproducible response from GitHub’s public user endpoint without an
Authorization header. ReqBro identifies the missing header, cites the exact
supporting note and exposes every stage and timing. Moss retrieval finishes in
milliseconds; the model is the slower stage.”

Show **GROUNDED**, the cited source and the evidence trace.

## 1:10–1:35 — Honest abstention

Click **500 vague server error**, then analyze.

“A generic 500 cannot prove one root cause. Here the evidence gate withholds the
diagnosis and skips OpenAI entirely. The result returns in milliseconds without
spending model tokens or inventing a fix.”

Show **ABSTAINED**, `AI 0ms`, and `diagnosis withheld`.

## 1:35–1:50 — Safety

“ReqBro never calls the submitted endpoint, never applies fixes automatically,
rejects changed retrieval text, validates model citations and has no application
database for submitted bodies.”

## 1:50–2:00 — Close

“ReqBro makes Moss the trust and speed layer in front of AI: retrieve fast,
verify locally, and answer only when the evidence supports it.”

