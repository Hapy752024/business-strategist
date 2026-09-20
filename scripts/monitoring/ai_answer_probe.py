"""Normalize and diff AI answer-engine observations; observations are not demand evidence."""
import argparse
import json
from datetime import datetime
from pathlib import Path

STATUSES = ('success', 'error', 'unsupported')
SURFACES = ('api', 'consumer', 'ai_overview')
PROMPT_TYPES = ('unbranded_discovery', 'brand_seeded', 'decision_stage', 'educational')
FIELDS = ('engine', 'model', 'search_config', 'locale', 'timestamp', 'surface',
          'prompt_type', 'prompt_id', 'prompt_version', 'repetition', 'status',
          'brand_mentioned', 'url_cited', 'recommended', 'answer_text')
KEY = ('engine', 'model', 'search_config', 'surface', 'locale', 'prompt_type',
       'prompt_id', 'prompt_version')
TRACKED = ('brand_mentioned', 'url_cited', 'recommended')


def load_panel(raw):
    if not isinstance(raw, dict):
        raise ValueError('panel must be an object')
    prompts = raw.get('prompts')
    if not isinstance(prompts, list) or not prompts:
        raise ValueError('panel.prompts must be a nonempty list')
    declared, seen = [], set()
    for entry in prompts:
        if not isinstance(entry, dict):
            raise ValueError('panel.prompts entries must be objects')
        for k in ('id', 'type', 'text'):
            if not isinstance(entry.get(k), str) or not entry[k]:
                raise ValueError(f"panel.prompts[].{k}: nonempty string required")
        if type(entry.get('version')) is not int:
            raise ValueError('panel.prompts[].version: integer required')
        if entry['type'] not in PROMPT_TYPES:
            raise ValueError(f"panel.prompts[].type: must be one of {PROMPT_TYPES}")
        key = (entry['id'], entry['version'])
        if key in seen:
            raise ValueError(f'duplicate panel prompt id/version: {key}')
        seen.add(key)
        declared.append({'prompt_id': entry['id'], 'prompt_version': entry['version'],
                         'prompt_type': entry['type']})
    engines = raw.get('engines')
    if engines is not None and (not isinstance(engines, list) or not engines
                                or not all(isinstance(e, str) and e for e in engines)):
        raise ValueError('panel.engines: must be a nonempty list of nonempty strings when present')
    repetitions = raw.get('repetitions')
    if repetitions is not None and (type(repetitions) is not int or repetitions < 1):
        raise ValueError('panel.repetitions: integer >= 1 required when present')
    return {'declared': declared, 'engines': engines, 'repetitions': repetitions,
            'panel_version': raw.get('panel_version')}


def _usable_timestamp(value):
    if not isinstance(value, str) or not value:
        raise ValueError('timestamp: nonempty ISO-8601 string required on success')
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        raise ValueError(f'timestamp: not ISO-8601 parseable: {value!r}')
    if parsed.tzinfo is None:
        raise ValueError('timestamp: a timezone offset is required so collection windows are comparable')
    return value


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
        if not isinstance(row['locale'], str) or not row['locale']:
            raise ValueError('locale: nonempty string required on success; comparison needs collection context')
        if not isinstance(row['answer_text'], str) or not row['answer_text']:
            raise ValueError('answer_text: nonempty string required on success; a claim must retain its source answer')
        _usable_timestamp(row['timestamp'])
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


def _index_success(rows):
    seen = {}
    for r in rows:
        if r.get('status') != 'success':
            continue
        k = (_key(r), r['repetition'])
        if k in seen:
            raise ValueError(
                f"duplicate successful observation for prompt {r['prompt_id']} "
                f"engine {r['engine']} repetition {r['repetition']}: "
                'repetitions are independent samples and must be retained, not overwritten')
        seen[k] = r
    return seen


def _group(indexed):
    grouped = {}
    for (key, _rep), row in indexed.items():
        grouped.setdefault(key, []).append(row)
    return grouped


def _window(rows):
    stamps = sorted(r['timestamp'] for r in rows if r.get('status') == 'success')
    return {'start': stamps[0], 'end': stamps[-1]} if stamps else None


def _rate(rows, field):
    return sum(1 for r in rows if r[field]) / len(rows) if rows else None


def _fmt_rate(value):
    return 'n/a' if value is None else f'{value:.2f}'


def diff_observations(current, prior):
    indexed_current, indexed_prior = _index_success(current), _index_success(prior)
    by_current, by_prior = _group(indexed_current), _group(indexed_prior)

    changes, trends = [], []
    compared, skipped_incompatible, skipped_unpaired = 0, 0, 0

    for key in sorted(set(by_current) | set(by_prior)):
        cur, old = by_current.get(key), by_prior.get(key)
        if cur is None or old is None:
            skipped_incompatible += len(cur or [])
            continue
        compared += 1
        for field in TRACKED:
            prior_rate, current_rate = _rate(old, field), _rate(cur, field)
            trends.append({'prompt_id': key[6], 'engine': key[0], 'prompt_type': key[5],
                           'field': field, 'prior_rate': prior_rate, 'current_rate': current_rate,
                           'delta': current_rate - prior_rate,
                           'prior_n': len(old), 'current_n': len(cur)})
        old_by_rep = {r['repetition']: r for r in old}
        cur_by_rep = {r['repetition']: r for r in cur}
        skipped_unpaired += len(set(old_by_rep) ^ set(cur_by_rep))
        for rep in sorted(set(old_by_rep) & set(cur_by_rep)):
            for field in TRACKED:
                if old_by_rep[rep][field] != cur_by_rep[rep][field]:
                    changes.append({'prompt_id': key[6], 'engine': key[0], 'repetition': rep,
                                    'field': field, 'from': old_by_rep[rep][field],
                                    'to': cur_by_rep[rep][field]})

    prior_window, current_window = _window(prior), _window(current)
    overlapping = bool(prior_window and current_window
                       and prior_window['start'] <= current_window['end']
                       and current_window['start'] <= prior_window['end'])
    return {'changes': changes, 'trends': trends,
            'coverage': {'current': len(current), 'prior': len(prior), 'compared': compared,
                         'skipped_incompatible': skipped_incompatible,
                         'skipped_failed': sum(1 for r in current if r.get('status') != 'success'),
                         'skipped_unpaired': skipped_unpaired,
                         'prior_window': prior_window, 'current_window': current_window,
                         'overlapping_windows': overlapping}}


def _panel_coverage(rows, panel):
    declared = panel['declared']
    on_panel_keys = {(p['prompt_id'], p['prompt_version'], p['prompt_type']) for p in declared}
    on_panel, off_panel_ids = [], []
    for r in rows:
        if (r['prompt_id'], r['prompt_version'], r['prompt_type']) in on_panel_keys:
            on_panel.append(r)
        else:
            off_panel_ids.append(r['prompt_id'])

    gaps, covered = [], 0
    for p in declared:
        mine = [r for r in on_panel if (r['prompt_id'], r['prompt_version'], r['prompt_type'])
                == (p['prompt_id'], p['prompt_version'], p['prompt_type'])]
        if not mine:
            gaps.append({**p, 'reason': 'missing_no_observation'})
            continue
        engines = panel['engines'] or sorted({r['engine'] for r in mine})
        fully_covered = True
        for engine in engines:
            ok = [r for r in mine if r['engine'] == engine and r['status'] == 'success']
            if not ok:
                failed = [r for r in mine if r['engine'] == engine]
                reason = failed[0]['status'] if failed else 'missing_engine_observation'
                gaps.append({**p, 'engine': engine, 'reason': reason})
                fully_covered = False
                continue
            want = panel['repetitions']
            if want is not None and len(ok) < want:
                gaps.append({**p, 'engine': engine, 'reason': 'insufficient_repetitions',
                             'expected': want, 'observed': len(ok)})
                fully_covered = False
        covered += 1 if fully_covered else 0

    successful = [r for r in on_panel if r['status'] == 'success']
    return {'gaps': gaps, 'covered': covered, 'declared': len(declared),
            'successful_observations': len(successful),
            'off_panel': {'count': len(off_panel_ids),
                          'prompt_ids': sorted(set(off_panel_ids))},
            'unmeasured': not successful}


def build_summary(rows, prior_rows, panel):
    pc = _panel_coverage(rows, panel)
    return {'observations': len(rows),
            'panel_version': panel['panel_version'],
            'coverage': {'declared_prompts': pc['declared'], 'covered_prompts': pc['covered'],
                         'successful_observations': pc['successful_observations']},
            'coverage_gaps': sorted(pc['gaps'], key=lambda g: (g['prompt_id'], g.get('engine') or '')),
            'off_panel': pc['off_panel'],
            'unmeasured': pc['unmeasured'],
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
        panel = load_panel(json.loads(args.panel.read_text()))
        rows = [normalize_observation(json.loads(line)) for line in args.recorded.read_text().splitlines() if line.strip()]
        prior = [normalize_observation(json.loads(line)) for line in args.prior.read_text().splitlines() if line.strip()] if args.prior else []
    except (OSError, ValueError, AttributeError) as exc:
        print(json.dumps({'status': 'fail', 'errors': [str(exc)]}))
        return True
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'evidence.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in rows))
    summary = build_summary(rows, prior, panel)
    (args.out / 'summary.json').write_text(json.dumps(summary, indent=2))
    lines = ['# AI-answer observation report', '', f"Boundary: {summary['boundary']}", '',
             f"Observations: {summary['observations']}; coverage gaps: {len(summary['coverage_gaps'])}"]
    lines.append(f"Coverage: {summary['coverage']['covered_prompts']}/"
                 f"{summary['coverage']['declared_prompts']} declared prompts fully covered; "
                 f"gaps: {len(summary['coverage_gaps'])}")
    if summary['off_panel']['count']:
        lines.append(f"Off-panel rows (excluded from coverage): {summary['off_panel']['count']}")
    if summary['diff']:
        cov = summary['diff']['coverage']
        lines.append(f"Compared: {cov['compared']} probe targets; "
                     f"response changes: {len(summary['diff']['changes'])}; "
                     f"unpaired repetitions: {cov['skipped_unpaired']}")
        if cov['overlapping_windows']:
            lines.append('Warning: prior and current collection windows overlap; '
                         'treat movement as unestablished.')
        for t in summary['diff'].get('trends') or []:
            lines.append(f"{t['prompt_id']}/{t['engine']}/{t['field']}: "
                         f"{_fmt_rate(t['prior_rate'])} (n={t['prior_n']}) -> "
                         f"{_fmt_rate(t['current_rate'])} (n={t['current_n']})")
    (args.out / 'report.md').write_text('\n'.join(lines) + '\n')
    if summary['unmeasured']:
        summary['status'] = 'unmeasured'
        print(json.dumps(summary, default=str))
        return True
    print(json.dumps({'status': 'pass', 'out': str(args.out), **summary}, default=str))
    return False


if __name__ == '__main__':
    raise SystemExit(main())
