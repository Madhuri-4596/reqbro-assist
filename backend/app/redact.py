"""Best-effort credential removal; not a guarantee for arbitrary free text."""
import json
import re
from urllib.parse import unquote

REDACTED = '[REDACTED]'
KEY = r'(?:authorization|proxy[-_]?authorization|cookie|set[-_]?cookie|x[-_]?api[-_]?key|api[-_]?key|password|passwd|pwd|(?:access|refresh|auth|id)[-_]?token|token|secret|client[-_]?secret|credential|signature|sig|x-amz-signature|x-amz-credential|x-amz-security-token)'
SENSITIVE = re.compile(rf'^{KEY}$', re.I)
HEADERS = re.compile(rf'(?im)^([ \t]*{KEY}[ \t]*:)[^\r\n]*')
PAIRS = re.compile(rf'''(?i)(["']?{KEY}["']?\s*[:=]\s*)("(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|[^&\s,;}}]+)''')
SCHEMES = re.compile(r'(?i)\b(?:Bearer|Basic)\s+[A-Za-z0-9._~+/=-]+')
KEYS = re.compile(r'\b(?:sk-(?:proj-)?[A-Za-z0-9_-]{10,}|AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9]{10,})\b')
USERINFO = re.compile(r'(?i)(https?://)[^/\s?#]+@')

def _clean_text(text):
    text = USERINFO.sub(r'\1[REDACTED]@', text)
    text = HEADERS.sub(lambda m: m[1] + ' ' + REDACTED, text)
    text = PAIRS.sub(lambda m: m[1] + REDACTED, text)
    text = SCHEMES.sub(REDACTED, text)
    return KEYS.sub(REDACTED, text)

def _clean_json(value):
    if isinstance(value, dict):
        return {k: REDACTED if SENSITIVE.fullmatch(unquote(k)) else _clean_json(v) for k,v in value.items()}
    if isinstance(value, list):
        return [_clean_json(v) for v in value]
    if isinstance(value, str):
        return _clean_text(value)
    return value

def redact(text: str | None) -> str | None:
    if not text:
        return text
    for _ in range(2):
        decoded = unquote(text)
        if decoded == text:
            break
        text = decoded
    try:
        value = json.loads(text)
    except (ValueError, RecursionError):
        return _clean_text(text)
    return json.dumps(_clean_json(value), ensure_ascii=False)

def redact_all(*texts: str | None) -> list[str | None]:
    return [redact(t) for t in texts]
