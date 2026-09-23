"""Offline AI-answer recordings: immutable runs, explicit populations, descriptive comparisons."""
import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit
from uuid import uuid4

STATUSES = ('success', 'error', 'unsupported')
SURFACES = ('api', 'consumer', 'ai_overview')
PROMPT_TYPES = ('unbranded_discovery', 'brand_seeded', 'decision_stage', 'educational')
TARGET_FIELDS = ('engine', 'model', 'search_config', 'surface', 'locale')
PROMPT_FIELDS = ('prompt_id', 'prompt_version', 'prompt_type')
KEY = TARGET_FIELDS + PROMPT_FIELDS
TRACKED = ('brand_mentioned', 'url_cited', 'recommended')
BOUNDARY = ('Recorded observations of declared surfaces only; not customer-demand evidence. '
            'Failures are unknown, not absence. Rate differences are descriptive, not causal or statistically established uplift.')
ARTIFACTS = ('panel.json', 'raw.jsonl', 'evidence.jsonl', 'summary.json', 'report.md')


def _text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{label}: nonempty string required')
    return value


def _positive(value, label):
    if type(value) is not int or value < 1:
        raise ValueError(f'{label}: positive integer required')
    return value


def _url(value, label):
    _text(value, label)
    parsed = urlsplit(value)
    if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError(f'{label}: public HTTP(S) URL without credentials required')
    return value


def _stamp(value):
    _text(value, 'timestamp')
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError as exc:
        raise ValueError('timestamp: ISO-8601 required') from exc
    if parsed.tzinfo is None:
        raise ValueError('timestamp: timezone required')
    return parsed


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def load_panel(raw):
    if not isinstance(raw, dict) or raw.get('schema_version') != 2:
        raise ValueError('panel.schema_version: use version 2; see references/ai-answer-recordings.md and fixtures/monitoring/recorded-example/')
    _text(raw.get('panel_version'), 'panel_version')
    subject = raw.get('subject')
    if not isinstance(subject, dict):
        raise ValueError('panel.subject: name and domains required')
    _text(subject.get('name'), 'subject.name')
    domains = subject.get('domains')
    if not isinstance(domains, list) or not domains:
        raise ValueError('subject.domains: nonempty list required')
    for domain in domains:
        _text(domain, 'subject.domain')
        if urlsplit('https://' + domain).hostname != domain or '/' in domain or ':' in domain:
            raise ValueError('subject.domain: lowercase hostname only')
    prompts, targets = raw.get('prompts'), raw.get('targets')
    if not isinstance(prompts, list) or not prompts or not isinstance(targets, list) or not targets:
        raise ValueError('panel.prompts and panel.targets: nonempty lists required')
    declared, seen = [], set()
    for prompt in prompts:
        if not isinstance(prompt, dict):
            raise ValueError('panel prompt: object required')
        for field in ('id', 'text', 'source'):
            _text(prompt.get(field), 'prompt.' + field)
        _positive(prompt.get('version'), 'prompt.version')
        if prompt.get('type') not in PROMPT_TYPES:
            raise ValueError('prompt.type: unsupported type')
        key = (prompt['id'], prompt['version'])
        if key in seen:
            raise ValueError('duplicate panel prompt id/version')
        seen.add(key)
        declared.append({'prompt_id': prompt['id'], 'prompt_version': prompt['version'],
                         'prompt_type': prompt['type'], 'text': prompt['text']})
    seen = set()
    for target in targets:
        if not isinstance(target, dict):
            raise ValueError('panel target: object required')
        for field in TARGET_FIELDS:
            _text(target.get(field), 'target.' + field)
        if target['surface'] not in SURFACES:
            raise ValueError('target.surface: unsupported surface')
        _positive(target.get('repetitions'), 'target.repetitions')
        key = tuple(target[k] for k in TARGET_FIELDS)
        if key in seen:
            raise ValueError('duplicate panel target')
        seen.add(key)
    # Selection-source notes and ordering do not change the questions being asked.
    semantic = {'subject': {'name': subject['name'], 'domains': sorted(set(domains))},
                'panel_version': raw['panel_version'],
                'prompts': sorted(declared, key=lambda p: (p['prompt_id'], p['prompt_version'])),
                'targets': sorted([{k: t[k] for k in TARGET_FIELDS + ('repetitions',)} for t in targets],
                                  key=lambda t: tuple(t[k] for k in TARGET_FIELDS))}
    return {**semantic, 'digest': _digest(semantic), 'raw': raw}


def normalize_observation(raw):
    if not isinstance(raw, dict):
        raise ValueError('observation: object required')
    row = dict(raw)  # Preserve supplied citation annotations, error detail and other provenance.
    for field in TARGET_FIELDS + ('prompt_id', 'prompt_text', 'target_brand', 'recording_source'):
        _text(row.get(field), field)
    _url(row.get('target_url'), 'target_url')
    _positive(row.get('prompt_version'), 'prompt_version')
    _positive(row.get('repetition'), 'repetition')
    _stamp(row.get('timestamp'))
    if row.get('status') not in STATUSES or row.get('surface') not in SURFACES or row.get('prompt_type') not in PROMPT_TYPES:
        raise ValueError('status, surface or prompt_type: unsupported value')
    if row['status'] == 'success':
        _text(row.get('answer_text'), 'answer_text')
        _text(row.get('annotation_method'), 'annotation_method')
        urls = row.get('citation_urls')
        if not isinstance(urls, list):
            raise ValueError('citation_urls: list required on success')
        for url in urls:
            _url(url, 'citation_url')
        for field in TRACKED:
            if type(row.get(field)) is not bool:
                raise ValueError(f'{field}: boolean required on success')
        if row['url_cited'] and not urls:
            raise ValueError('url_cited requires citation_urls')
    else:
        _text(row.get('error_detail'), 'error_detail')
        if any(row.get(field) is not None for field in TRACKED):
            raise ValueError('failure flags must be null: unknown, not absence')
    return row


def _key(row):
    return tuple(row[k] for k in KEY)


def _selection(rows, panel):
    targets = {tuple(t[k] for k in TARGET_FIELDS): t for t in panel['targets']}
    prompts = {tuple(p[k] for k in PROMPT_FIELDS): p for p in panel['prompts']}
    selected, excluded, seen = [], [], set()
    for row in rows:
        target = targets.get(tuple(row[k] for k in TARGET_FIELDS))
        prompt = prompts.get(tuple(row[k] for k in PROMPT_FIELDS))
        if target is None or prompt is None or row['repetition'] > target['repetitions']:
            excluded.append({**{k: row[k] for k in KEY}, 'repetition': row['repetition'], 'reason': 'outside_declared_panel'})
            continue
        if row['prompt_text'] != prompt['text']:
            raise ValueError('recorded prompt_text differs from declared prompt; assign a new prompt version')
        if row['target_brand'] != panel['subject']['name'] or urlsplit(row['target_url']).hostname not in panel['subject']['domains']:
            raise ValueError('observation target does not match panel subject')
        if row['status'] == 'success' and row['url_cited'] and not any(urlsplit(u).hostname in panel['subject']['domains'] for u in row['citation_urls']):
            raise ValueError('url_cited requires a citation to a declared subject domain')
        key = (_key(row), row['repetition'])
        if key in seen:
            raise ValueError('duplicate selected observation/repetition; retain retries in raw source and select one final outcome')
        seen.add(key)
        selected.append(row)
    return selected, sorted(excluded, key=lambda r: tuple(str(r[k]) for k in KEY) + (r['repetition'],))


def _coverage(rows, panel):
    indexed = {(_key(r), r['repetition']): r for r in rows}
    gaps, counts = [], []
    for target in panel['targets']:
        for prompt in panel['prompts']:
            identity = {k: target[k] for k in TARGET_FIELDS} | {k: prompt[k] for k in PROMPT_FIELDS}
            count = 0
            for rep in range(1, target['repetitions'] + 1):
                row = indexed.get((_key(identity), rep))
                if row and row['status'] == 'success':
                    count += 1
                else:
                    gaps.append({**identity, 'repetition': rep, 'reason': row['status'] if row else 'missing',
                                 'detail': row.get('error_detail') if row else None})
            counts.append({**identity, 'expected': target['repetitions'], 'successful': count})
    return {'expected_observations': sum(t['expected'] for t in counts),
            'successful_observations': sum(t['successful'] for t in counts), 'targets': counts}, gaps


def diff_observations(current, prior, panel, prior_panel):
    empty = {'eligible': False, 'reason': None, 'trends': []}
    if prior_panel is None:
        return {**empty, 'reason': 'prior_panel_unknown'}
    if panel['digest'] != prior_panel['digest']:
        return {**empty, 'reason': 'panel_or_collection_context_changed'}
    current, _ = _selection(current, panel)
    prior, _ = _selection(prior, prior_panel)
    _, gaps = _coverage(current, panel)
    _, prior_gaps = _coverage(prior, prior_panel)
    if gaps or prior_gaps:
        return {**empty, 'reason': 'incomplete_current_or_prior_coverage', 'prior_coverage_gaps': prior_gaps}
    if max(_stamp(r['timestamp']) for r in prior) >= min(_stamp(r['timestamp']) for r in current):
        return {**empty, 'reason': 'overlapping_or_reversed_windows'}
    trends = []
    for key in sorted({_key(r) for r in current}):
        now, old = [r for r in current if _key(r) == key], [r for r in prior if _key(r) == key]
        for field in TRACKED:
            before, after = sum(r[field] for r in old) / len(old), sum(r[field] for r in now) / len(now)
            trends.append({**dict(zip(KEY, key)), 'field': field, 'prior_rate': before,
                           'current_rate': after, 'delta': after - before, 'prior_n': len(old), 'current_n': len(now)})
    return {'eligible': True, 'reason': 'compatible_complete_nonoverlapping_windows', 'trends': trends}


def build_summary(rows, prior_rows, panel, prior_panel=None, prior_supplied=False):
    selected, excluded = _selection(rows, panel)
    coverage, gaps = _coverage(selected, panel)
    diff = diff_observations(selected, prior_rows, panel, prior_panel) if prior_supplied else None
    status = ('unmeasured' if not coverage['successful_observations'] else 'partial' if gaps else
              'incomparable' if diff and not diff['eligible'] else 'compared' if diff else 'baseline')
    return {'schema_version': 2, 'status': status, 'boundary': BOUNDARY, 'subject': panel['subject'],
            'panel_digest': panel['digest'], 'panel_version': panel['panel_version'],
            'observations': len(rows), 'coverage': coverage, 'coverage_gaps': gaps,
            'off_panel': {'count': len(excluded), 'rows': excluded}, 'diff': diff,
            'eligible_for_trend': bool(diff and diff['eligible'])}


def _label(row):
    return ' / '.join(str(row[k]) for k in KEY)


def _report_lines(summary):
    lines = ['# AI-answer recording report', '', 'Boundary: ' + summary['boundary'], '',
             'Run: ' + summary['run_id'], 'Measurement status: ' + summary['status'],
             'Subject: ' + summary['subject']['name'], 'Panel digest: ' + summary['panel_digest'],
             f"Coverage: {summary['coverage']['successful_observations']}/{summary['coverage']['expected_observations']} expected observations",
             f"Excluded observations: {summary['off_panel']['count']}"]
    for gap in summary['coverage_gaps']:
        lines.append(f"- Unknown: {_label(gap)} / repetition {gap['repetition']}: {gap['reason']} ({gap['detail'] or 'no recording'})")
    if summary['diff']:
        lines.append('Comparison: ' + summary['diff']['reason'])
        for gap in summary['diff'].get('prior_coverage_gaps', []):
            lines.append(f"- Prior unknown: {_label(gap)} / repetition {gap['repetition']}: {gap['reason']}")
        for trend in summary['diff']['trends']:
            lines.append(f"- {_label(trend)} / {trend['field']}: {trend['prior_rate']:.3f} (n={trend['prior_n']}) -> {trend['current_rate']:.3f} (n={trend['current_n']}); descriptive delta {trend['delta']:+.3f}")
    lines.extend(['', '## Decision handoff',
                  'Inspect the retained source answers and citation annotations before proposing a change.',
                  'Record affected URL/customer task, evidence and uncertainty, proposed change, expected customer benefit, agent work, owner dependency, acceptance check and review/stop rule in the existing improvement queue.',
                  'No action warranted is a valid decision. No automatic publishing, cadence or demand inference follows from this report.'])
    return lines


def _write(path, content):
    # Exclusive files inside this run's exclusively allocated directory. Never delete old data.
    with path.open('x', encoding='utf-8') as handle:
        handle.write(content)


def load_run(path):
    """Read only digest-bound completed runs; partial runs remain diagnostic artifacts."""
    path = Path(path)
    if path.is_symlink() or not path.is_dir():
        raise ValueError('run must be a real directory')
    marker = path / 'run.json'
    if marker.is_symlink():
        raise ValueError('run completion marker must not be a symlink')
    receipt = json.loads(marker.read_text(encoding='utf-8'))
    if receipt.get('schema_version') != 2 or receipt.get('completion') != 'complete' or set(receipt.get('artifacts', {})) != set(ARTIFACTS):
        raise ValueError('invalid run completion manifest')
    _text(receipt.get('run_id'), 'run_id')
    contents = {}
    for name in ARTIFACTS:
        artifact = path / name
        if artifact.is_symlink() or not artifact.is_file():
            raise ValueError('missing/linked run artifact: ' + name)
        data = artifact.read_bytes()
        if hashlib.sha256(data).hexdigest() != receipt['artifacts'][name]:
            raise ValueError('changed/incomplete run artifact: ' + name)
        contents[name] = data.decode('utf-8')
    summary = json.loads(contents['summary.json'])
    if summary.get('run_id') != receipt['run_id']:
        raise ValueError('run identity mismatch')
    panel = load_panel(json.loads(contents['panel.json']))
    if summary.get('panel_digest') != panel['digest']:
        raise ValueError('panel identity mismatch')
    rows = _rows(contents['evidence.jsonl'])
    return {'summary': summary, 'panel': panel, 'rows': rows}


def _rows(text):
    return [normalize_observation(json.loads(line)) for line in text.splitlines() if line.strip()]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--panel', type=Path, required=True)
    parser.add_argument('--recorded', type=Path, required=True)
    prior_group = parser.add_mutually_exclusive_group()
    prior_group.add_argument('--prior-run', type=Path, help='Completed immutable run; hashes verified before comparison')
    prior_group.add_argument('--prior', type=Path, help='Raw prior recording; also supply --prior-panel for eligibility')
    parser.add_argument('--prior-panel', type=Path)
    parser.add_argument('--out', type=Path, required=True, help='New, non-existing run directory; existing destinations are rejected')
    args = parser.parse_args()
    run_id = uuid4().hex
    out = args.out.absolute()
    try:
        if out.exists() or out.is_symlink():
            raise ValueError('--out must be a new, non-existing directory; existing destinations are never replaced')
        if args.prior_panel and not args.prior:
            raise ValueError('--prior-panel requires --prior; --prior-run includes its own panel')
        panel_raw = json.loads(args.panel.read_text(encoding='utf-8'))
        panel = load_panel(panel_raw)
        raw = args.recorded.read_text(encoding='utf-8')
        rows = _rows(raw)
        prior, prior_panel = [], None
        if args.prior_run:
            loaded = load_run(args.prior_run)
            prior, prior_panel = loaded['rows'], loaded['panel']
        elif args.prior:
            prior = _rows(args.prior.read_text(encoding='utf-8'))
            prior_panel = load_panel(json.loads(args.prior_panel.read_text(encoding='utf-8'))) if args.prior_panel else None
        summary = build_summary(rows, prior, panel, prior_panel, bool(args.prior or args.prior_run))
        summary['run_id'] = run_id
        summary['prior_source'] = str((args.prior_run or args.prior).absolute()) if args.prior_run or args.prior else None
        out.parent.mkdir(parents=True, exist_ok=True)
        out.mkdir()  # Exclusive allocation: only one concurrent invocation can own this path.
        contents = {'panel.json': json.dumps(panel_raw, indent=2) + '\n', 'raw.jsonl': raw,
                    'evidence.jsonl': ''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows),
                    'summary.json': json.dumps(summary, indent=2) + '\n',
                    'report.md': '\n'.join(_report_lines(summary)) + '\n'}
        for name, content in contents.items():
            _write(out / name, content)
        receipt = {'schema_version': 2, 'completion': 'complete', 'run_id': run_id,
                   'artifacts': {name: hashlib.sha256(content.encode()).hexdigest() for name, content in contents.items()}}
        _write(out / 'run.json', json.dumps(receipt, indent=2) + '\n')
    except (OSError, ValueError, TypeError, KeyError, AttributeError, KeyboardInterrupt) as exc:
        print(json.dumps({'status': 'fail', 'completion': 'incomplete', 'run_id': run_id,
                          'out': str(out), 'errors': [str(exc) or 'interrupted']}))
        return 1
    print(json.dumps({'completion': 'complete', 'out': str(out), **summary}))
    return 0 if summary['status'] in ('baseline', 'compared') else 2


if __name__ == '__main__':
    raise SystemExit(main())
