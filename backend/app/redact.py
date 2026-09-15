"""Strips credentials out of pasted request/response data before anything is sent to
Moss or the LLM. Runs on raw text (headers, bodies) rather than requiring a fully
parsed/valid structure, since users paste messy real-world data.
"""

import re

_HEADER_PATTERNS = [
    re.compile(r"(?im)^(authorization)\s*:\s*.+$"),
    re.compile(r"(?im)^(x-api-key)\s*:\s*.+$"),
    re.compile(r"(?im)^(api-key)\s*:\s*.+$"),
    re.compile(r"(?im)^(cookie)\s*:\s*.+$"),
    re.compile(r"(?im)^(set-cookie)\s*:\s*.+$"),
    re.compile(r"(?im)^(proxy-authorization)\s*:\s*.+$"),
]

_JSON_FIELD_PATTERNS = [
    re.compile(r'(?i)("(?:password|passwd|pwd)"\s*:\s*)"[^"]*"'),
    re.compile(r'(?i)("(?:api[_-]?key|apikey)"\s*:\s*)"[^"]*"'),
    re.compile(r'(?i)("(?:access[_-]?token|refresh[_-]?token|auth[_-]?token|token)"\s*:\s*)"[^"]*"'),
    re.compile(r'(?i)("(?:secret|client[_-]?secret)"\s*:\s*)"[^"]*"'),
]

_INLINE_TOKEN_PATTERNS = [
    # Bearer/Basic scheme values wherever they appear, not just on a header line
    re.compile(r"(?i)\b(Bearer|Basic)\s+[A-Za-z0-9\-._~+/]+=*"),
    # Common vendor key prefixes (OpenAI, Stripe, AWS, etc.)
    re.compile(r"\b(sk-[A-Za-z0-9]{10,}|sk-proj-[A-Za-z0-9_-]{10,}|AKIA[0-9A-Z]{16})\b"),
]

_REDACTED = "[REDACTED]"


def redact(text: str | None) -> str | None:
    """Best-effort redaction of headers, JSON secret fields, and inline tokens.

    Not a guarantee of perfect coverage - it's a safety net over free-text paste,
    not a substitute for the user avoiding real production secrets in a demo.
    """
    if not text:
        return text

    result = text
    for pattern in _HEADER_PATTERNS:
        result = pattern.sub(lambda m: f"{m.group(1)}: {_REDACTED}", result)
    for pattern in _JSON_FIELD_PATTERNS:
        result = pattern.sub(lambda m: f'{m.group(1)}"{_REDACTED}"', result)
    for pattern in _INLINE_TOKEN_PATTERNS:
        result = pattern.sub(_REDACTED, result)

    return result


def redact_all(*texts: str | None) -> list[str | None]:
    return [redact(t) for t in texts]
