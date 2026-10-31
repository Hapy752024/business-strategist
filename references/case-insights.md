# Consolidated case insights

For a registered Business case, `cases/<id>/case_insights.md` is the one current reader-facing assessment. The project README navigates cases; feasibility, economics and research files remain source material. Do not create a case-level README for new cases; older README cases convert only through the case publisher, which refuses while a stage, question or plan still consumes the old README (refresh that consumer from reviewed original sources first).

Use `templates/project/case_insights.md` as the section pattern. Update the synthesis after each coherent batch of reviewed research, deep dives, answered founder questions, corrected evidence or changed assumptions; do not wait for the whole workflow. Integrate each answer where it changes the analysis; a link to a report does not substitute for the answer or its implication. State unknown market size, demand, prevalence or willingness to pay plainly. Keep process logs, run IDs, hashes, skill coverage and provider mechanics out of the client text.

## Before drafting

1. Resume the case and inspect `case_insights.md`, the manifest and inputs. The current document is orientation, not evidence for itself.
2. Capture a material user research question with `case_workspace.py record-question`. Founder preferences remain `known_answers`, not customer evidence.
3. Run `python3 scripts/validate_case_insights.py --workspace <business-root> --case <id> --inventory --json` and give every candidate input a disposition with a reason (incorporated, superseded, duplicate, no material finding, out of scope; pending only in a progress publication with a plain-language `pending_summary`). Newer files are not automatically more correct. Missing inputs need an explicit coverage limitation, never an invented finding.
4. Check cited findings against original passages and claim reviews. Keep customer experience separate from supplier statements; repeated copies of one incident count once.

## Draft and review

Write one concise assessment with the template's sections: customer and problem, market and demand, alternatives, feasibility, risks, recommendation, unanswered questions and sources. Use numeric claim markers for source-attributed figures and economics markers for model results; unmarked prose is not verified.

Renewed publications use contract version 2: put `{{evidence_claim.<id>}}` next to each material reviewed statement; the renderer inserts original URLs from accepted evidence or bound manual captures. Mark inspected secondary accounts with a visible limitation. A source-list link alone does not establish claim support. Label founder inputs, assumptions and model outputs for what they are.

Prepare the rendered document with `validate_case_insights.py --packet <draft.json> --prepare --out <fresh-dir>` and review that text against the inventory and underlying passages. Compare conclusions across runs for the same segment, period and definition; record each material conflict and its resolution, and disclose any unresolved disagreement in the text and the recommendation. Record reviewer type and mode honestly; an inline review is not independent. Publication requires review outcome `pass`, every check passed and no blocking findings (the validator enforces this; it does not infer approval from prose). Disclosed real-world uncertainty is not an unresolved review defect.

An interim (`progress`) publication states that research continues and names the decision-relevant open question; newly captured material cannot support a claim until reviewed. `complete` under v2 needs a separate reviewer record bound as `independent_review`; inline review is valid only for progress snapshots. Local identities are inspectable records, not proof against dishonest authorship.

If a current comparison exists, a presentation-only refresh retains it verbatim; change assessed conclusions through `case-appraisal` first. Packet shape: `validate_case_insights.py --help` and the existing case's last packet; never copy example values into a case.

Publish with `python3 scripts/case_workspace.py insights --workspace <business-root> --case <id> --input <reviewed-packet.json> --decision-id <id> --reason <reason>`. A presentation rewrite does not revalidate a research stage. While consolidation is pending, do not describe the old brief as current. Before closing a substantive case task, check with `validate_case_insights.py --workspace <business-root> --case <id> --json` and link the document to the user. For focused answers outside a registered case, apply the task-scope rules; do not create a case just to answer the question. Source links are relative to `case_insights.md` and must stay inside the Business workspace.

## Enriched research and downstream case plans

Apply [research-data-and-precedents.md](research-data-and-precedents.md) for statistics/studies, international commercial precedents and investor signals. After consolidating material findings, refresh the case business plan using [case-assessment.md](case-assessment.md); a provisional or stale plan does not establish full case delivery.

Vocabulary: prefer "Not checked" and "I don't know for sure" to hedged affirmatives ("likely", "should", "clearly", "obviously"); semantic review flags them unless a cited source supports that strength. See `research-coaching.md` for the challenging stance.

## Contract version 3: assumption register

A case with `assumptions.json` (every case registered since 2026-10-21) is held to version 3 whatever the packet declares; version 3 includes every version 2 rule and adds:

- Two required sections before `## Sources`: `## What would change this recommendation` (at least one `{{assumption.<id>}}` marker) and `## What we could not check` (at least one `- ` bullet naming a gap and why). "Not checked" is a valid finding.
- The publisher inserts the top unknowns and closed experiments blocks; do not author them. Assumption status changes only through `case_workspace.py assumptions` or `experiment-close`.
- Every paragraph in `## Executive assessment` and `## Recommended next decisions` carries an evidence, numeric or assumption marker, or opens with `Not checked`, `Unknown`, `Insufficient evidence` or `Refuted`. A blunt recommendation must point at evidence or say plainly what is not known.

Legacy cases without a register keep contracts 1 and 2 and cannot close version 3 delivery.

## Decision memo

`python3 scripts/evidence_scout/build_decision_memo.py` writes `decision_memo.md` and `scores.json` from the reviewed ledger or `--draft-claims`; it is a read-only summary, not a publication route. Scoring rules, caps, gate handling and factor-claim limits are in its `--help` and docstring.

- Verdict words are the strategy-plan `verdict` enum; a memo `commit` requires the pain-first gate passed or a recorded override, otherwise it tops out at `test`. Verdicts above `test` should be rare.
- Basis: use the reviewed ledger when it exists; otherwise `--draft-claims` (memo opens "Basis: draft claims, not ledger-bound"; draft claims never score). An `Unreviewed` VOC table may be passed without a source review; its rows never score. Use reviewed inputs when they exist, otherwise the labelled fallback; never skip the memo.
- Final: `--final` is refused without a claim challenge (falsification output of either basis). No final recommendation, final delivery or final case insights without one; progress snapshots are allowed.
- Placement: carry the memo's verdict, riskiest assumption, ≤ 2-week test with cost cap and kill criteria into `## Executive assessment` and `## Recommended next decisions` with the usual markers, and link `decision_memo.md` under `## Sources`. Rerun after any ledger, falsification, VOC table or economics change.
