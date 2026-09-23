> Historical handoff, not the current implementation contract. See [closure results](search-visibility-closure-2026-09-23.md) and [format-2 recording instructions](../references/ai-answer-recordings.md). Existing output replacement is now rejected; do not replay old cleanup plans.

# Handoff brief — Search-visibility work (2026-09-21)

**Purpose of this document.** It is written to be pasted as a prompt into another capable model or agent so it can pick up this work with full context. It states what the plan was and why, what was done and why, what is open, and where to look. It is deliberately blunt about mistakes, including mine, because the failure modes here are the useful part.

**Repo:** `business-strategist` (a portable business-idea validation skill set for Claude Code — skills, routing config, evals, and Python tooling). Branch: `main`. Nothing in this work is pushed; `main` is **29 commits ahead of `origin/main`**.

---

## 1. The original request, and why

The user asked (paraphrasing their words):

> "I want to write / optimize existing skills for digital marketing... Build a plan on how to optimize a website / brand for digital marketing (SEO, GEO, ...) and how to adjust our current agent setup to perform that."

Plus a second requirement: where a layer needs the *owner* to do something (e.g. "write a post every week"), the skills should surface those as explicit recommendations rather than leaving them implicit.

So the goal had three parts: (a) decide what actually moves the needle in modern search, (b) wire that into the existing agent skills at their real entry points, and (c) give the owner a structured way to see what only they can do.

### Documents that define the goal

| Document | What it is |
| --- | --- |
| `docs/digital-marketing-optimization-plan.md` | **The spec.** A six-layer search stack — SEO (be found), SMO (discovered/discussed), AEO (be the answer), GEO (understood/cited by generative systems), DEO (evaluated/chosen by agents), SXO (converted) — over a shared foundation of entities + content + data + authority + trust. Contains binding evidence limits (§1) and measurement contracts (§3.1). |
| `docs/digital-marketing-optimization-plan-adversarial-review.md` | Adversarial review of that spec, which forced several claims to be weakened to what the evidence supports. |
| `docs/superpowers/plans/2026-09-20-search-visibility-setup.md` | **The implementation plan** (6 tasks). Also carries the execution progress log and an errata section. |
| `docs/search-visibility-implementation-review-2026-09-20.md` | An independent external review of the implementation, which found five material defects. |
| `docs/superpowers/plans/2026-09-20-search-visibility-review-fixes.md` | **The fix plan**, now covering Rounds 1–5 of defect fixes. This is the most current document. |

### Binding constraints that shaped everything

These come from the spec and are not negotiable in the code or the prose:

- Model/AI-engine output is **observation data, never customer-demand evidence**.
- A failed or credit-blocked probe is a **coverage gap (`unknown`), never absence of mention**.
- Never quote the "4–9x AI conversion" figure; the schema/citation result is scoped to its matched sample; `llms.txt` has no measured impact; `Google-Extended` is a product token with no observable HTTP user agent; Reddit's Responsible Builder Policy establishes **no "90/10 rule"**.
- The AI-answer probe is **offline / recorded-mode only**. No live API calls, no credentials, no network. It is a normalizer and comparator.

---

## 2. What was done, and why

Executed with the `superpowers:subagent-driven-development` discipline: a fresh implementer per task, a fresh independent reviewer per task, fix rounds, then whole-branch adversarial review. Two plans ran in sequence.

### Plan A — `2026-09-20-search-visibility-setup.md` (6 tasks)

| Task | Deliverable | Why |
| --- | --- | --- |
| 1 | New `aeo-geo-visibility.md` + `deo-agent-readiness.md` references; edits to `maintenance.md`, `seo-performance.md` | Existing-site work had no AEO/GEO entry point at all |
| 2 | `references/owner-actions.md` (repo root) + bottleneck-gated handoffs in marketing/social workflows | The owner-action requirement; also prevents appending recurring programs to narrow work |
| 3 | Two capability entries in `config/source-capabilities.json` | Registers the observation providers so `capability_lookup.py` can surface them |
| 4 | Route tokens in `config/workflow-routes.json` + evals + a parametrized routing test | Make the new work reachable by the router |
| 5 | `scripts/monitoring/ai_answer_probe.py` + tests | The measurement gap: nothing in the repo measured AI visibility |
| 6 | Gate run | Verification only |

### Plan B — `2026-09-20-search-visibility-review-fixes.md` (Rounds 1–5)

The external review found five defects; fixing them surfaced more, and each round's fixes introduced or exposed further ones. Rounds in order:

- **Round 1** — F1 repeated observations collapsed (file order could flip a reported gain into a loss); F2 the selected panel was validated then ignored (an empty recording reported *zero coverage gaps*); F3 successful observations accepted without locale/timestamp/source answer, and `prompt_type` missing from the comparison key; F4 accepted owner actions persisted as `open_blockers`; F5 DEO markup scopes conflated (organization-level vs offer-level).
- **Round 2** — the fixes introduced new defects: `report.md` couldn't distinguish "nothing comparable" from "no movement"; an undeclared engine suppressed the fail-closed exit; duplicate repetitions satisfied coverage but were rejected by comparison; `skipped_incompatible` undercounted one side; window overlap compared timestamps lexicographically. **18 mutations survived the test suite.**
- **Round 3** — the publish was **not atomic** (re-creating the defect it was written to kill); `--out .` was a **regression**; 10 more survivors. Added an artifact-consistency test layer.
- **Round 4** — **two data-loss defects**: the cleanup deleted a directory the run never created, and followed a symlink at such a name — **both while reporting `status: pass`**.
- **Round 5** — cleanup path rebuilt on `tempfile.mkdtemp` (so collisions are impossible by construction rather than defended against); the remaining mutation survivors pinned.

Also repaired, outside this work: `tests/test_community_discovery.py` had **two date-expired fixtures** that began failing at 2026-09-21T10:00Z regardless of any of this work.

---

## 3. Current state

**Gates (all four run, all green as of the last run):**

- `bash scripts/validate_setup.sh` → `1 warning(s), 0 errors` (the warning is the pre-existing missing-evals notice for `town-db-curator`)
- `python3 scripts/run_evals.py` → all structural checks pass, 167 eval cases, 0 errors
- `python3 scripts/validate_skill_routes.py` → `{"passed": true, "errors": []}`
- `python3 -m pytest tests/ -q` → **645 passed**

**Test counts:** `tests/test_ai_answer_probe.py` grew 8 → 77.

**Open:** a Round 5 adversarial review was dispatched and **has not reported yet**. Its result is unknown; do not assume it passed. It was briefed to attack the rewritten cleanup path, specifically whether `_make_removable`'s chmod can be aimed outside the run's own trees, `out.name` edge cases (`.`, `..`, trailing slash), permission leakage from `mkdtemp`'s 0700, and a black-box concurrency re-run.

---

## 4. Open issues and risks

**1. The probe has no consumer.** Nothing in the tree reads its `report.md` or `summary.json` — no Python caller of `build_summary`/`diff_observations` outside its own test, no reference under `projects/`. Today's blast radius is zero, which is why the data-loss defects were survivable but also why five rounds of investment are worth questioning.

**2. The recurring defect class, and why it kept recurring.** The probe renders one internal state **four ways** — `report.md`, `summary.json`, stdout, and the exit code — and every test originally asserted the *internal dict*. So each review round found a *rendering* that lied while the dict was correct. Round 3 added an artifact-consistency oracle that reconstructs the whole report independently and asserts the four agree; that is the durable fix, and it is the single most valuable thing in this changeset.

**3. My plan documents were themselves a defect source.** Six separate plan claims were wrong and were caught by implementers who pushed back rather than complying:

| Claim I wrote | Reality |
| --- | --- |
| `PANEL_REQUIRED` tuple is produced | No step defines it — dead interface |
| Round 1 finding 4 affects one test | It affected three |
| Order-invariance test kills the `sorted()` mutation | It cannot — the union order comes from the current set |
| Task 5 literal block has 4 named defects | 2 are not in the block; they live in the correction |
| F-F: `skipped_incompatible` renders `: 2` | It renders `4`; that described the *mutant*, not the code |
| F-G: `unmeasured` no longer outranks `incomparable` | It already does; test gap only |

The pattern: transcribing a review finding one level too confidently, as a statement about shipped behaviour rather than a mutation to verify. **If you continue this work, write plan findings as mutations to verify, not as claims about code.**

**4. Unexplained concurrent modification of the repo — twice.**
- `feat/search-visibility-setup` was fast-forwarded into `main` and deleted by something not run in this session. The reflog records the checkout and merge but not the actor. Both subagents active at the time independently confirmed the branch was already gone when they started.
- A **separate workstream is editing this repo concurrently**, uncommitted: `scripts/evidence_scout/collect.py` (~233 lines), `.agents/skills/evidence-scout/SKILL.md`, `.agents/skills/evidence-scout/references/workflow.md`, `.agents/skills/idea-grill/references/workflow.md`, `references/commands.md`, and an untracked `.agents/skills/evidence-scout/references/pain-query-calibration.md`.

Everything in this changeset was therefore committed with **explicit pathspecs**, never `git add -A` or `git commit -a`. **If you continue, keep doing that.** It is also worth finding out what is driving these modifications.

**5. Known, accepted limitations** (recorded in the fix plan with their cost): `competitor-monitoring/SKILL.md`'s description is still competitor-only; the router's matcher at `scripts/route_workflow.py:230` has no word-boundary logic, so bounded tokens are used instead (changing the matcher would re-scope ~40 routes); concurrent writers sharing one `--out` are not *serialized* (exactly one wins, losers fail honestly); `config/source-capabilities.json`'s `requires_env` reads as four mandatory keys when they are per-engine alternatives.

**6. `main` is 29 commits ahead and unpushed.** The user's standing instruction was to keep it local until the probe work settles. Nothing is public and everything is reversible.

---

## 5. If you pick this up

1. **Read the fix plan first** — `docs/superpowers/plans/2026-09-20-search-visibility-review-fixes.md`. It is the current record: every finding, its reproduction, its fix, and the corrections where an earlier claim was wrong.
2. **Check whether the Round 5 review has reported.** If it found another layer in the cleanup path, the user's stated position was to be consulted rather than iterating without bound.
3. **Verify before trusting.** The most expensive lesson here: two rounds of review returned a confident SHIP that was wrong, because the reviewers verified the code matched a plan instead of testing the plan's claims. Reproduce; do not confirm.
4. **Prefer testing rendered artifacts over internal state** for anything with more than one output surface.
5. **Before any destructive filesystem operation**, prove the code only touches paths it created. That is where this went wrong, twice.

### Quick verification commands

```bash
bash scripts/validate_setup.sh
python3 scripts/run_evals.py
python3 scripts/validate_skill_routes.py
python3 -m pytest tests/ -q
python3 -m pytest tests/test_ai_answer_probe.py -q     # 77 tests
git log --oneline origin/main..main                     # 29 commits, unpushed
```

---

## 6. Commit map (29 commits, oldest → newest)

```
bcf70c8  Task 1: AEO/GEO + agent-readiness references at website entry points
abf742d  Task 2: owner-action contract + bottleneck-gated handoffs
0717237  Task 3: register AI answer-engine and mention-listening providers
fb8e073  Task 4: route AEO/GEO and own-brand observation requests
388b9a1  Task 4 fix: bound the AEO token (unbounded substring hijacked "Kaeon"/"Aeon")
60b6db6  Task 5: read-only AI-answer observation pilot
f7c9dfc  Final fix: bound route tokens; give competitor-monitoring own-brand instructions
a75a0cf  Final fix: reference pointers, action encoding, AEO gate reach
c0be157  docs: spec, adversarial review, implementation plan
b152c5a  docs: log the final whole-branch review outcome
3970356  fix: three review residuals (SKILL.md description, boundary assertion, -O safety)
46a6f6e  fix: F4 + F5 (open_blockers reservation; DEO markup scopes)
5e89afb  Round 1: panel-driven coverage + contextual validation
9052d75  Round 1: order-independent, repetition-aware comparison
5cc807b  docs: external review + fix plan
80b2031  docs: close Task 3 review nits
24abc32  Round 2: report gaps/skipped counts; fail closed on undeclared engines
024b176  Round 2: bound replay-hazard route literals
5b98cfd  Round 2: name the remaining Task 5 replay hazards
554bf1a  Round 3: make rendered artifacts agree with state
14453a4  Round 3: assert rendered artifacts, not the internal dict
b0efd6f  Round 3: drop dead status literal
43afeca  docs: correct the Task 8 framing (two claims refuted)
f80f8cc  Round 4: publish by directory rename; repair --out .
7e7a5a1  Round 4: assert the whole report, not per-category subsets
1f618e1  fix: stop community-discovery fixtures expiring
c09f367  Round 5: never discard a cleanup path the probe did not create
2adbea5  Round 5: pin the five mutations that outlived the cleanup rewrite
9a5d075  docs: record Round 5 and correct two findings that described mutants
```
