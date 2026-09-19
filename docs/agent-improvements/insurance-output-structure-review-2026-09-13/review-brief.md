# Insurance output structure review

Date: 2026-09-13. Scope: inspect the existing insurance workspace and comparable public agent workflows; use three proposal agents and one independent judge to converge on two restructuring options, at most five review rounds. This is an architecture/design deliverable, not authorization to migrate research or select a business.

## Evidence and boundaries

- Current workspace: `projects/german-insurance-opportunity/` (explicitly selected by the user).
- 376 files, including 130 Markdown files; 322 files under `market_research/`, 51 under `strategy/`. Full inventory and SHA-256 baseline: `workspace-inventory.json`.
- Existing project files, manifests, archived evidence, reusable skills and code remain unchanged by this review. The working tree already contains unrelated changes.
- Existing research claims are inspected for organization and provenance, not revalidated as market findings.
- Source search uses primary project documentation/code. Transferable design patterns are distinguished from demonstrated suitability for business research.
- Firecrawl authenticated but sandbox account lookup failed; an escalated search returned HTTP 402. User was asked whether to continue with the available web tool or wait for a top-up. No credit retry or top-up is authorized by this review.

## Observed defects

1. Stage folders dominate the hierarchy. Idea identity appears inconsistently in intake filenames, pain folders, competitor runs, strategy annexes and dated deep dives.
2. English and Chinese are separately investigated variants but lack obvious entry points. Arabic-speaking doctors cross language and profession. Discount motor is a distinct model. Register mail is explicitly described in the README as a channel. A single exclusive taxonomy would misrepresent these relationships.
3. The root README combines recent summaries with an explicitly superseded scorecard and execution plan. `strategy/current-recommendation.md` retains a current-looking title. There are several historical next actions in stage records. A new folder alone cannot resolve document authority.
4. The research manifest reports `current_stage: synthesis`, root `gate_result: not_run`, and `problem_validation.status: passed` with `gate_result: conditional_pass` from a migration backfill whose gap says pain synthesis is pending. Segment selection is in progress and customer profile is pending. These are observed stored values, not a fresh validation judgment.
5. Controller blockers are empty; research-manifest blockers are not. The controller is a track/link authority, not an independent source of research readiness; its summary should not mislead readers.
6. Three prior workspaces were consolidated on 2026-09-11. Research is gitignored, so any later migration needs a filesystem backup and explicit path map, not reliance on Git rollback.
7. `scripts/route_workflow.py:pain_gate_state` accepts a project slug and reads `projects/<slug>/market_research/manifest.json`. Nested idea scopes and inherited evidence admission are not implemented. `scripts/project_workspace.py` also assumes project roots and linked track authority.

## Review protocol

Round 1: three independent local inspections and proposals. Root supplies a common external-source packet. Judge evaluates all three and requests explicit changes. Round 2: proposal agents see all proposals and judge feedback, identify borrowed/rejected elements, and revise. Judge reevaluates. Repeat only for substantive blockers, maximum five rounds.

The initial agents independently converged on an additive idea library. Root explicitly asked proposal B to develop the strongest physical idea-first alternative to avoid presenting two cosmetically different finalists. This steering is part of the review record.

## Judge rubric

Scores are reasoned design judgments, not measured usability results. Rate each criterion 1–5 and calculate a weighted total out of 100:

| Criterion | Weight |
|---|---:|
| Founder can find and compare the investigated alternatives | 25 |
| Overlapping ideas, variants, channels and capabilities represented honestly | 15 |
| Evidence reuse, traceability and correction propagation | 15 |
| Clear current conclusions, historical decisions and scoped readiness | 20 |
| Compatibility, migration safety and reversibility | 15 |
| Ongoing maintenance and complexity | 10 |

Required scenarios: Chinese, English and motor visible within two navigation steps; Arabic doctors without duplicated evidence; one shared source correction reaches affected ideas; a parked idea remains discoverable; an emerging cyber idea cannot inherit personal-insurance validation; old English-first guidance cannot appear as the current winner; resume research on Chinese without touching motor state; distinguish a genuinely separate project from a language variant.

Stop with two materially different options scoring at least 80/100, no unresolved design blocker, explicit implementation prerequisites and honest disadvantages. This is a design-review threshold, not production approval or proof of human usability. If fewer than two qualify after five rounds, report that rather than declaring forced convergence.

## Files to load

Current README/manifests; lifecycle/task-scope references; three idea intake files; language/profession/Arabic/motor annexes; latest deep dives; consolidation map; relevant router, workspace and schema code. Raw provider payloads stay on disk unless a specific provenance question requires them. Do not read the whole evidence corpus into agent context.

## Deliverables

One final design report with two concrete trees, actual-file mapping, source comparison, costs/risks and migration prerequisites; all three initial proposals and revised proposals; judge feedback per round; explicit cross-pollination and a record of which checks were actually performed.
