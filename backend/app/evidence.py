"""Conservative demo evidence gate, not proof of diagnostic correctness."""
import re
from .data.docs import DOCS

CATALOG = {d['id']: d for d in DOCS}
SOURCE_URL = 'https://github.com/Madhuri-4596/reqbro-assist/blob/main/backend/app/data/docs.py'
SIGNALS = {
    '401-missing-auth-header': r'missing (?:authorization|auth) header|authorization header.*(?:missing|required)',
    '401-expired-token': r'token.*expir|expir.*token',
    '401-wrong-auth-scheme': r'(?:unsupported|wrong|invalid) (?:authentication|auth) scheme',
    '401-revoked-key': r'(?:revoked|invalid)[ _-](?:api[ _-])?key',
    '403-insufficient-scope': r'insufficient[ _-](?:scope|permission)|required_scope',
    '403-resource-ownership': r'not (?:the )?owner|ownership',
    '403-plan-tier-restriction': r'(?:plan|tier).*(?:required|restricted|upgrade)|upgrade.*(?:plan|tier)',
    '400-missing-required-field': r'field.*required|required field|missing.*field',
    '400-wrong-data-type': r'(?:expected|must be).*(?:integer|number|array|boolean|string)',
    '400-malformed-json': r'(?:malformed|invalid) json|json.*(?:parse|syntax)',
    '422-invalid-enum-value': r'enum|must be one of|allowed values',
    '400-query-vs-body-param': r'missing.*(?:query|path).*param',
    '429-rate-limit-exceeded': r'retry-after|rate.?limit|too many requests',
    '429-burst-vs-sustained': r'burst.*limit',
    '429-concurrent-request-limit': r'concurrent.*limit|too many concurrent',
    '500-upstream-timeout': r'upstream.*tim(?:e|ed)[ -]?out|database.*tim(?:e|ed)[ -]?out',
    '500-unhandled-exception': r'unhandled exception|traceback',
}


def trusted_docs(docs):
    # An ID alone cannot authenticate retrieved text. Only this version's exact
    # curated text can enter the model. Others remain visible as untrusted.
    return [d for d in docs if d.get('id') in CATALOG
            and d.get('text') == CATALOG[d['id']]['text']]


def matching_docs(docs, status, error, response):
    signal = (error or '') + '\n' + (response or '')
    categories = {'400', '422'} if status in {'400', '422'} else {status}
    return [d for d in trusted_docs(docs)
            if CATALOG[d['id']]['category'] in categories
            and d['id'] in SIGNALS and re.search(SIGNALS[d['id']], signal, re.I)]


def fallback(sparse=False):
    return dict(meaning='The supplied information does not establish a specific cause.',
                likely_cause='Not established from the available evidence.',
                what_to_check=['Inspect the redacted response and the API-specific documentation.'],
                suggested_fix='No specific fix can be supported yet.', source_ids=[],
                needs_more_info=sparse, insufficient_evidence=not sparse,
                clarifying_question='What error message or response details did the API return?' if sparse else None)
