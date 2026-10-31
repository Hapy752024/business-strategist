"""Write a current draft-basis claim challenge for a case (no reviewed ledger bound)."""
import hashlib
import json
from pathlib import Path


def install(root, case_id='a'):
    base = Path(root) / 'cases' / case_id / 'claim_challenge'
    base.mkdir(parents=True, exist_ok=True)
    draft = base / 'draft-claims.json'
    draft.write_text(json.dumps([{'claim_id': 'D1', 'text': 'Synthetic draft claim.', 'section': 'Executive assessment',
                                  'sources': []}]))
    report = base / 'draft-falsification-report.json'
    report.write_text(json.dumps({'schema_version': 1, 'basis': 'draft', 'source_ledger': str(draft),
                                  'source_ledger_sha256': hashlib.sha256(draft.read_bytes()).hexdigest(),
                                  'counts': {'survived': 1}}))
    return report
