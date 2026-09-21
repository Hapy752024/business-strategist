"""Normalize and diff AI answer-engine observations; observations are not demand evidence."""
import argparse
import json
import os
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
    panel_version = raw.get('panel_version')
    # Validated at the boundary so two windows can only ever be compared
    # like-for-like: `1` and `'1'` are different values that render identically.
    if panel_version is not None and (not isinstance(panel_version, str) or not panel_version):
        raise ValueError('panel.panel_version: nonempty string required when present')
    return {'declared': declared, 'engines': engines, 'repetitions': repetitions,
            'panel_version': panel_version}


def _stamp(value):
    return datetime.fromisoformat(value.replace('Z', '+00:00'))


def _usable_timestamp(value):
    if not isinstance(value, str) or not value:
        raise ValueError('timestamp: nonempty ISO-8601 string required on success')
    try:
        parsed = _stamp(value)
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


def _index_success(rows, label='successful observation'):
    """Index successful rows by (comparison key, repetition), rejecting shared indices.

    Two rows sharing a repetition index are not independent samples, so they fail
    closed rather than being silently collapsed or partially credited as coverage.
    """
    seen = {}
    for r in rows:
        if r.get('status') != 'success':
            continue
        k = (_key(r), r['repetition'])
        if k in seen:
            raise ValueError(
                f"duplicate {label} for prompt {r['prompt_id']} "
                f"engine {r['engine']} repetition {r['repetition']}: "
                'repetitions are independent samples and must be retained, not overwritten; '
                'two rows sharing a repetition index are not independent samples')
        seen[k] = r
    return seen


def _group(indexed):
    grouped = {}
    for (key, _rep), row in indexed.items():
        grouped.setdefault(key, []).append(row)
    return grouped


def _window(rows):
    stamps = [r['timestamp'] for r in rows if r.get('status') == 'success']
    if not stamps:
        return None
    # Ordered by the instant each timestamp denotes, not by its literal text: the
    # same instant may be written with different offsets and still be one window.
    return {'start': min(stamps, key=_stamp), 'end': max(stamps, key=_stamp)}


def _rate(rows, field):
    return sum(1 for r in rows if r[field]) / len(rows) if rows else None


def _fmt_rate(value):
    return 'n/a' if value is None else f'{value:.2f}'


def _fmt_version(value):
    return 'unversioned' if value is None else str(value)


def _comparable_version(value):
    """A panel version is comparable only when it is a nonempty string.

    `load_panel` already refuses a non-string version, but this function is also a
    library entry point: comparing `1` with `'1'` would report a change that did not
    happen, so an unusable pair is left unknown instead.
    """
    return isinstance(value, str) and bool(value)


def _panel_version_compatibility(panel_versions):
    """Compare the panel versions the two windows were collected under.

    `compatible` is None when either version is unknown: an unverifiable pair must
    not be reported as compatible, but it also cannot be shown to have changed.
    """
    current_version = (panel_versions or {}).get('current')
    prior_version = (panel_versions or {}).get('prior')
    if not _comparable_version(current_version) or not _comparable_version(prior_version):
        compatible = None
    else:
        compatible = current_version == prior_version
    return {'current': current_version, 'prior': prior_version, 'compatible': compatible}


def diff_observations(current, prior, panel_versions=None):
    indexed_current = _index_success(current, 'recorded observation')
    indexed_prior = _index_success(prior, 'prior observation')
    by_current, by_prior = _group(indexed_current), _group(indexed_prior)
    versions = _panel_version_compatibility(panel_versions)

    changes, trends = [], []
    compared, skipped_incompatible, skipped_unpaired = 0, 0, 0
    if versions['compatible'] is False:
        # The measurement contract compares only observations from the same panel
        # version, so a changed panel is recorded as incompatible rather than
        # silently compared as if the two windows asked the same questions.
        skipped_incompatible = len(indexed_current) + len(indexed_prior)
    else:
        for key in sorted(set(by_current) | set(by_prior)):
            cur, old = by_current.get(key), by_prior.get(key)
            if cur is None or old is None:
                # Both sides count: a prior-only observation was dropped just as a
                # current-only one was added, and neither has a comparable counterpart.
                skipped_incompatible += len(cur or []) + len(old or [])
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
                       and _stamp(prior_window['start']) <= _stamp(current_window['end'])
                       and _stamp(current_window['start']) <= _stamp(prior_window['end']))
    return {'changes': changes, 'trends': trends,
            'coverage': {'current': len(current), 'prior': len(prior), 'compared': compared,
                         'skipped_incompatible': skipped_incompatible,
                         'skipped_failed': sum(1 for r in current if r.get('status') != 'success'),
                         # Prior-window failures are counted separately: a credit-blocked
                         # prior engine is a reported coverage gap, never a clean comparison.
                         'skipped_failed_prior': sum(1 for r in prior if r.get('status') != 'success'),
                         'skipped_unpaired': skipped_unpaired,
                         'prior_window': prior_window, 'current_window': current_window,
                         'overlapping_windows': overlapping,
                         'panel_version': versions}}


def _panel_coverage(rows, panel):
    # Shared repetition indices are not independent samples. `main` rejects them at
    # load time, but coverage is also reachable as a library call, and whether a
    # window earns credit for a prompt must not depend on whether an unrelated
    # `--prior` window was supplied. Enforced here so both paths fail closed alike.
    _index_success(rows, 'recorded observation')
    declared, declared_engines = panel['declared'], panel['engines']
    on_panel_keys = {(p['prompt_id'], p['prompt_version'], p['prompt_type']) for p in declared}
    on_panel, off_panel_ids = [], []
    for r in rows:
        if (r['prompt_id'], r['prompt_version'], r['prompt_type']) not in on_panel_keys:
            off_panel_ids.append(r['prompt_id'])
            continue
        if declared_engines is not None and r['engine'] not in declared_engines:
            # An undeclared engine is not a surface the panel selected, so the row
            # cannot stand as coverage for the prompt it names.
            off_panel_ids.append(r['prompt_id'])
            continue
        on_panel.append(r)

    gaps, covered = [], 0
    for p in declared:
        mine = [r for r in on_panel if (r['prompt_id'], r['prompt_version'], r['prompt_type'])
                == (p['prompt_id'], p['prompt_version'], p['prompt_type'])]
        if not mine:
            gaps.append({**p, 'reason': 'missing_no_observation'})
            continue
        engines = declared_engines or sorted({r['engine'] for r in mine})
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
            if want is None:
                continue
            # Only distinct repetition indices are samples. Rows sharing an index are
            # rejected before coverage is computed, so a shortfall here is reported as
            # insufficient distinct samples.
            samples = {r['repetition'] for r in ok}
            if len(samples) < want:
                gaps.append({**p, 'engine': engine, 'reason': 'insufficient_repetitions',
                             'expected': want, 'observed': len(samples)})
                fully_covered = False
        covered += 1 if fully_covered else 0

    successful = [r for r in on_panel if r['status'] == 'success']
    return {'gaps': gaps, 'covered': covered, 'declared': len(declared),
            'successful_observations': len(successful),
            'off_panel': {'count': len(off_panel_ids),
                          'prompt_ids': sorted(set(off_panel_ids))},
            'unmeasured': not successful}


def build_summary(rows, prior_rows, panel, prior_panel_version=None, prior_supplied=None):
    pc = _panel_coverage(rows, panel)
    # A supplied-but-empty prior is a different state from no prior at all: the
    # probe's own zero-row run writes an empty evidence.jsonl, and rendering that as
    # "no prior window" would present unknown as absence. `prior_supplied=None`
    # infers the flag from the rows for callers that only have the rows.
    has_prior = bool(prior_rows) if prior_supplied is None else prior_supplied
    diff = diff_observations(
        rows, prior_rows,
        {'current': panel['panel_version'], 'prior': prior_panel_version}
    ) if has_prior else None
    # A measured run whose panel changed between windows abandoned the comparison,
    # so the machine-readable status must not read `pass`. `unmeasured` outranks it:
    # with no successful observation there is no measurement to declare incomparable.
    if pc['unmeasured']:
        status = 'unmeasured'
    elif diff and diff['coverage']['panel_version']['compatible'] is False:
        status = 'incomparable'
    else:
        status = 'pass'
    return {'status': status,
            'observations': len(rows),
            'panel_version': panel['panel_version'],
            'coverage': {'declared_prompts': pc['declared'], 'covered_prompts': pc['covered'],
                         'successful_observations': pc['successful_observations']},
            'coverage_gaps': sorted(pc['gaps'], key=lambda g: (g['prompt_id'], g.get('engine') or '')),
            'off_panel': pc['off_panel'],
            'unmeasured': pc['unmeasured'],
            'diff': diff,
            'boundary': 'observation of configured surfaces only; not customer-demand evidence; failures are unknown, not absence'}


def _report_lines(summary):
    coverage = summary['coverage']
    lines = ['# AI-answer observation report', '', f"Boundary: {summary['boundary']}", '',
             f"Status: {summary['status']}",
             f"Panel version: {_fmt_version(summary['panel_version'])}",
             f"Observations: {summary['observations']}; coverage gaps: {len(summary['coverage_gaps'])}",
             f"Coverage: {coverage['covered_prompts']}/{coverage['declared_prompts']} "
             'declared prompts fully covered']
    if summary['unmeasured']:
        lines.append('No successful observation: nothing was measured; failures are unknown, not absence.')
    for gap in summary['coverage_gaps']:
        # Identified by prompt id and version: a panel declaring the same id at two
        # versions would otherwise render two indistinguishable gap rows.
        target = f"{gap['prompt_id']} v{gap['prompt_version']}"
        target += f"/{gap['engine']}" if gap.get('engine') else ''
        lines.append(f"- coverage gap: {target} ({gap['reason']})")
    if summary['off_panel']['count']:
        lines.append(f"Off-panel rows (excluded from coverage): {summary['off_panel']['count']} "
                     f"[{', '.join(summary['off_panel']['prompt_ids'])}] "
                     '(matched on prompt id, version, type and declared engine, so an id that is '
                     'also declared in the panel appears here when its version, type or engine '
                     'was not selected)')
    diff = summary['diff']
    if diff:
        cov = diff['coverage']
        lines.append(f"Compared: {cov['compared']} probe targets; "
                     f"response changes: {len(diff['changes'])}; "
                     f"unpaired repetitions: {cov['skipped_unpaired']}; "
                     f"skipped incompatible: {cov['skipped_incompatible']}; "
                     f"skipped failed: {cov['skipped_failed']}; "
                     f"skipped failed prior: {cov['skipped_failed_prior']}")
        if cov['skipped_failed_prior']:
            lines.append(f"Warning: the prior window contained {cov['skipped_failed_prior']} "
                         'failed observation(s); failures are unknown, not absence, so the '
                         'comparison is partial and the prior window is not a clean baseline.')
        if cov['prior'] == 0:
            lines.append('Warning: the prior window was supplied but contains no observations; '
                         'no movement is comparable.')
        elif cov['prior_window'] is None:
            lines.append('Warning: no successful prior observation established a prior collection '
                         'window; no movement is comparable.')
        versions = cov['panel_version']
        if versions['compatible'] is False:
            lines.append(f"Warning: panel version differs between windows "
                         f"({_fmt_version(versions['prior'])} -> {_fmt_version(versions['current'])}); "
                         'observations from different panel versions are not comparable, so no '
                         'movement is reported.')
        elif versions['compatible'] is None:
            # Testing `compatible is None` rather than `prior is None`: an unversioned
            # *current* panel with a versioned prior also compares as unknown, and a
            # reader must be able to tell `null` from `true` in both directions.
            lines.append('Panel-version comparability unverified '
                         f"(current: {_fmt_version(versions['current'])}, "
                         f"prior: {_fmt_version(versions['prior'])}); an unversioned or "
                         'unsupplied panel version cannot be shown to be comparable.')
        if cov['overlapping_windows']:
            lines.append('Warning: prior and current collection windows overlap; '
                         'treat movement as unestablished.')
        for t in diff['trends']:
            lines.append(f"{t['prompt_id']}/{t['engine']}/{t['field']}: "
                         f"{_fmt_rate(t['prior_rate'])} (n={t['prior_n']}) -> "
                         f"{_fmt_rate(t['current_rate'])} (n={t['current_n']})")
    return lines


def _discard_tree(path):
    """Best-effort removal of a directory tree a run staged or set aside."""
    if path is None or not path.exists():
        return
    try:
        for child in path.iterdir():
            # A symlink is unlinked rather than followed: recursing through one would
            # delete content that lives outside the directory being discarded.
            if child.is_dir() and not child.is_symlink():
                _discard_tree(child)
            else:
                child.unlink()
        path.rmdir()
    except OSError:
        pass


def _rename(src, dst):
    """Rename a path; a module-level seam so tests can inject a publish failure."""
    src.rename(dst)


def _publish(out, staging, trash):
    """Publish staged artifacts by swapping directories into place.

    The outgoing `out` is renamed aside and only then is the staging directory
    renamed into its place, so a crash between the two renames leaves no `out` at
    all — which reads as "the run did not complete" — rather than a tree mixing a
    fresh evidence file with a previous run's pass-claiming summary. Absent is
    recoverable; misleading is not.
    """
    if out.is_dir():
        _rename(out, trash)
    _rename(staging, out)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--panel', type=Path, required=True)
    p.add_argument('--recorded', type=Path, required=True)
    p.add_argument('--prior', type=Path)
    p.add_argument('--prior-panel', type=Path,
                   help='the panel.json preserved alongside the prior run output; when supplied, '
                        'a changed panel version is recorded and the windows are not compared')
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    staging = trash = None
    try:
        # Resolved before the staging name is derived: `.` and `..` are valid
        # destinations with no usable name of their own, and the staging directory
        # must be a sibling of `out` for the rename to publish it atomically.
        out = args.out.resolve()
        if not out.name:
            raise ValueError(f'--out: cannot publish into the filesystem root ({out})')
        if out.exists() and not out.is_dir():
            raise ValueError(f'--out: existing path is not a directory ({out})')
        # The panel is parsed once and the copy is rendered from that object, so the
        # panel.json in `out` is the panel that was measured rather than whatever a
        # second read of the path happened to return.
        panel_raw = json.loads(args.panel.read_text())
        panel = load_panel(panel_raw)
        rows = [normalize_observation(json.loads(line)) for line in args.recorded.read_text().splitlines() if line.strip()]
        prior = [normalize_observation(json.loads(line)) for line in args.prior.read_text().splitlines() if line.strip()] if args.prior else []
        prior_panel = load_panel(json.loads(args.prior_panel.read_text())) if args.prior_panel else None
        # Validate both files identically before anything is written: a duplicate
        # (comparison key, repetition) is not independent sampling, and the verdict
        # must not depend on whether an unrelated --prior window was supplied.
        _index_success(rows, 'recorded observation')
        _index_success(prior, 'prior observation')
        summary = build_summary(rows, prior, panel,
                                prior_panel_version=prior_panel['panel_version'] if prior_panel else None,
                                prior_supplied=args.prior is not None)
        # Stage every artifact in a directory unique to this process, then publish by
        # renaming the directory into place. Two runs sharing `--out` therefore cannot
        # write into the same staging directory, and no failure path can leave a
        # partially published tree.
        staging = out.parent / f'.{out.name}.staging.{os.getpid()}'
        trash = out.parent / f'.{out.name}.outgoing.{os.getpid()}'
        staging.mkdir(parents=True)
        (staging / 'evidence.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in rows))
        (staging / 'panel.json').write_text(json.dumps(panel_raw))
        (staging / 'report.md').write_text('\n'.join(_report_lines(summary)) + '\n')
        (staging / 'summary.json').write_text(json.dumps(summary, indent=2))
        _publish(out, staging, trash)
    except (OSError, ValueError, AttributeError) as exc:
        print(json.dumps({'status': 'fail', 'errors': [str(exc)]}))
        return True
    except KeyboardInterrupt:
        # An interrupt is a failure like any other and owes the caller the same
        # machine-readable envelope and non-zero exit, not a traceback.
        print(json.dumps({'status': 'fail',
                          'errors': ['interrupted before the output was published']}))
        return True
    finally:
        # Runs for every exit, including KeyboardInterrupt, so neither an unfinished
        # staging tree nor a set-aside previous epoch is left behind.
        _discard_tree(staging)
        _discard_tree(trash)
    print(json.dumps({'out': str(out), **summary}, default=str))
    return summary['status'] != 'pass'


if __name__ == '__main__':
    raise SystemExit(main())
