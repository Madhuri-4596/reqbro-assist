"""Curated API troubleshooting knowledge base, seeded into a Moss index.

Each entry is a focused, single-cause chunk rather than a broad essay - retrieval
works better against narrow, specific documents than one long FAQ page.
"""

DOCS = [
    # --- 401: authentication failure ---
    {
        "id": "401-missing-auth-header",
        "category": "401",
        "text": (
            "401 Unauthorized: Missing Authorization header. The request was sent without an "
            "Authorization header at all, or the client stripped it before sending (common with "
            "browser fetch() calls that don't include credentials, or proxies that drop custom "
            "headers). Fix: confirm the header is actually present in the outgoing request "
            "(check with a network inspector, not just the code that sets it), and that the "
            "client isn't following a redirect that drops the header."
        ),
    },
    {
        "id": "401-expired-token",
        "category": "401",
        "text": (
            "401 Unauthorized: Expired access token. JWTs and OAuth access tokens carry an "
            "expiry (exp claim / expires_in). If the token was issued more than its TTL ago "
            "(often 15-60 minutes for access tokens), the server correctly rejects it. Fix: "
            "implement token refresh using the refresh token before the access token expires, "
            "or catch 401 and retry once after refreshing. Decode the JWT payload (base64) to "
            "check the exp timestamp directly if unsure."
        ),
    },
    {
        "id": "401-wrong-auth-scheme",
        "category": "401",
        "text": (
            "401 Unauthorized: Wrong authentication scheme. APIs differ in whether they expect "
            "'Authorization: Bearer <token>', 'Authorization: Basic <base64>', or a custom "
            "header like 'X-Api-Key: <key>'. Sending a raw API key as 'Authorization: <key>' "
            "without the 'Bearer' prefix is a very common mistake. Fix: check the API's docs for "
            "the exact expected header name and scheme prefix, not just where the credential goes."
        ),
    },
    {
        "id": "401-revoked-key",
        "category": "401",
        "text": (
            "401 Unauthorized: Invalid or revoked API key. The key may have been rotated, "
            "deleted, or belongs to a different environment (e.g. a test key used against a "
            "production endpoint, or vice versa). Fix: regenerate the key from the provider's "
            "dashboard and confirm it matches the target environment's base URL."
        ),
    },
    # --- 403: permission failure ---
    {
        "id": "403-insufficient-scope",
        "category": "403",
        "text": (
            "403 Forbidden: Authenticated but insufficient scope/permissions. Unlike 401, the "
            "credential is valid, but it doesn't grant access to this specific action or "
            "resource. Common with OAuth scopes (e.g. a token with 'read' scope hitting a "
            "'write' endpoint) or role-based permissions. Fix: check what scopes/roles the "
            "endpoint requires versus what the token/user actually has, and re-authorize with "
            "the correct scope if needed."
        ),
    },
    {
        "id": "403-resource-ownership",
        "category": "403",
        "text": (
            "403 Forbidden: Resource-level ownership check failing. The user is valid and has "
            "general API access, but is trying to access, modify, or delete a resource (e.g. "
            "another user's record) they don't own. This is often intentional server-side "
            "protection, not a bug. Fix: confirm the resource ID in the request actually "
            "belongs to the authenticated user/account."
        ),
    },
    {
        "id": "403-plan-tier-restriction",
        "category": "403",
        "text": (
            "403 Forbidden: Endpoint not included in current plan/tier. Some APIs gate specific "
            "endpoints or features behind a paid plan or enterprise tier, returning 403 for "
            "otherwise-valid, correctly-scoped requests. Fix: check the API provider's pricing/"
            "plan documentation for which tier the endpoint requires."
        ),
    },
    # --- 400/422: invalid request or validation ---
    {
        "id": "400-missing-required-field",
        "category": "400",
        "text": (
            "400/422: Missing required field in request body. The error message usually names "
            "the missing field directly (e.g. 'email is required'). Fix: compare the request "
            "body against the endpoint's documented schema field-by-field, checking for typos "
            "in field names as well as fields left out entirely."
        ),
    },
    {
        "id": "400-wrong-data-type",
        "category": "400",
        "text": (
            "400/422: Wrong data type for a field. Sending a string where a number is expected "
            "(e.g. '\"20\"' instead of 20), or a single value where an array is expected, is a "
            "frequent validation failure. Fix: check the field's expected JSON type in the "
            "schema, not just that a value was provided."
        ),
    },
    {
        "id": "400-malformed-json",
        "category": "400",
        "text": (
            "400: Malformed JSON body. Trailing commas, unescaped quotes inside string values, "
            "or a body that isn't valid JSON at all (e.g. accidentally sending form-encoded data "
            "with a JSON Content-Type header) will fail before the server even validates field "
            "content. Fix: validate the raw request body through a JSON linter/parser before "
            "sending, and confirm Content-Type matches the actual body format."
        ),
    },
    {
        "id": "422-invalid-enum-value",
        "category": "422",
        "text": (
            "422 Unprocessable Entity: Value outside the allowed set (enum). The field exists "
            "and has the right type, but its value isn't one of the API's accepted options "
            "(e.g. sending status='completed' when only 'pending'/'done'/'cancelled' are valid). "
            "Fix: check the endpoint's documented enum values exactly, including case-sensitivity."
        ),
    },
    {
        "id": "400-query-vs-body-param",
        "category": "400",
        "text": (
            "400: Parameter sent in the wrong place. A value that belongs in the URL query "
            "string was put in the JSON body, or vice versa. This produces a 'missing "
            "parameter' error even though the value was technically sent somewhere in the "
            "request. Fix: check the endpoint's docs for whether each parameter is a path "
            "param, query param, or body field."
        ),
    },
    # --- 429: rate limiting ---
    {
        "id": "429-rate-limit-exceeded",
        "category": "429",
        "text": (
            "429 Too Many Requests: Rate limit exceeded. Most APIs enforce a per-key or "
            "per-IP request budget over a time window. Fix: check the response for a "
            "'Retry-After' header or rate-limit headers (X-RateLimit-Remaining, "
            "X-RateLimit-Reset) and back off accordingly; implement exponential backoff with "
            "jitter rather than immediate retry."
        ),
    },
    {
        "id": "429-burst-vs-sustained",
        "category": "429",
        "text": (
            "429: Burst limit hit even though average request rate looks fine. Many APIs "
            "enforce both a short burst limit (e.g. 10 requests/second) and a longer sustained "
            "limit (e.g. 1000/hour) separately. A tight loop of parallel requests can trip the "
            "burst limit while staying well under the hourly quota. Fix: add a small delay or "
            "concurrency cap between requests instead of firing them all at once."
        ),
    },
    {
        "id": "429-concurrent-request-limit",
        "category": "429",
        "text": (
            "429: Concurrent request limit exceeded. Separate from a time-window rate limit, "
            "some APIs cap how many requests can be in-flight simultaneously per key. Fix: "
            "use a semaphore/connection pool to cap concurrent outgoing requests to that API, "
            "rather than relying only on rate-limit headers."
        ),
    },
    # --- 500: server error requiring further investigation ---
    {
        "id": "500-upstream-timeout",
        "category": "500",
        "text": (
            "500 Internal Server Error: Often caused by an upstream dependency (database, "
            "third-party API, internal microservice) timing out or erroring, which the server "
            "fails to handle gracefully. From the client side, this looks identical to any "
            "other 500. Fix: retry with backoff since it may be transient; if it persists "
            "across retries, this needs server-side log investigation rather than a client fix."
        ),
    },
    {
        "id": "500-unhandled-exception",
        "category": "500",
        "text": (
            "500 Internal Server Error: Unhandled exception from edge-case input. Input that "
            "passes basic validation (right types, required fields present) can still trigger "
            "a server-side bug with certain values (e.g. an empty array where the code expects "
            "at least one item, or a date far in the past/future). Fix: try simplifying the "
            "request to a minimal known-good payload, then reintroduce fields one at a time to "
            "isolate which value triggers the failure."
        ),
    },
    {
        "id": "500-transient-retry",
        "category": "500",
        "text": (
            "500: Transient server error. Some 500s are momentary (deploy in progress, brief "
            "resource exhaustion) and resolve on retry. Fix: retry once or twice with a short "
            "delay before treating it as a persistent failure worth escalating."
        ),
    },
    {
        "id": "500-insufficient-info",
        "category": "500",
        "text": (
            "500: Insufficient information to diagnose from the client side alone. A generic "
            "500 with no error body or trace ID doesn't reveal the server-side cause. This is a "
            "case where the honest next step is to check the API provider's status page, look "
            "for a request/trace ID to include in a support ticket, or contact their support "
            "rather than guessing at a client-side fix that may not exist."
        ),
    },
]
