#!/usr/bin/env python3
"""Generate a smoke-test plan, message variants, pending budget approval, and responder ledger."""
from __future__ import annotations
import argparse
import json
import time
from pathlib import Path

PAIN_FRAMES = ['cost of the current workaround', 'time or effort lost', 'risk or fear of getting it wrong',
               'missed outcome or opportunity', 'trust in existing providers']


def build(*, run_dir: Path, hypothesis_id: str, offer: str, segment: str, variants: int, out_dir: Path) -> Path:
    if not 1 <= variants <= len(PAIN_FRAMES):
        raise ValueError(f'variants must be between 1 and {len(PAIN_FRAMES)}')
    if not hypothesis_id.strip() or not offer.strip() or not segment.strip():
        raise ValueError('hypothesis_id, offer, and segment must be nonempty')
    summary = json.loads((run_dir / 'summary.json').read_text()) if (run_dir / 'summary.json').exists() else {}
    topic = summary.get('topic', 'unknown topic')
    out_dir.mkdir(parents=True, exist_ok=False)
    msgs = [{'id': f'V{i+1}', 'pain_frame': PAIN_FRAMES[i],
             'headline': f'[{PAIN_FRAMES[i]}] headline for {segment}', 'promise': offer,
             'cta': 'Book a 20-minute call', 'evidence_ref': None} for i in range(variants)]
    (out_dir / 'message-variants.json').write_text(json.dumps(msgs, indent=2) + '\n')
    budget = {'status': 'pending', 'requested_amount': None, 'currency': None, 'channel': None,
              'duration_days': None, 'decision_informed': f'{hypothesis_id}: does {segment} take a behavioral step for "{offer}"?',
              'cpc_assumption': None, 'cpc_source': None, 'approved_by': None, 'approved_at': None}
    (out_dir / 'budget-approval.json').write_text(json.dumps(budget, indent=2) + '\n')
    (out_dir / 'responders.json').write_text('[]\n')
    plan = f'''# Smoke test plan — {topic}

Generated {time.strftime('%Y-%m-%d')} from `{run_dir}`. Follow `references/smoke-test.md`.

## Hypothesis
{hypothesis_id}: {segment} experiencing {topic} will take a behavioral step for "{offer}".

## Segment and traffic source
Segment: {segment}. Traffic: <channel, why this reaches the segment, retrieved CPC range with source and date>.

## Message variants
See `message-variants.json` ({variants} variants, one pain frame each). Replace bracketed headlines with customer language from the evidence run and record the evidence_ref.

## Conversion action and thresholds
Action: <booked call | deposit | pre-order | email (directional only)>. Pass threshold: <x% of qualified visitors>, proposed learning budget, not a benchmark. Minimum qualified visitors per variant: <n>.

## Disclosure
<exact on-page text shown after the CTA>.

## Budget approval
See `budget-approval.json`; status pending. Do not launch before it is approved.

## Responder to interview funnel
identified → exposed → responded → eligible → booked → attended → usable incident. Log in `responders.json`; screen with the interview kit.

## Stop rules
<budget/window spent | qualified traffic below minimum | responders out of segment | different pain reported>.
'''
    (out_dir / 'smoke-test-plan.md').write_text(plan)
    return out_dir


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--run-dir', required=True, type=Path)
    ap.add_argument('--hypothesis-id', required=True)
    ap.add_argument('--offer', required=True)
    ap.add_argument('--segment', required=True)
    ap.add_argument('--variants', type=int, default=3)
    ap.add_argument('--out-dir', required=True, type=Path)
    a = ap.parse_args()
    print(build(run_dir=a.run_dir, hypothesis_id=a.hypothesis_id, offer=a.offer, segment=a.segment,
                variants=a.variants, out_dir=a.out_dir))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
