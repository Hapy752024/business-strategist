#!/usr/bin/env python3
"""The one hard rule: no final recommendation without a current claim challenge.

A claim challenge is a falsification report written by apply_falsification.py:
- reviewed basis (`falsification-report.json`): accepted only when its `source_ledger_sha256`
  equals the sha256 of every currently bound reviewed `claim-ledger.json`;
- draft basis (`draft-falsification-report.json`): accepted only when no reviewed ledger is
  bound and its `source_ledger_sha256` equals the current draft-claims file it names.
Used by final delivery, final appraisal, final plan and final case-insights publication.
Progress or provisional publications never call it.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

REVIEWED, DRAFT = 'falsification-report.json', 'draft-falsification-report.json'
MISSING = ('no claim challenge: a final recommendation needs a falsification output (reviewed ledger, or '
           '--draft-claims when no ledger exists); run export_claims_for_falsification.py, the claim-falsifier '
           'and apply_falsification.py (references/falsify.md)')
STALE = ('claim challenge stale or unrelated to current claims: rerun export_claims_for_falsification.py, the '
         'claim-falsifier and apply_falsification.py on the current {what}')


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _reports(base: Path, name: str) -> list[tuple[Path, dict]]:
    out = []
    for path in sorted(base.rglob(name)) if base.is_dir() else ():
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(data, dict):
            out.append((path, data))
    return out


def _draft_source(report: Path, data: dict) -> Path | None:
    named = Path(str(data.get('source_ledger') or ''))
    for candidate in (named, report.parent / named.name):
        if str(candidate) and candidate.is_file():
            return candidate
    return None


def status(root: Path, case_id: str, ledger_paths=(), extra_dirs=()) -> dict:
    """{'status': current|missing|stale, 'basis', 'path', 'reason'} for the case's current claims."""
    root = Path(root).absolute()
    ledgers = [p if Path(p).is_absolute() else root / p for p in ledger_paths]
    ledgers = [Path(p) for p in ledgers if Path(p).is_file()]
    dirs = [root / 'cases' / case_id, *map(Path, extra_dirs), *(p.parent for p in ledgers)]
    seen, reviewed, drafts = set(), [], []
    for base in dirs:
        for kind, bucket in ((REVIEWED, reviewed), (DRAFT, drafts)):
            for path, data in _reports(base, kind):
                if path.resolve() not in seen:
                    seen.add(path.resolve())
                    bucket.append((path, data))
    if not reviewed and not drafts:
        return {'status': 'missing', 'reason': MISSING}
    if ledgers:
        matched = []
        for led in ledgers:
            digest = _sha(led)
            hit = next((p for p, d in reviewed if d.get('basis', 'reviewed_ledger') != 'draft'
                        and d.get('source_ledger_sha256') == digest), None)
            if hit is None:
                return {'status': 'stale', 'reason': STALE.format(what=f'reviewed ledger {led.name}')}
            matched.append(hit)
        return {'status': 'current', 'basis': 'reviewed_ledger', 'path': str(matched[0])}
    for path, data in sorted(drafts, key=lambda item: item[0].stat().st_mtime, reverse=True):
        source = _draft_source(path, data)
        if source is not None and data.get('source_ledger_sha256') == _sha(source):
            return {'status': 'current', 'basis': 'draft', 'path': str(path), 'draft_claims': str(source)}
    return {'status': 'stale', 'reason': STALE.format(what='draft claims (or bind the reviewed ledger)')}


def require_current(root: Path, case_id: str, ledger_paths=(), extra_dirs=()) -> dict:
    result = status(root, case_id, ledger_paths, extra_dirs)
    if result['status'] != 'current':
        raise ValueError(result['reason'])
    return result


def bound_ledgers(bindings) -> list[str]:
    """Reviewed claim-ledger paths among source bindings (dicts with `path`, or plain paths)."""
    paths = [b.get('path') if isinstance(b, dict) else b for b in bindings or []]
    return sorted({p for p in paths if isinstance(p, str) and p.endswith('/customer-feedback/claim-ledger.json')})
