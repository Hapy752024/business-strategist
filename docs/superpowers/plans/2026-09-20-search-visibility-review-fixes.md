# Search-Visibility Review Fixes Implementation Plan

> Historical executed plan. Do not replay its code or acceptance criteria. Current contract: `references/ai-answer-recordings.md`; current closure plan: `docs/search-visibility-closure-plan-2026-09-21.md`.

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

---

## Round 2 — defects introduced by the Round 1 fixes

A whole-branch adversarial review of Tasks 1–2 returned **CHANGES REQUIRED**: F1–F5 are genuinely closed and could not be falsified, but the fixes left new defects on ordinary inputs. All were reproduced independently before being written here.

### Task 4: probe reporting and coverage identity (findings 1–5, nits a and c)

**Files:** `scripts/monitoring/ai_answer_probe.py`, `tests/test_ai_answer_probe.py`

**Finding 1 — `report.md` cannot distinguish "nothing comparable" from "no movement". MUST FIX.**
Reproduced: panel `{p01}`, prior recorded under `model: gpt-other` → `exit 0`, `status: pass`, and `report.md` reads `Coverage: 1/1 declared prompts fully covered; gaps: 0` / `Compared: 0 probe targets; response changes: 0`. A configuration change — the exact case spec §3.1 requires be tested before trusting trends — renders as a clean, unchanged, fully covered run. `skipped_incompatible` and `skipped_failed` are never printed; gap rows are counted but not identified; `unmeasured` never reaches the file. A credit-blocked engine is likewise invisible: the reader cannot tell which engine failed or that it failed.
*Fix:* print `skipped_incompatible` and `skipped_failed`; list the gap rows (prompt, engine, reason) rather than only counting them; print `unmeasured`/`status`.

**Finding 2 — an undeclared engine suppresses the fail-closed gate. MUST FIX.**
Reproduced: panel `{prompts:[p01], engines:['openai']}`, recording = one success from `engine: 'gemini'` → `exit 0`, `unmeasured: false`, `covered_prompts: 0/1`, `off_panel: {count: 0}`. Nothing the panel declared was measured, the undeclared row appears in no counter, and the run is not fail-closed.
*Cause:* `_panel_coverage` decides on/off-panel from `(prompt_id, prompt_version, prompt_type)` only — `engine` is absent — while `unmeasured` is `not successful` over all on-panel successes regardless of the declared engine set.
*Fix:* when `panel['engines']` is declared, a row whose engine is not in that set is **off-panel** (separated, not counted toward coverage), and `unmeasured` is computed over successes matching the declared engine set.

**Finding 3 — duplicate repetitions satisfy coverage but are rejected by comparison. SHOULD FIX.**
Same recording, two contradictory verdicts: panel `repetitions: 2` with rows `[rep1, rep1]` → `Coverage: 1/1 fully covered`, `gaps: []`, `exit 0`; add `--prior` and the same run hard-fails on duplicate `(key, repetition)`. Two rows sharing a repetition index are not independent samples.
*Fix:* count **distinct** repetition indices for the `repetitions` comparison, and report a `duplicate_repetitions` gap so coverage and comparison agree.

**Finding 4 — `skipped_incompatible` undercounts prior-only observations, and a test locks the bug in. SHOULD FIX.**
`skipped_incompatible += len(cur or [])` should be `len(cur or []) + len(old or [])`. Reproduced: prior `[p01, p02]`, current `[p01]` → `skipped_incompatible: 0` although a prior observation was dropped. Worse, `test_diff_skips_incompatible_config` asserts `== 2`, a value only the asymmetric code produces — so the suite **rejects a fix to this line**.
*Fix:* make the count symmetric and update that assertion to the corrected value (4), documenting it as a contract correction.

**Finding 5 — window-overlap detection compares timestamps lexicographically. SHOULD FIX.**
`_window` string-sorts and string-compares, but `_usable_timestamp` accepts any ISO offset and its message claims the offset exists "so collection windows are comparable". Reproduced: prior `2026-09-20T10:00:00Z` vs current `2026-09-20T05:00:00-05:00` — the same instant — → `overlapping_windows: false`, suppressing the "treat movement as unestablished" warning.
*Fix:* compare parsed aware datetimes, not strings.

**Nits:** (a) `summary.json` never contains `status`; add it. (c) `args.out.mkdir` sits outside the `try`, so an unwritable `--out` exits 1 with empty stdout and a raw traceback instead of the documented `{"status": "fail"}` envelope; move it inside.

**Finding 7 — tests that must be added (surviving mutations).** All five survived the current suite:
- `covered += 1` unconditionally — no test asserts `coverage['covered_prompts']`, the headline number in `report.md`.
- `successful = list(on_panel)` (failures counted as coverage) — no test asserts that an all-failed on-panel recording is `unmeasured`. The shipped code is correct; the fail-closed path is unasserted.
- `overlapping = False` — the overlap warning is never exercised.
- `panel.engines` validation disabled — the `load_panel` engines error path is untested.
- removing `sorted()` over comparison keys — the order-invariance test uses a single key, so multi-key order dependence could return unnoticed.

Each of the above needs a test that kills it. Use multi-key inputs for the order-invariance case.

### Task 5: replay-safety and instruction nits (finding 6, nit d)

**Files:** `docs/superpowers/plans/2026-09-20-search-visibility-setup.md`, `.agents/skills/brand-website-designer-builder/references/deo-agent-readiness.md`

**Finding 6 — the errata misses two defective route literals. SHOULD FIX.**
The executed plan still carries the bare tokens the earlier fix dispatch bounded: `"agent readiness"` at lines 320 and 350, `"brand mentions"` at lines 247, 320 and 354. Shipped `config/workflow-routes.json` correctly carries `"agent readiness audit"` / `"website agent readiness"` and `"track brand mentions"` / `"own-brand mentions"`, but the plan's own progress log records that these bare tokens were must-fix defects (they stole voice-of-customer requests and hijacked app-UI prompts) — and only the `"AEO"` token was corrected in the plan text. A replayer following the errata's instruction would reintroduce both.
*Fix:* correct those literals to the shipped bounded tokens, and extend the errata to name them plus the `prompt_type`-in-`KEY` omission that was half of F3.

**Nit d.** `deo-agent-readiness.md:5` states offer-level "outranks" organization-level but omits Google's stated *preference* for a site-wide organization policy with offer-level reserved for overrides. Add that qualification.

---

## Round 3 — the artifact surface

A Round 2 adversarial review returned **CHANGES REQUIRED**: Round 2's own mandate (findings 1–5 + nits) is genuinely closed and all five claimed mutation kills reproduce, but the rewritten report/coverage surface is under-asserted — **18 mutations survived** — and two evidence-discipline holes remain open in that same area.

**Root cause, and why this round is shaped differently.** The probe renders one internal state four ways: `report.md`, `summary.json`, stdout, and the exit code. Every test asserts the internal dict. So each review round finds a *rendering* that lies while the dict is correct. Findings 1 and 3 below are both exactly that. Patching them individually invites a Round 4. The durable fix is a test layer that asserts the four renderings against each other, which is why Task 7 exists and why it is not optional.

### Task 6: probe behaviour (findings 1–5, nits 6–8)

**Files:** `scripts/monitoring/ai_answer_probe.py`, `tests/test_ai_answer_probe.py`

**Finding 1 — a credit-blocked prior window renders as a clean pass. MUST FIX.**
Reproduced: prior file = one `status: 'error'` row; current = one success → `exit 0`, and `report.md` reads `Status: pass` / `Coverage: 1/1 declared prompts fully covered` / `Compared: 0 probe targets; … skipped incompatible: 1; skipped failed: 0`. `summary.json`'s `diff.coverage` has no prior-failure field at all, and `prior_window` is `None`.
`skipped_failed` is computed over `current` only; prior rows are dropped by `_index_success` before grouping. Round 2 is what put the misleading `skipped failed: 0` on the page. Spec §3.1 requires a credit-blocked engine to be a *reported* coverage gap.
*Fix:* account for prior-window failures separately (`skipped_failed_prior`), surface them in `report.md` and `summary.json`, and make the report state plainly when the prior window contained failures rather than implying a clean comparison.

**Finding 2 — the panel is neither preserved nor version-checked. SHOULD FIX.**
`build_summary` records `panel_version` but `diff_observations` never receives the panel, so no panel-version compatibility check exists; `main` writes only `evidence.jsonl`, `summary.json`, `report.md`. Reproduced: bumping `panel_version` and editing a prompt's text between windows yields `Status: pass` / `response changes: 1` with no indication the panel changed. Spec §3.1 requires comparing only observations from the "same … panel version", and the external review's correction (`docs/search-visibility-implementation-review-2026-09-20.md:45`) says "Preserve the selected panel alongside the output so a later reader can identify what was measured" — the fix plan dropped that clause.
*Fix:* copy the panel into `--out`; print `panel_version` in `report.md`; compare panel versions between windows and record incompatibility rather than silently comparing across a changed panel.

**Finding 3 — a failed run can leave a `summary.json` claiming `status: pass`. SHOULD FIX.**
`main` writes `summary.json` before `report.md`; a failure on the later write hits the `except`, prints the fail envelope and returns 1 — but the already-written `summary.json` says `pass`. Reproduced: pre-create `out/report.md` as a directory → `exit 1`, fail envelope on stdout, and on-disk `summary.json` with `"status": "pass"`. Round 2's new `status` field is what turns the stale artifact into a false pass claim.
*Fix:* make the output stage atomic — write to a temporary directory and rename on success, or write `summary.json` last — so no failure path leaves a pass-claiming artifact.

**Finding 4 — multi-row window ordering is unasserted. SHOULD FIX.**
`_window` now uses `min`/`max` over parsed instants, but every overlap test uses single-row windows where min/max is trivial. Survivor S13 (restore string sort) inverts the prior window and suppresses the overlap warning while the suite stays green.
*Fix:* add a multi-row, mixed-offset window test that asserts both the window bounds and `overlapping_windows`.

**Finding 5 — duplicate repetitions give opposite verdicts depending on an unrelated flag. SHOULD FIX.**
Without `--prior`: `exit 0` with a `duplicate_repetitions` gap. With `--prior`: `exit 1` and no report, because `_index_success` hard-rejects.
*Fix:* validate duplicate `(entity, repetition)` at load time in `main`, for both files, so both paths behave identically. Two rows sharing a repetition index are not independent samples, so this fails closed consistently. Update the tests that assert the old `duplicate_repetitions` gap accordingly, and justify each change as a contract correction.

**Nits:** (6) `report.md` gap rows must include `prompt_version` — a panel with `p01 v1` and `p01 v2` currently prints two identical `p01` lines. (7) the off-panel line should not be ambiguous when the id is also a declared prompt. (8) the unmeasured stdout envelope should carry `out` like the pass envelope does.

### Task 7: artifact-consistency test layer (the 18 survivors)

**Files:** `tests/test_ai_answer_probe.py`

The review's survivor table lists 18 mutations that the suite does not catch. They cluster on the rendering surface: deleting the overlap-warning line, the trend-line loop, the off-panel line, the `Observations:` line, hard-coding `skipped incompatible: 0`, dropping `prompt_version` or `prompt_type` from the on-panel key, removing `sorted()` on gap or off-panel ids, disabling `panel.repetitions` validation, zeroing `skipped_unpaired`, truncating `prompt_ids`, and emitting `status: fail` or dropping `out` in the success envelope.

Task: add a test layer that asserts the **rendered artifacts**, not the internal dict — for each scenario, parse `report.md`, `summary.json` and stdout and assert they agree with each other and with the exit code. At minimum this must kill every mutation in the review's survivor table, plus the ones Round 2 claimed to kill (re-verified, so a regression is caught).

Every survivor must be named in the task report with the test that now kills it, and the kill verified by applying the mutation, observing the failure, and restoring byte-identically.

### Task 8: errata completeness (finding 9)

**Files:** `docs/superpowers/plans/2026-09-20-search-visibility-setup.md`

The Task 5 literal code block in the executed plan is still defective in ways the errata does not name, so a replayer applying only the four listed corrections still ships a defective probe. Extend the errata to name them, pointing at the fix plan.

**Correction to this task's original framing.** The first draft of this section claimed four defects were present *in the Task 5 literal block*. Two of them are not. The implementer extracted the block (lines 589–694), ran it unmodified, and showed:
- *"duplicate repetitions satisfy declared coverage"* — not present; the block never reads `panel['repetitions']` or `panel['engines']` at all, so there is no declared coverage for duplicates to satisfy. The defect appears only **after** the Round 1 corrections.
- *"window bounds compared lexicographically"* — not present; the block has no window logic whatsoever. The lexicographic comparison is introduced by this fix plan's own Task 2 `_window`, so it is still a replay hazard, but it is a hazard in the correction, not in the block.

Verified in the block: one-sided `skipped_incompatible`, and the absence of gap-row listing and undeclared-engine fail-closed. The implementer also found three omissions this section had not listed — `args.out.mkdir` outside the `try`, the missing panel copy and `panel_version` check, and the fact that the Task 5 **test and Interfaces blocks** encode the superseded contracts (`build_summary(rows, prior_rows)` two-arg, the change shape without `repetition`, `skipped_incompatible == 2`) and would re-lock F1/F4 if copied.

The errata was written to say exactly this rather than assert the block contains defects it does not.

---

## Round 4 — the publish path, and the oracle's blind spots

A Round 3 adversarial review returned **CHANGES REQUIRED**. Round 3 closes Round 2's findings 1–5 and nits 6–8 (all reproduced independently), but the new atomic-write path is **not atomic** and re-creates the defect class it was written to kill; `--out .` is a **regression**; and the new oracle leaves **10 mutations alive**, three of which the plan claimed were killed.

**Why Round 3's fix failed.** The plan offered two options — "write to a temporary directory and rename on success, **or** write `summary.json` last" — and the implementer took the weaker one. Per-file `Path.replace` in a fixed order with `staging.rmdir()` as the last statement *inside* the `try` is not atomic: anything failing after the loop lands in the `except` with all four artifacts already live. **An acceptance criterion written as a choice is not an acceptance criterion.** Task 9 must state one mechanism and require it be tested.

### Task 9: publish-path correctness (findings 1–5, nits 6–9)

**Files:** `scripts/monitoring/ai_answer_probe.py`, `tests/test_ai_answer_probe.py`

**Finding 1 — the publish is not atomic. MUST FIX.** Five reproduced triggers, all leaving a pass-claiming `summary.json` beside a non-zero exit:
- residue in `<out>.staging` → `rc 1`, `{"status":"fail","errors":["Directory not empty: …"]}`, while `out/summary.json` reads `"status": "pass"` and `report.md` reads `Status: pass`. All four renderings disagree.
- `KeyboardInterrupt` during the publish loop (not in the caught tuple) → mixed-epoch `out/`: fresh `evidence.jsonl`+`panel.json` beside the **previous** run's `report.md`/`summary.json`.
- hard kill mid-loop → same mixed-epoch state.
- `out/summary.json` pre-existing as a directory → fail envelope while `out/report.md` is fresh and says `Status: pass`.
- two concurrent runs sharing `--out` → **7 of 10 trials** returned `rc 1` with `out/summary.json` saying `pass`.
*Fix — one mechanism, not a choice:* make the staging directory **unique per process** (so concurrent runs cannot collide), publish by **directory rename** with the outgoing `out` renamed aside first, and clean up staging in a `finally` that also covers `KeyboardInterrupt`. Choose the crash window deliberately: a crash between the two renames must leave **no** `out` (reads as "the run did not complete") rather than a mixed-epoch `out` carrying a pass claim. Absent must beat misleading.
*Acceptance criterion, and it must be tested:* for each of an interrupt mid-publish and an exception mid-publish, assert the exit code is non-zero **and** that no reachable `out/summary.json` claims `status: pass`. A test that asserts only the exit code does not satisfy this.

**Finding 2 — `--out .` is a regression. MUST FIX.** `args.out.with_name(args.out.name + '.staging')` raises `ValueError: PosixPath('.') has an empty name`. Verified: at `24abc32` `--out .` → `rc 0` with all four artifacts written; at HEAD → `rc 1`, `{"status":"fail","errors":["PosixPath('.') has an empty name"]}`, nothing written.
*Fix:* resolve the output path before deriving the staging name, so `.`/`..`/relative paths work. A resolved path whose name is still empty (filesystem root) must fail with a message naming the `--out` flag, not an internal type name.

**Finding 3 — `compatible: null` is invisible in `report.md` when the *current* panel is unversioned. SHOULD FIX.** The unverified branch tests `versions['prior'] is None`, so an unversioned current panel with a versioned prior proceeds to compare and prints no comparability line at all — a reader cannot tell `null` from `true`. Changing the branch to test `versions['compatible'] is None` is the fix and passes the suite unchanged.

**Finding 4 — an empty `--prior` file renders as "no prior window supplied". SHOULD FIX.** `if prior_rows else None` means `prior == []` yields `diff: null`, byte-identical to omitting `--prior`. The probe's own zero-row run writes an empty `evidence.jsonl`, so this is a natural artifact. Distinguish "no prior supplied" from "prior supplied but empty", and render the latter as unknown, not as absence. This is the file-level twin of Round 2 finding 1.

**Finding 5 — duplicate validation is not enforced where coverage is computed. SHOULD FIX.** `main` validates both files, but `_panel_coverage` does not: `build_summary(dup_rows, [], panel_without_declared_repetitions)` → `covered_prompts: 1`, no gaps, `status: pass`, while the same rows with a prior raise. Coverage semantics for shared repetition indices must not depend on whether an unrelated field was declared. Enforce it in the coverage path too, so a direct library call cannot grant credit to duplicates.

**Nits.** (6) validate `panel_version`'s type and compare like-for-like — `1` vs `'1'` currently warns "panel version differs (1 -> 1)". (7) a panel-version mismatch reports `status: pass`; the machine-readable status should reflect the abandoned comparison. (8) the panel is read twice (`load_panel(...read_text())` and a second `read_text()` for the copy) — a TOCTOU; copy from the parsed panel so `out/panel.json` is what was actually measured. (9) the `unmeasured` and pass branches print identical statements and differ only in the return value; collapse them.

### Task 10: oracle hardening and the 10 surviving mutations

**Files:** `tests/test_ai_answer_probe.py`

Round 3's oracle compares **filtered per-category** line lists, so it has no "no unexpected lines" assertion, never asserts a warning's *absence*, and cannot see cross-category order. That is exactly why these survive. Each must be killed, verified by applying the mutation, observing the failure, and restoring byte-identically:

| # | Mutation | Why it survives today |
|---|---|---|
| 1 | `mine` lookup drops `prompt_version` | panel declaring `p01 v1` **and** `p01 v2` with only `v1` measured → mutant reports `2/2` covered |
| 2 | `mine` lookup drops `prompt_type` | same site, type dimension |
| 3 | off-panel ids unsorted | caught under 11 hash seeds, survives under `PYTHONHASHSEED=2` — the kill is hash-luck, not an order assertion |
| 4 | `Boundary:` line deleted | the module's evidence-discipline statement never reaches `report.md` and nothing asserts it |
| 5 | arbitrary extra report line added | no "no unexpected lines" assertion |
| 6 | unconditional false overlap warning | additions of warning lines are unasserted; removals are caught |
| 7 | unconditional false comparability warning | same |
| 8 | pure cross-category reorder (trends before `Compared:`) | within-category order enforced, across categories not |
| 9 | `main`'s prior duplicate check removed | message assertion passes; `out/` is then created and left empty |
| 10 | `staging.rmdir()` removed | success-path cleanup unasserted |

Tests 1–2 and 8 are the substantive ones: they need inputs where the correct value is non-trivial (a two-version panel; a run with a diff so category order is observable). Test 3 needs an order assertion that does not depend on hash seed — assert the exact expected list, not membership.

Also add the **acceptance test** for Task 9 finding 1 (interrupt mid-publish → non-zero exit **and** no pass-claiming `summary.json`), and a test that a successful run leaves no staging directory behind.

### Round 4 close-out

After Tasks 9–10: run all four gates, then one more adversarial round. If that round again finds a fresh layer in the publish path, stop and revisit scope with the user rather than continuing to iterate — the user's instruction was to fix must and should findings, not to iterate without bound.

**The stop condition triggered.** The Round 4 review found a fresh layer in the publish path — including two data-loss defects — so scope was escalated to the user, who elected to fix must and should findings and continue reviewing.

---

## Round 5 — the cleanup path (data loss)

Round 4 fixed the atomicity of the *rename* sequence but left the *cleanup* logic unsafe. Round 4's review returned **CHANGES REQUIRED** with five must-fixes, three should-fixes and nits.

**Root cause, and the shape of the fix.** Round 4 hand-rolled the staging and outgoing paths as `.<out-name>.staging.<pid>` / `.<out-name>.outgoing.<pid>` in `out.parent`, then discarded **both unconditionally in a `finally`** — regardless of whether this run created them. Every must-fix below descends from that: the run can delete a directory it never created, and it can follow a symlink standing at one of those names.

The fix is a **simplification, not more complexity**: let `tempfile.mkdtemp` choose the staging name (which makes collisions with user paths and with other processes impossible by construction), record exactly which paths this run created, and discard only those.

### Task 11: cleanup-path correctness (F-A, F-B, F-C, F-F, F-G, F-H)

**Files:** `scripts/monitoring/ai_answer_probe.py`, `tests/test_ai_answer_probe.py`

**F-A — `_discard_tree` recursively deletes a directory the run did not create, and reports success. MUST FIX.**
Verified in-process with the pid pinned: a real directory pre-exists at `.out.outgoing.<pid>`, `out` is absent → the run **returns success** (`status: pass`) and the directory and its contents are **destroyed**. Trigger is a name collision in `out.parent`; the probe itself creates these names on a crash, so pid reuse after a crash is a live route.
*Fix:* never discard a path this run did not create.

**F-B — `_discard_tree` follows a symlink passed as its root, contradicting its own docstring. MUST FIX.**
Verified: a symlink at `.out.outgoing.<pid>` pointing at a directory → run **succeeds**, the target is **emptied**, the symlink left behind. The guard at `_discard_tree` checks *children* (`if child.is_dir() and not child.is_symlink()`), never the root — while its docstring claims "A symlink is unlinked rather than followed".
*Fix:* check the root before recursing, or remove the possibility by using `mkdtemp` so the name cannot pre-exist.

**F-C — `Path.resolve()` can raise `RuntimeError`, escaping the fail envelope. MUST FIX.**
On Python 3.12 a symlink loop makes `resolve()` raise `RuntimeError`, which is not in the `(OSError, ValueError, AttributeError)` tuple → `rc 1` with **empty stdout and a traceback**. That breaks the machine-readable-envelope contract the module states elsewhere.
*Fix:* catch it, or resolve in a way that cannot raise for this input.

**F-F — version-incompatible `skipped_incompatible` counts only the current window. SHOULD FIX.**

> **Corrected after implementation — this described the mutant, not the code.** The shipped code has counted both windows since `554bf1a` (`skipped_incompatible = len(indexed_current) + len(indexed_prior)`); 2 current + 2 prior renders **4**, verified. The finding's real content is "mutation M22 survives the suite", i.e. a **test gap only**. Task 11 added the missing test; no code change was needed or made.

**F-G — `unmeasured` no longer outranks `incomparable`. SHOULD FIX.**

> **Corrected after implementation — also a test gap only.** `unmeasured` already outranks `incomparable` in the shipped code; verified. The finding's real content is "reordering the branches survives the suite". Task 11 added the test that kills the reorder.

**F-H — a successful run can leak an entire previous epoch forever. SHOULD FIX.**
With read-only content inside the outgoing `out` (e.g. `out/sub` mode 0555) the run **succeeds** and leaves `.out.outgoing.<pid>` holding the whole previous epoch, because `_discard_tree` swallows the `OSError`. The `finally` comment claims nothing is left behind — false on this path. Either surface the failure or make the claim true.

**Nit.** A second interrupt during `finally` cleanup escapes as an unhandled `KeyboardInterrupt` (exit 130, no envelope).

### Task 12: oracle hardening for the Round 4 survivors

**Files:** `tests/test_ai_answer_probe.py`

Round 4's review found 8 survivors. Two are equivalent mutants and need no test; the rest need one each, verified by applying the mutation, observing the failure and restoring byte-identically:

| # | Mutation | Note |
|---|---|---|
| N11 | removing the child-symlink guard (`and not child.is_symlink()`) | the only thing between F-B and a realistic data loss; no test has a symlink inside the outgoing tree |
| N7 | dropping `.{os.getpid()}` from the staging name | 20/20 clean trials today because of startup jitter; with a widened publish window the mutant gives **0 successes in 4 of 5 trials** |
| M22 | `len(indexed_current) + len(indexed_prior)` → `len(indexed_current)` | reachable via two panels with different versions |
| M21 | reordering `unmeasured` / `incomparable` | F-G |
| M23 | coverage-path label `'recorded observation'` → any other string | assertions match `'duplicate'` only |
| N20 | `_discard_tree` re-raising on `OSError` | would turn a successful publish into a traceback in `finally` |
| M28 | `resolve()` → `absolute()` | differs for a dangling `--out` symlink; pin the behaviour deliberately |
| N4 | deleting the `--out is not a directory` guard | only the message text differs |

S9 (removing `main`'s prior-duplicate check) was verified as a **true equivalent mutant** over 19 differential scenarios — do not add a test for it; the implementer's pinning test is sufficient. S2 (the `prompt_type` dimension) is not CLI-reachable because `load_panel` rejects duplicate `(id, version)`; the direct-library test is the correct place for it.

### Task 13: repair the date-bombed test (outside this work)

**File:** `tests/test_community_discovery.py`

Gate 1 fails as of 2026-09-21T10:00Z, independent of this work: the fixture pins `"fetched_at": "2026-09-14T10:00:00+00:00"` while `scripts/evidence_scout/review_community_candidates.py:29` rejects `activity_status`/`public_access` observations older than `DIMENSION_MAX_AGE = 7 days`. It fails in a pristine archive of both `12d83ad` and `HEAD`.

*Fix:* make the fixture's timestamp relative to the current time (or re-pin to a date that cannot expire) so the test stops being time-bombed. Verify it passes now and that the assertion's intent is unchanged — do not weaken what it asserts.

**Caution:** a concurrent external workstream is editing `scripts/evidence_scout/` and evidence-scout skill files. This task touches only the test file; if the working tree shows the workstream has already changed that test, stop and report rather than conflicting with it.