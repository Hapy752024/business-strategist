---
name: market-problem-discovery
description: Discover sourced customer problems, workarounds, segments, and candidate underserved pockets. Use for broad market exploration before a specific customer and problem hypothesis exists.
---

# Market Problem Discovery

**Market-discovery sequence.**
1. Use `market-problem-discovery` to collect public evidence and write a detailed discovery report.
2. Ask the user to choose one candidate, change the scope, extend the research, or stop.
3. Once the user selects a candidate, use `idea-grill` to fill remaining hypothesis gaps, then continue with its core validation sequence.

**Customer search-journey SERP study.**
After a segment is named and before competitor discovery, optionally run the evidence-scout search-journey study
(`scripts/evidence_scout/search_journey.py`; method rules in `.agents/skills/evidence-scout/SKILL.md`).
Brainstormed queries are hypotheses; ads are supplier spend, not demand; `unobserved` ads are never zero.
Forum or aggregator dominance is a hypothesis for the next test, not a discovery finding.
It runs before the pain gate and does not authorize ads or content publication.

When a selected candidate becomes a registered Business case, pass material findings and answered founder questions to the case-insights owner under repo-root `references/case-insights.md`. Keep discovery artifacts in their normal research location.

The user’s requested outcome governs the study. For a topic or segment pain-point question, explain customer experiences and uncertainty without inventing a product or business. For a supplied idea, route to idea validation and challenge that idea; relevant similar companies are optional evidence, not a prompt to import one. Use the complementary methods in `references/opportunity-research-approaches.md` only when they contribute distinct evidence.

## Success Criteria
- **Research quality:** source-linked customer experiences and outcome/context distinctions survive synthesis; positive/contrary cases and missing markets remain visible. Candidate counts, headings and tool-call quotas do not establish research quality.
- **Qualitative:** every candidate includes segment, trigger, workaround, source-backed observation, counter-evidence, and named uncertainty; evidence and interpretation are not blended; user controls the next path.

## Workflow

For substantive query design and refinement, apply repo-root `references/research-query-calibration.md` (shared repository dependency) before broad collection. Keep each workflow's evidence type and source-review requirements distinct.

1. Read `references/workflow.md`, repo-root `references/customer-voice.md`, `references/voc-research-method.md` and `references/research-execution.md` completely. Always run topic-led discovery; add entity feedback when alternatives are verified, without requiring a preselected segment.
2. Infer discovery mode when explicit; otherwise ask the one routing question before collecting.
3. Create a durable discovery run, validate source routes, and collect public evidence before proposing candidates.
4. Write source-linked outcome shortfalls, competing explanations and next tests in the existing report; distinguish candidate underserved needs, adequate service and insufficient evidence.
5. For a selected candidate with explicit venture-scale or VC-financing relevance, optionally assess topic funding activity under repo-root `references/vc-investment-signals.md`; do not treat it as customer evidence or use it to rank customer pain.
6. Stop for the user's choice (sequence step 2); do not automatically convert a discovery candidate into a startup thesis.

## Output

Return the report path, source coverage, 3–7 candidate problem-segment pockets or a clear no-opportunity finding, the strongest counter-evidence, and one user decision question.
For substantive Business research, read repo-root `references/research-data-and-precedents.md`. Select official statistics and studies by the decision, combine them with separately reviewed customer voice, and retain international applicability and relevant investor signals. Metadata is discovery until original findings are reviewed.

For customer-journey analysis, read repo-root `references/journey-activation-and-measurement.md`, section 1 (shared repository dependency). Record sourced touchpoints and candidate ad/tool/partner hooks with access, next action and measurement; keep intervention hypotheses separate from observed pain. Research does not select a campaign or bypass the pain-first gate.

Also read when the stage needs it:
- `.agents/skills/evidence-scout/references/workflow.md`
- `references/institutional-and-university-sources.md`
- `references/modules/source-worker-packet.md`
- `references/task-scope.md`
