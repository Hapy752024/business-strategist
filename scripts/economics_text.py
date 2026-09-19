"""Bind model-derived claims in current prose to explicit arithmetic references.

This checks marked claims, not the truth of arbitrary natural language. Historical
observations remain ordinary cited prose; model claims use {{economics.…}} tokens.
"""
import re

TOKEN = re.compile(r'\{\{economics\.([a-zA-Z0-9_.]+)\}\}')
FINANCIAL = re.compile(r'\b(contribution|break.?even|required (?:monthly )?sales|capacity (?:target|limit)|(?:our|venture|model|calculated|projected|expected) (?:revenue|cost|cash|sales|profit)|monthly (?:revenue|cost|cash|profit))\b', re.I)


def render(text, record, authored_digest=None):
    if not record:
        if TOKEN.search(text):
            raise ValueError('economics references require a model')
        return text
    # Explicit model claims cannot carry literal amounts from an older draft.
    for block in re.split(r'\n\s*\n|(?<=[.!?])\s+', text):
        plain = re.sub(r'\[[^\]]*\]\([^)]*\)', 'CITED', TOKEN.sub('BOUND', block))
        plain = re.sub(r'^\s*\d+[.)]\s*', '', plain, flags=re.M)
        if FINANCIAL.search(plain) and re.search(r'\d', plain):
            raise ValueError('model-derived numerical claims require economics placeholders')
    if (TOKEN.search(text) or FINANCIAL.search(text)) and authored_digest != record['input_digest']:
        raise ValueError('stale or missing authored economics input digest')

    def value(match):
        parts = match[1].split('.')
        if parts[0] not in {'inputs', 'results'} or 'provenance' in parts:
            raise ValueError('unsupported economics reference')
        item = record
        try:
            for part in parts:
                item = item[int(part)] if isinstance(item, list) and part.isdigit() else item[part]
        except (KeyError, IndexError, TypeError):
            raise ValueError('unknown economics reference: ' + match[1]) from None
        if isinstance(item, (dict, list)) or not isinstance(item, (int, float, bool, type(None))):
            raise ValueError('economics references must resolve to numeric results or unknowns')
        return 'unresolved' if item is None else str(item).lower() if isinstance(item, bool) else str(item)
    return TOKEN.sub(value, text)
