# Search-Visibility Review Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the five verified defects raised by the independent implementation review, so the recorded-observation pilot cannot report movement or coverage that did not occur.

**Architecture:** Three sequential tasks. Tasks 1 and 2 both rewrite `scripts/monitoring/ai_answer_probe.py` and its test and must not run in parallel; Task 3 edits two instruction documents that no other task touches.

**Tech Stack:** Python 3 stdlib only (`argparse`, `json`, `pathlib`, `datetime`). No network, no credentials, no new dependencies.

**Spec:** `docs/digital-marketing-optimization-plan.md` (§3.1 measurement contract)

**Review being addressed:** `docs/search-visibility-implementation-review-2026-09-20.md`

## Global Constraints

- The module stays **offline**. The complete import list may only be `argparse`, `json`, `pathlib`, `datetime`. No `requests`, `urllib`, `http.client`, `httpx`, `socket`, `os.environ`, `getenv`, `subprocess`, `ssl`, `urlopen`. None of the four `requires_env` keys registered in `config/source-capabilities.json` may be read.
- Never `git add -A` or `git commit -a`. Stage only the exact files listed in each task.
- Model output is **observation data, never customer-demand evidence**. Failed or credit-blocked probes are coverage gaps (`unknown`), **never absence of mention**.
- There is no "own-brand lane" in this repo. Do not use that phrase.
- Do not modify `scripts/route_workflow.py` or `config/workflow-routes.json`.
- Do not weaken an existing test to make a change pass. Where a test encodes the *old* (defective) contract, the task says so explicitly and states what the corrected contract is.

## Verified findings this plan fixes

All five were reproduced against the reviewed tree before this plan was written.

| ID | Defect | Evidence |
| --- | --- | --- |
| F1 | Repeated observations collapse to last-row-wins, so identical windows report opposite movement depending on file order | Prior `[rep1 false, rep2 true]` + identical current → one reported *loss*; reversing only the prior file order → one reported *gain* |
| F2 | The panel is validated for non-emptiness but never used, so missing observations vanish from coverage | Panel naming `p01`,`p02` + a recording containing only `not_in_panel` → exit 0, `coverage_gaps: []`. Empty recording → exit 0, `coverage_gaps: []` |
| F3 | Successful observations may omit `locale`/`timestamp`/`answer_text`, and `prompt_type` is excluded from the comparison key | Stripping all three is accepted, producing `null`s; a `brand_seeded` row compares against an `unbranded_discovery` row as a normal change |
| F4 | Accepted owner actions are persisted as `open_blockers`, misrepresenting optional follow-up as a dependency | `references/owner-actions.md:7` |
| F5 | The DEO procedure prescribes shipping/return markup at the wrong scope | `deo-agent-readiness.md:5` pairs an organization-scoped return policy with an offer-scoped shipping type, labelling both "Organization-level" |

F2 and F3 are additionally **conformance failures against the spec**: line 75 requires diff reports to "compare only compatible successful observations … report panel coverage", and line 74 requires the repetition index to be meaningful.

---

### Task 1: Panel-driven coverage and contextual validation (F2, F3-validation)

**Files:**
- Modify: `scripts/monitoring/ai_answer_probe.py`
- Test: `tests/test_ai_answer_probe.py`

**Interfaces:**
- Consumes: nothing from other tasks.
- Produces: `load_panel(raw)` → validated panel dict; `build_summary(rows, prior_rows, panel)` — **new required third argument**; `_usable_timestamp(value)` → validated timestamp string. Task 2 relies on `build_summary`'s new signature and on `KEY` containing `prompt_type`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_ai_answer_probe.py`:

```python
PANEL = {
    'prompts': [
        {'id': 'p01', 'version': 1, 'type': 'unbranded_discovery', 'text': 'Which provider?'},
        {'id': 'p02', 'version': 1, 'type': 'educational', 'text': 'How does this work?'},
    ],
}


def test_success_without_context_is_rejected():
    for missing in ('locale', 'timestamp', 'answer_text'):
        raw = {k: v for k, v in BASE.items() if k != missing}
        with pytest.raises(ValueError, match=missing):
            normalize_observation(raw)


def test_unparseable_timestamp_rejected():
    with pytest.raises(ValueError, match='timestamp'):
        obs(timestamp='last Tuesday')
    with pytest.raises(ValueError, match='timezone'):
        obs(timestamp='2026-09-20T10:00:00')


def test_panel_requires_id_version_type_text():
    with pytest.raises(ValueError, match='prompts'):
        load_panel({'prompts': []})
    with pytest.raises(ValueError, match='id'):
        load_panel({'prompts': [{'version': 1, 'type': 'educational', 'text': 'x'}]})
    with pytest.raises(ValueError, match='version'):
        load_panel({'prompts': [{'id': 'p01', 'type': 'educational', 'text': 'x'}]})
    with pytest.raises(ValueError, match='type'):
        load_panel({'prompts': [{'id': 'p01', 'version': 1, 'text': 'x'}]})
    with pytest.raises(ValueError, match='duplicate'):
        load_panel({'prompts': [dict(PANEL['prompts'][0]), dict(PANEL['prompts'][0])]})


def test_missing_panel_prompts_are_reported_as_unknown():
    summary = build_summary([obs(prompt_id='p01')], [], load_panel(PANEL))
    gaps = {(g['prompt_id'], g['reason']) for g in summary['coverage_gaps']}
    assert gaps == {('p02', 'missing_no_observation')}
    assert summary['unmeasured'] is False


def test_empty_recording_is_unmeasured_not_zero_gaps():
    summary = build_summary([], [], load_panel(PANEL))
    assert summary['unmeasured'] is True
    assert {g['prompt_id'] for g in summary['coverage_gaps']} == {'p01', 'p02'}


def test_off_panel_rows_are_separated_not_counted_as_coverage():
    summary = build_summary([obs(prompt_id='not_in_panel')], [], load_panel(PANEL))
    assert summary['off_panel'] == {'count': 1, 'prompt_ids': ['not_in_panel']}
    assert {g['prompt_id'] for g in summary['coverage_gaps']} == {'p01', 'p02'}
    assert summary['unmeasured'] is True


def test_declared_engines_and_repetitions_produce_coverage_gaps():
    panel = load_panel({**PANEL, 'engines': ['openai', 'perplexity'], 'repetitions': 2})
    summary = build_summary([obs(prompt_id='p01', engine='openai')], [], panel)
    gaps = {(g['prompt_id'], g.get('engine'), g['reason']) for g in summary['coverage_gaps']}
    assert ('p01', 'perplexity', 'missing_engine_observation') in gaps
    assert ('p01', 'openai', 'insufficient_repetitions') in gaps
```

Update the import line to `from scripts.monitoring.ai_answer_probe import normalize_observation, diff_observations, build_summary, load_panel`.

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_ai_answer_probe.py -q`
Expected: FAIL — `ImportError: cannot import name 'load_panel'`, and the context tests fail because the three fields are currently optional.

- [ ] **Step 3: Implement panel loading and contextual validation**

In `scripts/monitoring/ai_answer_probe.py`, add `from datetime import datetime` to the imports, add `'prompt_type'` to `KEY` (after `'locale'`), and add:

```python
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
```

In `normalize_observation`, inside the `status == 'success'` branch and **before** the `TRACKED` loop, add:

```python
        if not isinstance(row['locale'], str) or not row['locale']:
            raise ValueError('locale: nonempty string required on success; comparison needs collection context')
        if not isinstance(row['answer_text'], str) or not row['answer_text']:
            raise ValueError('answer_text: nonempty string required on success; a claim must retain its source answer')
        _usable_timestamp(row['timestamp'])
```

- [ ] **Step 4: Implement panel-driven coverage in `build_summary`**

```python
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
```

Then rewrite `build_summary` to take the panel and use it:

```python
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
```

- [ ] **Step 5: Wire the panel through `main()` and fail closed when unmeasured**

Replace the panel validation block in `main()` with:

```python
        panel = load_panel(json.loads(args.panel.read_text()))
```

and after `summary = build_summary(rows, prior, panel)`, replace the `print` tail with:

```python
    if summary['unmeasured']:
        summary['status'] = 'unmeasured'
        print(json.dumps(summary, default=str))
        return True
    print(json.dumps({'status': 'pass', 'out': str(args.out), **summary}, default=str))
    return False
```

Add to the `report.md` lines, after the `Observations:` line:

```python
    lines.append(f"Coverage: {summary['coverage']['covered_prompts']}/"
                 f"{summary['coverage']['declared_prompts']} declared prompts fully covered; "
                 f"gaps: {len(summary['coverage_gaps'])}")
    if summary['off_panel']['count']:
        lines.append(f"Off-panel rows (excluded from coverage): {summary['off_panel']['count']}")
```

Preserve the `out` directory write of `evidence.jsonl` for **all** rows — including off-panel ones — so nothing is silently dropped from the raw record.

- [ ] **Step 6: Update the test that encoded the old contract (plus the import line)**

`test_summary_reports_coverage_gap_for_failed_engine` called `build_summary(rows, prior_rows=[])` with no panel; it must now pass a panel and assert the failure appears as a panel-scoped gap:

```python
def test_summary_reports_coverage_gap_for_failed_engine():
    rows = [obs(engine='perplexity', status='error', brand_mentioned=None,
                url_cited=None, recommended=None, answer_text='')]
    summary = build_summary(rows, [], load_panel({'prompts': [
        {'id': 'p01', 'version': 1, 'type': 'unbranded_discovery', 'text': 'Which provider?'}]}))
    assert summary['coverage_gaps'] == [
        {'prompt_id': 'p01', 'prompt_version': 1, 'prompt_type': 'unbranded_discovery',
         'engine': 'perplexity', 'reason': 'error'}]
    assert summary['boundary'] == (
        'observation of configured surfaces only; not customer-demand evidence; failures are unknown, not absence'
    )
```

Any other call site passing `prior_rows=` positionally or by keyword must be updated to the new three-argument form. Do not delete a test that still expresses a valid requirement; adapt it.

- [ ] **Step 7: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_ai_answer_probe.py -q`
Expected: PASS, and the count is the original 8 plus the 7 new cases.

- [ ] **Step 8: Prove the empty-recording defect is closed end to end**

Run the review's own reproduction shape: a panel naming `p01`/`p02` with an empty recording must now exit **1** and report `unmeasured: true` with both prompts named as gaps — not exit 0 with `coverage_gaps: []`.

- [ ] **Step 9: Commit**

```bash
git add scripts/monitoring/ai_answer_probe.py tests/test_ai_answer_probe.py
git commit -m "fix: derive probe coverage from the selected panel"
```

---

### Task 2: Order-independent, repetition-aware comparison (F1, F3-comparison)

**Files:**
- Modify: `scripts/monitoring/ai_answer_probe.py`
- Test: `tests/test_ai_answer_probe.py`

**Interfaces:**
- Consumes: `build_summary(rows, prior_rows, panel)` and the `prompt_type`-bearing `KEY` from Task 1.
- Produces: `diff_observations(current, prior)` returning `changes` (index-matched individual response changes, each carrying `repetition`), `trends` (window-level rates with sample sizes), and `coverage` (including `skipped_unpaired`, `prior_window`, `current_window`, `overlapping_windows`).

- [ ] **Step 1: Write the failing tests**

```python
def test_reordering_the_prior_file_does_not_change_the_result():
    prior = [obs(repetition=1, brand_mentioned=False), obs(repetition=2, brand_mentioned=True)]
    current = [dict(r, timestamp='2026-09-21T10:00:00Z') for r in prior]
    assert diff_observations(current, prior)['changes'] == []
    assert diff_observations(current, list(reversed(prior)))['changes'] == []


def test_identical_windows_report_no_movement_in_either_direction():
    prior = [obs(repetition=1, brand_mentioned=False), obs(repetition=2, brand_mentioned=True)]
    current = [dict(r, timestamp='2026-09-21T10:00:00Z') for r in prior]
    trends = diff_observations(current, prior)['trends']
    mention = [t for t in trends if t['field'] == 'brand_mentioned'][0]
    assert mention['prior_rate'] == mention['current_rate'] == 0.5
    assert mention['delta'] == 0
    assert mention['prior_n'] == mention['current_n'] == 2


def test_duplicate_repetition_in_one_window_is_rejected():
    with pytest.raises(ValueError, match='duplicate'):
        diff_observations([obs(repetition=1), obs(repetition=1, brand_mentioned=False)], [])


def test_prompt_type_is_part_of_comparison_identity():
    result = diff_observations([obs(prompt_type='brand_seeded')], [obs(brand_mentioned=False)])
    assert result['changes'] == []
    assert result['coverage']['skipped_incompatible'] == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_ai_answer_probe.py -q`
Expected: FAIL — the reorder test reports a spurious change in one direction, `trends` does not exist, and duplicates are silently collapsed instead of rejected.

- [ ] **Step 3: Implement the corrected comparison**

Replace `diff_observations` with:

```python
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


def diff_observations(current, prior):
    indexed_current, indexed_prior = _index_success(current), _index_success(prior)
    by_current, by_prior = _group(indexed_current), _group(indexed_prior)

    changes, trends = [], []
    compared, skipped_incompatible, skipped_unpaired = 0, 0, 0

    for key in sorted(set(by_current) | set(by_prior)):
        cur, old = by_current.get(key), by_prior.get(key)
        if cur is None or old is None:
            skipped_incompatible += len(cur or old)
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
```

Add to the `report.md` lines in `main()`:

```python
    if summary['diff']:
        cov = summary['diff']['coverage']
        lines.append(f"Compared: {cov['compared']} probe targets; "
                     f"response changes: {len(summary['diff']['changes'])}; "
                     f"unpaired repetitions: {cov['skipped_unpaired']}")
        if cov['overlapping_windows']:
            lines.append('Warning: prior and current collection windows overlap; '
                         'treat movement as unestablished.')
        for t in summary['diff']['trends']:
            lines.append(f"{t['prompt_id']}/{t['engine']}/{t['field']}: "
                         f"{t['prior_rate']:.2f} (n={t['prior_n']}) -> "
                         f"{t['current_rate']:.2f} (n={t['current_n']})")
```

- [ ] **Step 4: Update tests that encoded the old comparison contract**

`test_diff_compares_only_compatible_successful` and `test_diff_skips_incompatible_config` were written against the per-row last-wins semantics. Adapt them:

- compatible case: assert the `p01` trend moves (`prior_rate` 0.0 → `current_rate` 1.0) **and** that exactly one index-matched change is reported carrying `repetition: 1`; keep the `compared`/`skipped_failed` assertions.
- incompatible case: keep asserting no movement and `skipped_incompatible == 2`.

Do not simply delete them — they encode real requirements (only compatible successful observations are compared; failures are skipped, not treated as absence). Their *encoding* changes because the corrected contract distinguishes response changes from trend.

- [ ] **Step 5: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_ai_answer_probe.py -q`
Expected: PASS.

- [ ] **Step 6: Re-run the review's exact F1 reproduction**

The two windows must now yield **no change** in both file orders, and the trend must read 0.50 (n=2) → 0.50 (n=2). Confirm the reorder produces byte-identical output.

- [ ] **Step 7: Commit**

```bash
git add scripts/monitoring/ai_answer_probe.py tests/test_ai_answer_probe.py
git commit -m "fix: compare repetitions as samples so file order cannot flip a result"
```

---

### Task 3: Instruction corrections (F4, F5)

**Files:**
- Modify: `references/owner-actions.md:7`
- Modify: `.agents/skills/brand-website-designer-builder/references/deo-agent-readiness.md:5`

**Interfaces:**
- Consumes: nothing. Independent of Tasks 1–2; touches no file they touch.

- [ ] **Step 1: Correct the owner-action persistence rule (F4)**

Replace the persistence sentence in `references/owner-actions.md:7`. The current rule routes every accepted action beyond the first into `open_blockers`; acceptance does not make work a blocker, and `references/workspace-lifecycle.md:82` and `AGENTS.md:34` both surface that field on resume as work preventing progress.

New rule: `open_blockers` is reserved for **actual dependencies and genuine blockers**. A concise **ordered set** of accepted next steps goes in `next_action` (a single string in both `schemas/project-manifest.schema.json` and `schemas/research-manifest.schema.json`), and the full per-action rows are rendered in the project's `owner-actions.md`. Existing unrelated blockers must be preserved, and the `proposed`/`accepted` distinction must remain visible.

- [ ] **Step 2: Correct the DEO markup scopes (F5)**

Verified against Google's live documentation on 2026-09-20:

- Organization-level standard policy: `Organization.hasMerchantReturnPolicy` → `MerchantReturnPolicy`, and `Organization.hasShippingService` → `ShippingService`.
- Offer-level override: `Offer.hasMerchantReturnPolicy` → `MerchantReturnPolicy`, and `Offer.shippingDetails` → `OfferShippingDetails`.
- Product/offer-level markup **outranks** organization-level markup, and offer-level supports a **narrower** property set.

`OfferShippingDetails` is therefore **not** an organization-level type. Replace the ambiguous prescription in `deo-agent-readiness.md:5` with the correct property/type relationships, keeping the existing owner-supplies-truth framing and the "matching the visible policy text exactly" requirement, and link the two current Google documentation pages. Keep organization return-policy guidance separate from offer-level shipping details.

Do not add a generic schema validator.

- [ ] **Step 3: Verify no other file repeats the wrong scope**

Grep the tree for `OfferShippingDetails` and `MerchantReturnPolicy` and confirm no other document pairs them at the wrong level. Report what you found.

- [ ] **Step 4: Commit**

```bash
git add references/owner-actions.md .agents/skills/brand-website-designer-builder/references/deo-agent-readiness.md
git commit -m "fix: reserve open_blockers for dependencies and correct DEO markup scopes"
```

---

## Final verification (after all three tasks)

- [ ] All four gates: `bash scripts/validate_setup.sh` → 0 errors; `python3 scripts/run_evals.py` → all structural checks pass; `python3 scripts/validate_skill_routes.py` → `{"passed": true, "errors": []}`; `python3 -m pytest tests/ -q` → 0 failures.
- [ ] Offline grep still clean: no network or credential import in `scripts/monitoring/ai_answer_probe.py`.
- [ ] The review's reproduction appendix now shows: reorder-invariant, off-panel rows separated, empty recording unmeasured and non-zero exit, missing context rejected.
- [ ] Whole-branch review on the most capable model before merge.

## Notes carried into execution

- The review's F1–F3 corrections **change the module's output contract**. Tasks 1 and 2 must update the tests that encoded the old contract, and each such update must be justified in the task report as a contract correction rather than a test weakened to pass.
- An empty recording now exits non-zero. That is deliberate fail-closed behaviour: no successful observation means nothing was measured, which must not read as a clean result.