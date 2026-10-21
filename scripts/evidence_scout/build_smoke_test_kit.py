#!/usr/bin/env python3
"""Author a smoke-test experiment card draft, message variants, pending budget approval and responder ledger.

The draft is committed by `case_workspace.py experiment-plan`, which freezes the
hypothesis, threshold, kill rule and sample plan. Nothing here touches the project lock.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
from pathlib import Path

try:
    from .workspace import prepare_research_output, cases
except ImportError:
    from workspace import prepare_research_output, cases

ROOT = Path(__file__).resolve().parents[2]
PAIN_FRAMES = ['cost of the current workaround', 'time or effort lost', 'risk or fear of getting it wrong',
               'missed outcome or opportunity', 'trust in existing providers']
Z_ALPHA = 1.645  # one-sided 95%
Z_POWER = 0.84   # 80% power


def sample_per_variant(p_low: float, p_high: float, z: float = Z_ALPHA, power_z: float = Z_POWER) -> int:
    """Qualified visitors per variant to tell p_low from p_high (two-proportion normal approximation)."""
    if not 0 < p_low < p_high < 1:
        raise ValueError('need 0 < p_low < p_high < 1')
    mean = (p_low + p_high) / 2
    spread = z * math.sqrt(2 * mean * (1 - mean)) + power_z * math.sqrt(p_low * (1 - p_low) + p_high * (1 - p_high))
    return math.ceil(spread ** 2 / (p_high - p_low) ** 2)


def _relative(path: Path) -> str:
    owner = cases.locate(path)
    return str(path.relative_to(owner)) if owner else str(path)


def build(*, run_dir: Path, experiment_id: str, assumption_ids: list[str], library_id: str, offer: str,
          segment: str, variants: int, p_low: float, p_high: float, out_dir: Path, metric: str = 'booked',
          window_days: int = 14, channel: str = 'to be chosen', action: str = 'book a 20-minute call',
          problem: str = '', source_bindings: str = '') -> Path:
    if not 1 <= variants <= len(PAIN_FRAMES):
        raise ValueError(f'variants must be between 1 and {len(PAIN_FRAMES)}')
    if not experiment_id.strip() or not offer.strip() or not segment.strip() or not assumption_ids:
        raise ValueError('experiment_id, assumption_ids, offer, and segment must be nonempty')
    run_dir, out_dir = Path(run_dir).absolute(), Path(out_dir).absolute()
    if not run_dir.is_dir() or not (run_dir / 'summary.json').is_file():
        raise ValueError('run-dir must contain an existing summary.json')
    summary = json.loads((run_dir / 'summary.json').read_text())
    if not isinstance(summary, dict):
        raise ValueError('summary.json must be an object')
    if out_dir.exists():
        raise ValueError('choose a fresh output directory')
    if cases.locate(run_dir) != cases.locate(out_dir):
        raise ValueError('run and output must share the same project authority')
    per_variant = sample_per_variant(p_low, p_high)
    topic = summary.get('topic', 'unknown topic')
    prepare_research_output(out_dir, input_paths=[run_dir / 'summary.json'], source_bindings_file=source_bindings)
    out_dir.mkdir(parents=True, exist_ok=True)
    ids = [f'V{i + 1}' for i in range(variants)]
    msgs = [{'id': ids[i], 'pain_frame': PAIN_FRAMES[i], 'headline': f'[{PAIN_FRAMES[i]}] headline for {segment}',
             'promise': offer, 'cta': 'Book a 20-minute call', 'evidence_ref': None} for i in range(variants)]
    (out_dir / 'message-variants.json').write_text(json.dumps(msgs, indent=2) + '\n')
    budget = {'status': 'pending', 'requested_amount': None, 'currency': None, 'channel': None,
              'duration_days': window_days, 'decision_informed': f'{experiment_id}: does {segment} take a behavioral step for "{offer}"?',
              'cpc_assumption': None, 'cpc_source': None, 'approved_by': None, 'approved_at': None}
    (out_dir / 'budget-approval.json').write_text(json.dumps(budget, indent=2) + '\n')
    responders = out_dir / 'responders.json'
    responders.write_text('[]\n')
    sample = per_variant * variants
    value = math.ceil(p_high * sample)
    card = {'schema_version': 1, 'id': experiment_id, 'library_id': library_id, 'assumption_ids': list(assumption_ids),
            'hypothesis': {'segment': segment, 'action': action, 'problem': problem or topic,
                           'threshold': {'metric': metric, 'value': value, 'sample': sample, 'window_days': window_days}},
            'kill_rule': f'Fewer than {value} {metric} from {sample} qualified visitors within {window_days} days.',
            'sample_plan': {'p_low': p_low, 'p_high': p_high, 'per_variant': per_variant}, 'channel': channel,
            'variants': ids, 'status': None,
            'authorization_refs': [{'path': _relative(out_dir / 'budget-approval.json'),
                                    'digest': hashlib.sha256((out_dir / 'budget-approval.json').read_bytes()).hexdigest()}],
            'responders_ref': {'path': _relative(responders), 'digest': hashlib.sha256(responders.read_bytes()).hexdigest()},
            'supersedes': None, 'result': None, 'frozen_digest': None}
    (out_dir / 'experiment-card.json').write_text(json.dumps(card, indent=2) + '\n')
    plan = f'''# Smoke test plan — {topic}

Generated {time.strftime('%Y-%m-%d')} from `{run_dir}`. Follow `references/smoke-test.md`. Commit the card with
`case_workspace.py experiment-plan --input experiment-card.json` before launch; that freezes everything below.

## Hypothesis
We believe {segment} will {action} because of {problem or topic}. We reconsider if fewer than {value} {metric}
within {sample} qualified visitors or {window_days} days. Tests assumptions: {', '.join(assumption_ids)}.

## Segment and traffic source
Segment: {segment}. Channel: {channel}. State why this channel reaches the segment and the retrieved CPC range with source and date in `budget-approval.json`.

## Message variants
See `message-variants.json` ({variants} variants, one pain frame each). Replace bracketed headlines with customer language from the evidence run and record the evidence_ref.

## Conversion action and thresholds
Primary measure: qualified {metric}, not clicks. Sample plan: {per_variant} qualified visitors per variant to tell {p_low:.0%} from {p_high:.0%}
at one-sided 95% confidence and 80% power. Pass threshold: {value} {metric} in total. These are learning budgets, not benchmarks.

## Disclosure
Show within one step after the call to action: the offer is being evaluated and not yet available, what happens with the data, and the interview booking option.

## Budget approval
See `budget-approval.json`; status pending. The experiment cannot be approved until its status is approved.

## Responder to interview funnel
identified → exposed → responded → eligible → booked → attended → usable incident. Import results with
`import_responders.py`; identities stay in `responders.json` and never enter case state.

## Stop rules
{card['kill_rule']} Also stop when the approved budget or window is spent, qualified traffic is below the sample plan and the channel cannot supply more, responders are out of segment, or the segment consistently reports a different pain.
'''
    (out_dir / 'smoke-test-plan.md').write_text(plan)
    return out_dir


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--run-dir', required=True, type=Path)
    ap.add_argument('--experiment-id', required=True, help='Card id, E-<slug>')
    ap.add_argument('--assumption-id', action='append', required=True, help='Register assumption id; repeatable')
    ap.add_argument('--library-id', default='message-smoke-test')
    ap.add_argument('--offer', required=True)
    ap.add_argument('--segment', required=True)
    ap.add_argument('--variants', type=int, default=3)
    ap.add_argument('--p-low', type=float, default=0.02)
    ap.add_argument('--p-high', type=float, default=0.05)
    ap.add_argument('--metric', default='booked')
    ap.add_argument('--window-days', type=int, default=14)
    ap.add_argument('--channel', default='to be chosen')
    ap.add_argument('--action', default='book a 20-minute call')
    ap.add_argument('--problem', default='')
    ap.add_argument('--out-dir', required=True, type=Path)
    ap.add_argument('--source-bindings', default='', help='Explicit shared-input applicability bindings')
    a = ap.parse_args()
    print(build(run_dir=a.run_dir, experiment_id=a.experiment_id, assumption_ids=a.assumption_id, library_id=a.library_id,
                offer=a.offer, segment=a.segment, variants=a.variants, p_low=a.p_low, p_high=a.p_high,
                out_dir=a.out_dir, metric=a.metric, window_days=a.window_days, channel=a.channel,
                action=a.action, problem=a.problem, source_bindings=a.source_bindings))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
