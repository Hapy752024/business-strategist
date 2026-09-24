# Search-visibility implementation review

Reviewed: **2026-09-20**. Verdict: **changes required before relying on the observation pilot's results.** The instruction changes are substantially better than the original proposal, but the probe can generate misleading comparisons and incomplete coverage reports on ordinary inputs.

Scope: the implementation described in [the setup plan](superpowers/plans/2026-09-20-search-visibility-setup.md), its revised [specification](digital-marketing-optimization-plan.md), and the relevant changes from `12d83ad` to `b152c5ade50bebe82ed87fa2941c34ff8b41f3cd`, plus the working-tree changes visible during review. `projects/` was excluded. This review addresses material output quality; it does not propose architecture changes, broad testing expansion or fixes for contrived inputs.

Concurrent edits to the probe, its test, and the competitor-monitoring skill appeared during review. They were preserved. The probe's `assert` was replaced with explicit validation; that does not resolve the findings below. No implementation files were modified by this review.

**F1 — High: repeated observations are collapsed, producing order-dependent false movement.**

Location: [ai_answer_probe.py](../scripts/monitoring/ai_answer_probe.py), lines 12 and 46–61.

`prior_ok` stores one row per comparison key. The key excludes `repetition`, so each later repetition overwrites the preceding one. Every current repetition is then compared with that single remaining prior observation.

Reproduced with two observations of the same prompt in each window:

| Input | Actual result |
| --- | --- |
| Prior mentions `[false, true]`; current mentions `[false, true]` | One reported loss: `true → false` |
| Same current rows; reverse only the prior file order | One reported gain: `false → true` |

Both windows have exactly the same two observations and the same 50% mention rate. The reported direction is an artifact of file order. Repetitions are an explicit part of the measurement contract, so this affects the intended use rather than an edge case.

Material impact: the agent can recommend a response to a visibility gain or loss that did not occur.

Correction: retain every repetition. For independent stochastic samples, compare per-prompt/window counts and rates with successful/failed sample sizes; do not let the last row become the baseline. If individual repetitions are intentionally paired, match them explicitly and still distinguish individual response changes from a window-level trend. Reordering a file must not change the result.

**F2 — High: the supplied panel is ignored, so missing observations disappear from coverage.**

Location: [ai_answer_probe.py](../scripts/monitoring/ai_answer_probe.py), lines 67–71 and 83–94.

The CLI checks only that `panel.prompts` is a nonempty list. It never uses the selected prompts to validate observations or calculate coverage. `coverage_gaps` is built exclusively from error/unsupported rows that happen to be present.

Reproduced against a panel containing `p01` and `p02`:

| Recording | Actual result |
| --- | --- |
| One successful row for `not_in_panel` | Exit 0, `status: pass`, `observations: 1`, `coverage_gaps: []` |
| Empty recording | Exit 0, `status: pass`, `observations: 0`, `coverage_gaps: []` |

The observation count is visible, but the named coverage result never identifies either missing panel prompt. A missing engine export or omitted row likewise cannot be distinguished from an intentionally unrequested observation. This is separate from the correctly handled case where a failed probe explicitly supplies an error row.

Material impact: an incomplete recording can look like a cleanly covered panel, and unrelated prompts can enter the selected run. The panel's provenance and versioning do not constrain the actual measurement.

Correction: validate prompt IDs, versions and types against the panel. Define the expected engine/repetition set in the panel or run configuration, calculate observed coverage against it, and report missing observations as unknown. Reject unrelated rows or explicitly separate them. An empty collection must be reported as unmeasured, not as zero coverage gaps. Preserve the selected panel alongside the output so a later reader can identify what was measured.

**F3 — Medium: successful observations can lack the context needed to verify or compare them.**

Location: [ai_answer_probe.py](../scripts/monitoring/ai_answer_probe.py), lines 9–12 and 16–39.

`locale`, `timestamp` and `answer_text` are declared output fields, but none is validated. Removing all three from an otherwise valid successful observation is accepted and produces `null` for each. Two observations with unknown locale can then compare as if their locales were compatible. The script also excludes `prompt_type` from its comparison key: a brand-seeded row compares with an unbranded-discovery row carrying the same ID/version. This was reproduced as an ordinary reported change rather than an incompatibility.

The implementation plan describes compatible-window comparisons, but neither normalization nor comparison establishes a collection window or checks timestamp usability. Merely carrying a nullable timestamp does not provide that guarantee.

Material impact: the agent can accept a positive mention/recommendation claim without retaining the answer that supports it, or interpret a difference across incompatible collection contexts as movement.

Correction: require usable locale/time context and the source answer for a successful observation. Validate prompt identity/type against the panel and make comparison windows explicit. Incomplete records may be retained as diagnostic inputs, but must not enter successful comparable coverage. This requires enforcing the existing measurement contract, not a larger validation framework.

**F4 — Medium: ordinary accepted tasks are persisted as blockers.**

Location: [owner-actions.md](../references/owner-actions.md), line 7.

The new encoding puts the highest-priority accepted action in `next_action` and every additional accepted action into `open_blockers`, prefixed `owner action:`. Acceptance alone does not make a task a dependency or a blocker. For example, an owner can approve both a monthly founder post and a later interview without either blocking the current website task; this rule reports one as an open blocker anyway.

The [workspace lifecycle](../references/workspace-lifecycle.md) explicitly surfaces open blockers on resume. The prefix does not change how that field is described to subsequent agents. No automatic deployment rejection from this field was demonstrated; the confirmed problem is misleading task/resume state.

Material impact: resumptions can frame optional, accepted follow-up work as work that prevents progress, undoing part of the earlier effort to avoid unnecessary owner obligations.

Correction: reserve `open_blockers` for actual dependencies. A string-valued `next_action` can contain a concise ordered set of accepted next steps; it does not require converting the rest into blockers. Preserve unrelated existing blockers and the proposed/accepted distinction. No new schema or task system is needed.

**F5 — Medium: the DEO procedure prescribes shipping markup at the wrong level.**

Location: [deo-agent-readiness.md](../.agents/skills/brand-website-designer-builder/references/deo-agent-readiness.md), line 5.

The procedure calls for Organization-level `MerchantReturnPolicy` and `OfferShippingDetails` together. Google's documented shipping structures distinguish `Offer.shippingDetails → OfferShippingDetails` from organization-level `Organization.hasShippingService → ShippingService`. The instruction conflates these scopes. [Merchant listing documentation](https://developers.google.com/search/docs/appearance/structured-data/merchant-listing), [organization shipping-policy documentation](https://developers.google.com/search/docs/appearance/structured-data/shipping-policy), both checked 2026-09-20.

Material impact: the agent can produce unsupported shipping markup despite having accurate owner-confirmed shipping facts. Fact checking alone will not catch the wrong schema relationship.

Correction: specify the appropriate property/type relationship for the selected page and consumer. Keep organization return-policy guidance separate from offer-level shipping details. Replace the ambiguous prescription with a direct current documentation link and the correct relationship; a new generic schema validator is unnecessary for this fix.

**What the implementation successfully improves**

- Existing-site maintenance now loads AEO/GEO guidance, closing the earlier entry-point gap.
- Marketing/social workflows require a relevant bottleneck, a business outcome and a stopping condition before recommending the new work.
- The revised specification gives the major numerical claims population and causality limits.
- The crawler guidance correctly distinguishes Google-Extended's training/grounding control from an HTTP crawler identity.
- Explicit error/unsupported rows require null result flags; model responses are labeled observations rather than demand evidence.
- Own-brand monitoring now has destination instructions, and customer-voice work is directed back to Evidence Scout.
- No general FAQ/schema-presence launch blocker, new visibility skill or speculative commerce server was introduced.

**Validation and interpretation of the previous SHIP result**

The targeted suite passed: `python3 -m pytest tests/test_ai_answer_probe.py tests/test_website_launch.py tests/test_skill_route_coverage.py -q` — **80 passed**. Route/catalog validation passed. `scripts/run_evals.py` reported **167 structural cases, zero structural errors** and the existing missing-evals warning for `town-db-curator`.

The reproductions above exercise the implementation independently of those assertions. The passing checks remain valid evidence for what they cover; they do not resolve F1–F3. This review does not count missing tests as a finding. It identifies wrong outputs from the shipped code.

The setup plan explicitly defers live API collection, the one-project pilot, mention collection and account-specific analytics work. Those deferrals are not implementation defects and were not exercised here. The script is currently a recorded-observation normalizer/comparator. No paid model calls, project inspection, production changes or account connections were performed.

The earlier blanket SHIP conclusion should therefore be narrowed: the instruction setup is substantially improved; the recorded-observation pilot is not yet reliable enough for trend or coverage decisions. Fix F1–F3 before trusting it, and apply the two small instruction corrections in F4–F5.

**Reproduction appendix — run from the repository root**

This uses synthetic observations and writes only to a fresh temporary directory. It does not alter tests, source files or project data. The prints show actual behavior rather than assuming the corrections have been implemented.

```bash
python3 - <<'PY'
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from scripts.monitoring.ai_answer_probe import normalize_observation, diff_observations

base = {
    'engine': 'openai', 'model': 'gpt-x', 'search_config': 'web_search:on',
    'locale': 'en-US', 'timestamp': '2026-09-20T10:00:00Z', 'surface': 'api',
    'prompt_type': 'unbranded_discovery', 'prompt_id': 'p01',
    'prompt_version': 1, 'repetition': 1, 'status': 'success',
    'brand_mentioned': True, 'url_cited': False, 'recommended': False,
    'answer_text': 'Synthetic answer',
}
def obs(**changes):
    return normalize_observation({**base, **changes})

prior = [obs(repetition=1, brand_mentioned=False),
         obs(repetition=2, brand_mentioned=True)]
current = [dict(row, timestamp='2026-09-21T10:00:00Z') for row in prior]
print('Same repetitions:', diff_observations(current, prior))
print('Reordered prior:', diff_observations(current, list(reversed(prior))))
print('Changed prompt type:', diff_observations(
    [obs(prompt_type='brand_seeded')], [obs(brand_mentioned=False)]))
print('Missing source context:', normalize_observation({
    k: v for k, v in base.items() if k not in ('locale', 'timestamp', 'answer_text')
}))

root = Path(tempfile.mkdtemp(prefix='visibility-review-'))
panel = {'prompts': [
    {'id': 'p01', 'version': 1, 'type': 'unbranded_discovery', 'text': 'Which provider?'},
    {'id': 'p02', 'version': 1, 'type': 'educational', 'text': 'How does this work?'},
]}
(root / 'panel.json').write_text(json.dumps(panel))
for label, rows in [('off_panel', [obs(prompt_id='not_in_panel')]), ('empty', [])]:
    recorded = root / (label + '.jsonl')
    recorded.write_text(''.join(json.dumps(row) + '\n' for row in rows))
    run = subprocess.run([
        sys.executable, 'scripts/monitoring/ai_answer_probe.py',
        '--panel', str(root / 'panel.json'), '--recorded', str(recorded),
        '--out', str(root / label),
    ], capture_output=True, text=True)
    print(label, 'exit:', run.returncode, 'output:', run.stdout.strip())
print('Temporary evidence:', root)
PY
```

Probe SHA-256 at the final review check: `3aab695d542d33fca22a0d0fe2a6bf3eb07199b462e2288e6482145210695767` (includes the concurrent explicit-validation edit). The owner-action and DEO files were unchanged during the review. Line references are to this reviewed state.

**Sources and evidence dates**

- Repository inspection and synthetic reproductions: **2026-09-20**, scoped to the commit and working-tree state above.
- [Implementation plan and execution log](superpowers/plans/2026-09-20-search-visibility-setup.md): reviewed **2026-09-20**.
- [Revised specification](digital-marketing-optimization-plan.md) and [prior adversarial review](digital-marketing-optimization-plan-adversarial-review.md): inspected **2026-09-20** for requirements and prior resolutions. The earlier review's research is historical context; this review did not re-verify every earlier market/platform claim.
- [Google merchant listing structured data](https://developers.google.com/search/docs/appearance/structured-data/merchant-listing): living official documentation, retrieved **2026-09-20**.
- [Google merchant shipping-policy structured data](https://developers.google.com/search/docs/appearance/structured-data/shipping-policy): living official documentation, retrieved **2026-09-20**.
