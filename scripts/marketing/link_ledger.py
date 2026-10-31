"""Per-project link ledger: every link asked for, promised, live or lost, in one file.

Lives at `<business-root>/marketing/earned_media/link-ledger.json`, one row per source page.
Stages move only through recorded events: prospect -> pitched -> promised -> live -> lost, with
rejected (our decision) and declined (theirs) as exits. Only a `verify_links.py` observation can
move a row to live or lost; a reply, a promise or a Search Console row is recorded as what it is.
Nothing here sends mail or contacts anyone.

Commands: init, import-candidates (competitor_backlinks output), import-links (earned_media
import-links output), set (manual stage event), record (observation.json), check (verify live and
promised rows, bounded), report (counts, overdue follow-ups, markdown).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.marketing.link_observations import ROOT, sha, url_key  # noqa: E402

SCHEMA = json.loads((ROOT / 'schemas/link-ledger.schema.json').read_text())
RELATIVE = 'marketing/earned_media/link-ledger.json'
STAGES = ('prospect', 'pitched', 'promised', 'live', 'lost', 'rejected', 'declined')
MANUAL = {  # stage -> stages a human may set
    'prospect': {'pitched', 'rejected'},
    'pitched': {'pitched', 'promised', 'declined', 'rejected'},  # pitched again = follow-up
    'promised': {'declined', 'rejected'},
    'live': {'rejected'},
    'lost': {'pitched', 'rejected'},
    'declined': {'pitched'},
    'rejected': {'prospect'},
}
FOLLOW_UP_DAYS = 7


def _domain(url: str) -> str:
    host = url_key(url).split('/')[2]
    return host[4:] if host.startswith('www.') else host


def _today() -> str:
    return date.today().isoformat()


def _event(stage: str, at: str, note: str | None, source: str) -> dict:
    datetime.strptime(at, '%Y-%m-%d')
    return {'stage': stage, 'at': at, 'note': note, 'source': source}


def validate(doc: dict) -> list[str]:
    errors = [e.message for e in Draft202012Validator(SCHEMA, format_checker=FormatChecker()).iter_errors(doc)]
    seen = set()
    for row in doc.get('rows', []):
        if row['source_url'] in seen:
            errors.append(f"duplicate source_url {row['source_url']}")
        seen.add(row['source_url'])
        if row['history'] and row['history'][-1]['stage'] != row['stage']:
            errors.append(f"{row['source_url']}: stage differs from last history event")
    return errors


def new_ledger(property_url: str) -> dict:
    return {'schema_version': 1, 'property': _domain(property_url if '://' in property_url else 'https://' + property_url), 'updated_at': _today(), 'rows': []}


def load(path: Path) -> dict:
    doc = json.loads(path.read_text(encoding='utf-8'))
    errors = validate(doc)
    if errors:
        raise ValueError('invalid link ledger: ' + '; '.join(errors[:3]))
    return doc


def save(path: Path, doc: dict) -> None:
    doc['updated_at'] = _today()
    errors = validate(doc)
    if errors:
        raise ValueError('refusing to write an invalid ledger: ' + '; '.join(errors[:3]))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def _row(doc: dict, source_url: str) -> dict | None:
    key = url_key(source_url)
    return next((r for r in doc['rows'] if r['source_url'] == key), None)


def _new_row(source_url: str, *, stage: str, origin: str, at: str, note: str | None, target_url: str | None = None,
             opportunity_id: str | None = None, provenance: list[dict] | None = None) -> dict:
    return {'id': sha(url_key(source_url).encode())[:12], 'source_url': url_key(source_url), 'source_domain': _domain(source_url),
            'target_url': url_key(target_url) if target_url else None, 'stage': stage, 'origin': origin,
            'opportunity_id': opportunity_id, 'first_seen': at, 'last_checked_at': None, 'last_observation': None,
            'history': [_event(stage, at, note, origin)], 'provenance': provenance or []}


def import_candidates(doc: dict, candidates: dict, *, candidates_path: str, at: str | None = None) -> dict:
    """competitor_backlinks output: clean rows become prospects, flagged rows rejected with the flags as reason."""
    at = at or _today()
    prov = [{'path': candidates_path, 'sha256': sha(json.dumps(candidates, sort_keys=True).encode())}]
    added = {'prospect': 0, 'rejected': 0, 'skipped_existing': 0}
    for cand in candidates.get('candidates', []):
        if _row(doc, cand['source_url']):
            added['skipped_existing'] += 1
            continue
        flagged = bool(cand.get('flags'))
        stage = 'rejected' if flagged else 'prospect'
        note = ('flags: ' + ', '.join(cand['flags'])) if flagged else (
            'links to ' + ', '.join(sorted({l['competitor'] for l in cand.get('links_to', [])})))
        doc['rows'].append(_new_row(cand['source_url'], stage=stage, origin='competitor_backlinks', at=at, note=note, provenance=prov))
        added[stage] += 1
    return added


def import_links(doc: dict, export: dict, *, export_path: str) -> dict:
    """earned_media import-links output (Search Console): reported links, recorded as promised-by-report, never live."""
    at = export['exported_at']
    prov = [{'path': export_path, 'sha256': sha(json.dumps(export, sort_keys=True).encode())}]
    added = {'reported': 0, 'skipped_existing': 0}
    for cand in export.get('candidates', []):
        if _row(doc, cand['source_url']):
            added['skipped_existing'] += 1
            continue
        doc['rows'].append(_new_row(cand['source_url'], stage='promised', origin='search_console', at=at,
                                    note='reported by Search Console export; not verified live', target_url=cand.get('target_url'), provenance=prov))
        added['reported'] += 1
    return added


def set_stage(doc: dict, source_url: str, stage: str, *, at: str | None = None, note: str | None = None,
              target_url: str | None = None, opportunity_id: str | None = None, origin: str = 'manual') -> dict:
    at = at or _today()
    if stage not in STAGES:
        raise ValueError(f'unknown stage {stage}')
    if stage in {'live', 'lost'}:
        raise ValueError('live and lost come only from a recorded observation (record <observation.json>)')
    row = _row(doc, source_url)
    if row is None:
        if stage != 'prospect':
            raise ValueError('a new row starts as prospect')
        row = _new_row(source_url, stage='prospect', origin=origin, at=at, note=note, target_url=target_url, opportunity_id=opportunity_id)
        doc['rows'].append(row)
        return row
    if stage not in MANUAL[row['stage']]:
        raise ValueError(f"cannot move {row['stage']} -> {stage}")
    if stage == 'pitched' and not (target_url or row['target_url']):
        raise ValueError('pitched needs --target: the page the pitch asks them to link to')
    if target_url:
        row['target_url'] = url_key(target_url)
    if opportunity_id:
        row['opportunity_id'] = opportunity_id
    row['stage'] = stage
    row['history'].append(_event(stage, at, note, origin))
    return row


def record(doc: dict, observation: dict, *, observation_path: str) -> dict:
    """Apply a verify_links observation: present -> live, absent after live -> lost; access problems only touch last_checked_at."""
    row = _row(doc, observation['source_url'])
    if row is None:
        raise ValueError('observation source is not in the ledger; add it first')
    if row['target_url'] and url_key(observation['target_url']) != row['target_url']:
        raise ValueError('observation target differs from the ledger target')
    checked = observation['checked_at'][:10]
    row['last_checked_at'] = checked
    row['last_observation'] = {'path': observation_path, 'sha256': sha(json.dumps(observation, sort_keys=True).encode()),
                               'outcome': observation['outcome'], 'checked_at': observation['checked_at'],
                               'rel': next((a.get('rel') for a in observation.get('anchors', []) if a.get('href') == url_key(observation['target_url'])), None)}
    if observation['outcome'] == 'present':
        if row['stage'] != 'live':
            row['stage'] = 'live'
            row['target_url'] = row['target_url'] or url_key(observation['target_url'])
            row['history'].append(_event('live', checked, 'observed present', 'observation'))
    elif observation['outcome'] == 'absent' and row['stage'] == 'live':
        row['stage'] = 'lost'
        row['history'].append(_event('lost', checked, 'observed absent', 'observation'))
    return row


def due_checks(doc: dict) -> list[dict]:
    return [r for r in doc['rows'] if r['stage'] in {'live', 'promised'} and r['target_url']]


def overdue_follow_ups(doc: dict, today: str | None = None, days: int = FOLLOW_UP_DAYS) -> list[dict]:
    today_d = date.fromisoformat(today or _today())
    out = []
    for row in doc['rows']:
        if row['stage'] != 'pitched':
            continue
        pitches = [h for h in row['history'] if h['stage'] == 'pitched']
        if len(pitches) == 1 and date.fromisoformat(pitches[-1]['at']) + timedelta(days=days) <= today_d:
            out.append(row)
    return out


def report(doc: dict, today: str | None = None) -> dict:
    counts = {s: sum(1 for r in doc['rows'] if r['stage'] == s) for s in STAGES}
    live = [r for r in doc['rows'] if r['stage'] == 'live']
    origins = {}
    for r in doc['rows']:
        origins[r['origin']] = origins.get(r['origin'], 0) + 1
    return {'property': doc['property'], 'updated_at': doc['updated_at'], 'counts': counts, 'by_origin': origins,
            'live_domains': sorted({r['source_domain'] for r in live}),
            'nofollow_live': sorted(r['source_domain'] for r in live if (r['last_observation'] or {}).get('rel') and
                                    any(k in (r['last_observation']['rel'] or '') for k in ('nofollow', 'sponsored', 'ugc'))),
            'overdue_follow_ups': [{'source_url': r['source_url'], 'pitched_at': r['history'][-1]['at']} for r in overdue_follow_ups(doc, today)],
            'due_checks': len(due_checks(doc)),
            'limits': 'Counts are ledger states, not ranking credit. Live means observed present on the last check only.'}


def render(rep: dict) -> str:
    lines = [f"# Link ledger: {rep['property']}", '', f"Updated {rep['updated_at']}. {rep['limits']}", '', '| stage | rows |', '|---|---|']
    lines += [f'| {s} | {n} |' for s, n in rep['counts'].items()]
    lines += ['', 'By origin: ' + ', '.join(f'{k} {v}' for k, v in sorted(rep['by_origin'].items())) if rep['by_origin'] else 'By origin: none']
    lines += ['', f"Live domains ({len(rep['live_domains'])}): " + (', '.join(rep['live_domains']) or 'none')]
    if rep['nofollow_live']:
        lines.append('Live but nofollow/sponsored/ugc: ' + ', '.join(rep['nofollow_live']))
    lines += ['', f"Overdue follow-ups ({len(rep['overdue_follow_ups'])}):"] + [f"- {o['source_url']} (pitched {o['pitched_at']})" for o in rep['overdue_follow_ups']]
    lines += ['', f"Rows due for a live check: {rep['due_checks']}", '']
    return '\n'.join(lines)


def check(doc: dict, *, ledger_path: Path, out_root: Path, max_rows: int, runner=None) -> list[dict]:
    """Run verify_links.py for due rows (bounded) and record each observation."""
    runner = runner or _run_verify
    results = []
    stamp = time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())
    for row in due_checks(doc)[:max_rows]:
        out_dir = out_root / 'link-checks' / stamp / row['id']
        observation = runner(row['source_url'], row['target_url'], row['id'], out_dir)
        if observation is None:
            results.append({'source_url': row['source_url'], 'outcome': 'runner_failed'})
            continue
        rel_path = (out_dir / 'observation.json').relative_to(ledger_path.parent).as_posix()
        record(doc, observation, observation_path=rel_path)
        results.append({'source_url': row['source_url'], 'outcome': observation['outcome']})
    return results


def _run_verify(source: str, target: str, ident: str, out_dir: Path) -> dict | None:
    cmd = [sys.executable, str(ROOT / 'scripts/marketing/verify_links.py'), '--source', source, '--target', target, '--id', ident,
           '--out', str(out_dir), '--evidence-root', str(out_dir.parents[2])]
    subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    path = out_dir / 'observation.json'
    return json.loads(path.read_text()) if path.is_file() else None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--base', type=Path, required=True, help='business root holding marketing/')
    sub = ap.add_subparsers(dest='command', required=True)
    init = sub.add_parser('init'); init.add_argument('--property', required=True)
    imp = sub.add_parser('import-candidates'); imp.add_argument('input', type=Path); imp.add_argument('--at')
    lnk = sub.add_parser('import-links'); lnk.add_argument('input', type=Path)
    st = sub.add_parser('set'); st.add_argument('--source', required=True); st.add_argument('--stage', required=True, choices=STAGES)
    st.add_argument('--at'); st.add_argument('--note'); st.add_argument('--target'); st.add_argument('--opportunity-id')
    rec = sub.add_parser('record'); rec.add_argument('observation', type=Path)
    chk = sub.add_parser('check'); chk.add_argument('--max', type=int, default=20)
    rep = sub.add_parser('report'); rep.add_argument('--markdown', action='store_true')
    args = ap.parse_args()
    ledger_path = args.base / RELATIVE
    try:
        if args.command == 'init':
            if ledger_path.exists():
                raise ValueError(f'{ledger_path} already exists')
            save(ledger_path, new_ledger(args.property))
            print(json.dumps({'status': 'created', 'path': str(ledger_path)})); return 0
        doc = load(ledger_path)
        if args.command == 'import-candidates':
            result = import_candidates(doc, json.loads(args.input.read_text()), candidates_path=_rel(args.input, ledger_path), at=args.at)
        elif args.command == 'import-links':
            result = import_links(doc, json.loads(args.input.read_text()), export_path=_rel(args.input, ledger_path))
        elif args.command == 'set':
            row = set_stage(doc, args.source, args.stage, at=args.at, note=args.note, target_url=args.target, opportunity_id=args.opportunity_id)
            result = {'source_url': row['source_url'], 'stage': row['stage']}
        elif args.command == 'record':
            row = record(doc, json.loads(args.observation.read_text()), observation_path=_rel(args.observation, ledger_path))
            result = {'source_url': row['source_url'], 'stage': row['stage'], 'outcome': row['last_observation']['outcome']}
        elif args.command == 'check':
            result = check(doc, ledger_path=ledger_path, out_root=ledger_path.parent, max_rows=args.max)
        else:
            rep_doc = report(doc)
            if args.markdown:
                ledger_path.with_suffix('.md').write_text(render(rep_doc), encoding='utf-8')
            print(json.dumps(rep_doc, indent=2)); return 0
        save(ledger_path, doc)
        print(json.dumps({'status': 'ok', 'result': result})); return 0
    except (OSError, ValueError, KeyError) as exc:
        print(json.dumps({'status': 'unavailable', 'reason': str(exc)})); return 1


def _rel(path: Path, ledger_path: Path) -> str:
    try:
        return path.absolute().relative_to(ledger_path.parent.absolute()).as_posix()
    except ValueError:
        return path.absolute().as_posix()


if __name__ == '__main__':
    raise SystemExit(main())
