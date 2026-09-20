"""Normalize and diff AI answer-engine observations; observations are not demand evidence."""
import argparse
import json
from pathlib import Path

STATUSES = ('success', 'error', 'unsupported')
SURFACES = ('api', 'consumer', 'ai_overview')
PROMPT_TYPES = ('unbranded_discovery', 'brand_seeded', 'decision_stage', 'educational')
FIELDS = ('engine', 'model', 'search_config', 'locale', 'timestamp', 'surface',
          'prompt_type', 'prompt_id', 'prompt_version', 'repetition', 'status',
          'brand_mentioned', 'url_cited', 'recommended', 'answer_text')
KEY = ('engine', 'model', 'search_config', 'surface', 'locale', 'prompt_id', 'prompt_version')
TRACKED = ('brand_mentioned', 'url_cited', 'recommended')


def normalize_observation(raw):
    if not isinstance(raw, dict):
        raise ValueError('observation must be an object')
    row = {k: raw.get(k) for k in FIELDS}
    if row['status'] not in STATUSES:
        raise ValueError(f"status: must be one of {STATUSES}")
    if row['surface'] not in SURFACES:
        raise ValueError(f"surface: must be one of {SURFACES}")
    if row['prompt_type'] not in PROMPT_TYPES:
        raise ValueError(f"prompt_type: must be one of {PROMPT_TYPES}")
    if type(row['prompt_version']) is not int or type(row['repetition']) is not int:
        raise ValueError('prompt_version and repetition: integer required')
    for k in ('engine', 'model', 'search_config', 'prompt_id'):
        if not isinstance(row[k], str) or not row[k]:
            raise ValueError(f'{k}: nonempty string required')
    if row['status'] == 'success':
        for k in TRACKED:
            if type(row[k]) is not bool:
                raise ValueError(f'{k}: boolean required on success')
    else:
        for k in TRACKED:
            if row[k] is not None:
                raise ValueError(f'{k}: must be null when status is {row["status"]}; failure is unknown, not absence')
    return row


def _key(row):
    return tuple(row[k] for k in KEY)


def diff_observations(current, prior):
    prior_ok = {_key(r): r for r in prior if r.get('status') == 'success'}
    changes, skipped_failed, skipped_incompatible, compared = [], 0, 0, 0
    for row in current:
        if row.get('status') != 'success':
            skipped_failed += 1
            continue
        old = prior_ok.get(_key(row))
        if old is None:
            skipped_incompatible += 1
            continue
        compared += 1
        for field in TRACKED:
            if row[field] != old[field]:
                changes.append({'prompt_id': row['prompt_id'], 'engine': row['engine'],
                                'field': field, 'from': old[field], 'to': row[field]})
    return {'changes': changes,
            'coverage': {'current': len(current), 'prior': len(prior), 'compared': compared,
                         'skipped_incompatible': skipped_incompatible, 'skipped_failed': skipped_failed}}


def build_summary(rows, prior_rows):
    gaps = sorted({(r['engine'], r['status']) for r in rows if r.get('status') != 'success'})
    return {'observations': len(rows),
            'coverage_gaps': [{'engine': e, 'reason': s} for e, s in gaps],
            'diff': diff_observations(rows, prior_rows) if prior_rows else None,
            'boundary': 'observation of configured surfaces only; not customer-demand evidence; failures are unknown, not absence'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--panel', type=Path, required=True)
    p.add_argument('--recorded', type=Path, required=True)
    p.add_argument('--prior', type=Path)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    try:
        panel = json.loads(args.panel.read_text())
        assert isinstance(panel.get('prompts'), list) and panel['prompts'], 'panel.prompts must be a nonempty list'
        rows = [normalize_observation(json.loads(line)) for line in args.recorded.read_text().splitlines() if line.strip()]
        prior = [normalize_observation(json.loads(line)) for line in args.prior.read_text().splitlines() if line.strip()] if args.prior else []
    except (OSError, ValueError, AttributeError, AssertionError) as exc:
        print(json.dumps({'status': 'fail', 'errors': [str(exc)]}))
        return True
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'evidence.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in rows))
    summary = build_summary(rows, prior)
    (args.out / 'summary.json').write_text(json.dumps(summary, indent=2))
    lines = ['# AI-answer observation report', '', f"Boundary: {summary['boundary']}", '',
             f"Observations: {summary['observations']}; coverage gaps: {len(summary['coverage_gaps'])}"]
    if summary['diff']:
        lines.append(f"Compared: {summary['diff']['coverage']['compared']}; changes: {len(summary['diff']['changes'])}")
    (args.out / 'report.md').write_text('\n'.join(lines) + '\n')
    print(json.dumps({'status': 'pass', 'out': str(args.out), **summary}, default=str))
    return False


if __name__ == '__main__':
    raise SystemExit(main())
