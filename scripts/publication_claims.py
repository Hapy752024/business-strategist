"""Resolve publication markers against the existing reviewed VOC claim ledger.

This is a renderer, not a second evidence authority. The packet supplies IDs and
current file bindings; URL and support are read from the reviewed run artifacts.
"""
from __future__ import annotations

import json
import re
import hashlib
from pathlib import Path

try:
    from scripts import case_workspace as cases
except ModuleNotFoundError:
    import case_workspace as cases

MARKER = re.compile(r"\{\{evidence_claim\.([a-z][a-z0-9_-]*)\}\}")


def bundle_digest(contents: dict[str, str | bytes], bindings: list) -> str:
    """Digest exact rendered outputs and consumed source identities."""
    payload = {'outputs': {key: hashlib.sha256(value if isinstance(value, bytes) else value.encode()).hexdigest()
                           for key, value in sorted(contents.items())},
               'sources': sorted(b['path'] + '#' + b['digest'] for b in bindings)}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def check_numeric_citations(texts: dict[str, str], numeric_claims: list, references: list) -> None:
    """Require a retained primary capture beside each verified observed figure."""
    for claim in numeric_claims:
        if claim.get('status') != 'verified':
            continue
        doc = claim['document']
        body = texts.get(doc, '')
        token = '{{source_numeric.' + claim['id'] + '}}'
        at = body.find(token)
        matches = [ref for ref in references if ref.get('numeric_claim_id') == claim['id']
                   and ref.get('document') == doc and 'capture_binding' in ref]
        if at < 0 or len(matches) != 1:
            raise ValueError(claim['id'] + ': verified numeric claim needs one nearby bound source capture')
        ref = matches[0]
        marker = '{{evidence_claim.' + ref['id'] + '}}'
        cite_at = body.find(marker)
        passage = ref.get('supporting_passage', '')
        if (cite_at < at or cite_at - at > 220 or marker not in body
                or claim['value'] not in passage or claim['period'] not in passage):
            raise ValueError(claim['id'] + ': numeric source marker must follow the figure and retain value and period')


def check_separate_review(root: Path, case_id: str, binding: dict | None,
                          expected_digest: str, sources: list, prefix: str) -> None:
    if not isinstance(binding, dict) or not binding.get('path', '').startswith(prefix):
        raise ValueError('final publication needs a separate case-local review record')
    if binding != cases.source_binding(root, binding['path'], locator=binding['locator'],
                                       applicability=binding['applicability']):
        raise ValueError('separate publication review changed')
    record = cases.load(cases.safe(root, binding['path']))
    expected_sources = sorted(b['path'] + '#' + b['digest'] for b in sources)
    if (not isinstance(record, dict) or set(record) != {'author', 'reviewer', 'review_task_id',
            'bundle_digest', 'reviewed_sources', 'outcome', 'material_findings'}
            or not all(isinstance(record[key], str) and record[key].strip()
                       for key in ('author', 'reviewer', 'review_task_id', 'bundle_digest'))
            or record['author'] == record['reviewer'] or record['bundle_digest'] != expected_digest
            or record['reviewed_sources'] != expected_sources or record['outcome'] != 'pass'
            or record['material_findings']):
        raise ValueError('separate review does not pass the exact rendered publication and inputs')


def render(root: Path, texts: dict[str, str], references: list, bindings: list) -> dict[str, str]:
    """Replace each declared marker with its original source link or safe private reference."""
    if not isinstance(references, list) or not isinstance(bindings, list):
        raise ValueError('publication claims and bindings must be lists')
    root = Path(root).absolute()
    output = dict(texts)
    seen = set()
    for ref in references:
        voc_fields = {'id', 'document', 'claim_id', 'evidence_id', 'ledger_binding', 'source_kind', 'limitation'}
        capture_fields = {'id', 'document', 'capture_binding', 'capture_index', 'supporting_passage',
                          'source_kind', 'limitation'}
        if not isinstance(ref, dict) or set(ref) not in (voc_fields, capture_fields,
                                                        capture_fields | {'numeric_claim_id'}):
            raise ValueError('publication claim needs exact reviewed-source fields')
        ident = ref['id']
        if not isinstance(ident, str) or not re.fullmatch(r'[a-z][a-z0-9_-]*', ident) or ident in seen:
            raise ValueError('publication claim IDs must be unique lowercase identifiers')
        seen.add(ident)
        document = ref['document']
        marker = '{{evidence_claim.' + ident + '}}'
        if document not in output or sum(body.count(marker) for body in output.values()) != 1 or marker not in output[document]:
            raise ValueError(ident + ': marker must appear once in its declared document')
        if set(ref) in (capture_fields, capture_fields | {'numeric_claim_id'}):
            replacement = _render_capture(root, ident, ref, bindings)
            output[document] = output[document].replace(marker, replacement)
            continue
        binding = ref['ledger_binding']
        if binding not in bindings or not binding['path'].endswith('/customer-feedback/claim-ledger.json'):
            raise ValueError(ident + ': reviewed claim ledger must be bound')
        ledger_path = cases.safe(root, binding['path'])
        pack = ledger_path.parent
        siblings = (pack / 'evidence.jsonl', pack / 'source-review.json')
        for path in (ledger_path, *siblings):
            expected = str(path.relative_to(root))
            if not any(b.get('path') == expected and
                       b == cases.source_binding(root, b['path'], locator=b['locator'], applicability=b['applicability'])
                       for b in bindings):
                raise ValueError(ident + ': ledger, evidence and source review need current bindings')
        ledger = json.loads(ledger_path.read_text(encoding='utf-8'))
        claim = next((row for row in ledger if row.get('claim_id') == ref['claim_id']), None)
        if not claim or claim.get('verification', {}).get('support_assessment') != 'supported' or ref['evidence_id'] not in claim.get('supporting_evidence', []):
            raise ValueError(ident + ': claim is not verified as supported by this evidence')
        evidence = {row['evidence_id']: row for line in siblings[0].read_text(encoding='utf-8').splitlines()
                    if line.strip() for row in [json.loads(line)]}
        record = evidence.get(ref['evidence_id'])
        review = json.loads(siblings[1].read_text(encoding='utf-8'))
        reviewed = next((row for row in review.get('reviews', []) if row.get('evidence_id') == ref['evidence_id']), None)
        if not record or not reviewed or reviewed.get('status') != 'accepted' or reviewed.get('source_url') != record.get('source_url'):
            raise ValueError(ident + ': source is missing or was not accepted in source review')
        source_kind = ref['source_kind']
        if source_kind not in {'original', 'secondary', 'private'}:
            raise ValueError(ident + ': source kind must be original, secondary or private')
        limitation = ref['limitation']
        if source_kind == 'secondary' and (not isinstance(limitation, str) or len(limitation.strip()) < 15):
            raise ValueError(ident + ': secondary account needs a visible limitation')
        if source_kind == 'private':
            replacement = '[Reviewed private source: ' + ref['evidence_id'] + ']'
        else:
            url = record.get('source_url')
            if not isinstance(url, str) or not re.fullmatch(r'https?://[^\s)]+', url):
                raise ValueError(ident + ': reviewed source has no usable original URL')
            replacement = '[Source: ' + ref['evidence_id'] + '](' + url + ')'
            if source_kind == 'secondary':
                replacement += ' (secondary account: ' + limitation.strip() + ')'
        output[document] = output[document].replace(marker, replacement)
    for name, body in output.items():
        if '{{evidence_claim.' in body:
            raise ValueError(name + ': undeclared or malformed evidence claim marker')
    return output


def _render_capture(root: Path, ident: str, ref: dict, bindings: list) -> str:
    """Cite a retained manual capture for official/contextual material."""
    binding = ref['capture_binding']
    if (binding not in bindings or not binding['path'].endswith('/manual-captures.json')
            or binding != cases.source_binding(root, binding['path'], locator=binding['locator'],
                                               applicability=binding['applicability'])):
        raise ValueError(ident + ': current manual capture binding required')
    capture_manifest = cases.safe(root, binding['path'])
    captures = cases.load(capture_manifest).get('captures', [])
    index = ref['capture_index']
    if isinstance(index, bool) or not isinstance(index, int) or index < 0 or index >= len(captures):
        raise ValueError(ident + ': capture index does not resolve')
    capture = captures[index]
    rel = capture.get('capture_path')
    if (not isinstance(rel, str) or Path(rel).is_absolute() or '..' in Path(rel).parts
            or not rel.startswith('raw/')):
        raise ValueError(ident + ': invalid retained source path')
    raw_path = cases.safe(root, str((capture_manifest.parent / rel).relative_to(root)))
    raw = raw_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != capture.get('sha256'):
        raise ValueError(ident + ': retained capture changed')
    passage = ref['supporting_passage']
    if not isinstance(passage, str) or len(passage.strip()) < 12 or passage not in raw.decode('utf-8'):
        raise ValueError(ident + ': source passage does not resolve in retained capture')
    if not capture.get('retrieved_at') or not capture.get('source_url'):
        raise ValueError(ident + ': capture lacks date or source URL')
    kind = ref['source_kind']
    if kind not in {'original', 'secondary', 'private'}:
        raise ValueError(ident + ': invalid source kind')
    if kind == 'private':
        return '[Reviewed private source: ' + ident + ']'
    url = capture['source_url']
    if not isinstance(url, str) or not re.fullmatch(r'https?://[^\s)]+', url):
        raise ValueError(ident + ': capture lacks usable original URL')
    text = '[Source: ' + str(capture['retrieved_at'])[:10] + '](' + url + ')'
    if kind == 'secondary':
        limitation = ref['limitation']
        if not isinstance(limitation, str) or len(limitation.strip()) < 15:
            raise ValueError(ident + ': secondary account needs a visible limitation')
        text += ' (secondary account: ' + limitation.strip() + ')'
    return text
