# Consolidated case insights

For a registered Business case, `cases/<id>/case_insights.md` is the one current
reader-facing assessment. The project README navigates cases; supporting
feasibility, economics and research files remain source material. Do not create
a case-level README for new cases. Older cases with a README stay in legacy
presentation until explicitly converted through the case publisher.

Conversion first checks whether a case, stage, answered question or current
Business plan still consumes the old README. If so, validation identifies the
consumer and publication changes nothing. Refresh that consumer through its
own workflow using the reviewed original sources, then retry conversion. Do
not silently redirect its evidence binding to the new narrative. Once those
references are cleared, conversion archives the README and retires its obsolete
artifact registration while preserving unrelated stage passes.

Use `templates/project/case_insights.md` as the section pattern. Update the
current synthesis after each coherent batch of reviewed research, deep dives, a
founder question that was answered, corrected evidence or changed assumptions;
do not wait for the whole workflow to finish. Retain valid earlier findings.
Integrate each answer where it changes the analysis. A link to a report
does not substitute for the answer or its business implication. State unknown
market size, demand, prevalence or willingness to pay plainly when evidence does
not establish them. Keep process logs, run IDs, validation hashes, skill coverage
and provider mechanics out of the client text.

## Before drafting

1. Resume the case and inspect `case_insights.md`, the case manifest and current
   input inventory. The current document is orientation, not evidence for itself.
2. Capture a material user research question through
   `case_workspace.py record-question` in existing coaching state. Founder
   preferences remain `known_answers`, not customer evidence. Bind an answered
   question to its reviewed analysis/source file.
3. Run `python3 scripts/validate_case_insights.py --workspace <business-root>
   --case <id> --inventory --json`. Reconcile all runs, deep dives, stage
   artifacts, old conclusions and explicit shared inputs. Judge each candidate
   output as incorporated, superseded, duplicate, no material finding or out of
   scope; give a reason. During an interim publication, inputs awaiting review
   may be marked pending only when `scope_status` is `progress` and
   `pending_summary` describes what remains in plain language. A complete
   publication cannot contain pending inputs. Run-level machine derivatives may
   appear as grouped rows; inspect their generated member list when a finding or
   source binding requires it. Do not treat newer files as automatically more correct.
   The inventory includes explicitly applicable shared sources from the case,
   stages, answered questions and the previous insights packet. Shared sources
   newly added to the draft appear in `--prepare` output too: reconcile that
   complete inventory before review. Do not import unrelated shared directories.
   Bindings retain their locator and applicability; inspect changed evidence and
   refresh its binding before incorporating it. Missing inputs need an explicit
   coverage limitation or reasoned exclusion, never an invented finding.
4. Check cited findings against original passages and existing claim reviews.
   Keep customer experience separate from supplier statements. Repeated copies
   of one incident count once.

## Draft and review

Write one concise, cohesive assessment with the sections in the template. Cover
the current customer and problem, market and demand, alternatives, feasibility,
material risks, recommendation, unanswered questions and sources. Use the
existing numeric claim marker for source-attributed decision figures and the
economics marker for model results. Checked numeric context still needs semantic
source inspection; unmarked prose is not automatically verified.

For renewed publications, set `publication_contract_version: 2` and put
`{{evidence_claim.<id>}}` next to each material reviewed VOC statement. Supply
`publication_claims` referencing the existing verified claim ID, supporting
evidence ID and current ledger binding. Bind the ledger, evidence JSONL and
source review; the renderer inserts the original URL from the accepted evidence
record. For official/contextual sources use a bound manual-capture receipt,
capture index and exact retained supporting passage; the renderer checks the
raw capture hash and inserts its original URL and date. Mark inspected secondary
accounts beside the affected claim with a visible limitation; keep legitimate
private interviews as protected local references. The semantic reviewer judges
whether each passage actually supports the statement. A source-list link alone
does not establish claim support. Founder inputs, assumptions and model outputs
must be labeled for what they are.

Prepare the exact rendered document with
`validate_case_insights.py --packet <draft.json> --prepare --out <fresh-dir>`.
Review that rendered text with the input inventory and underlying passages.
Compare conclusions across runs for the same segment, period and definition;
also check different scope, changed dates and unequal evidence strength.
Record each material conflict's source pair, scope, resolution and location in
the document. An unresolved factual disagreement may remain only if the text
discloses it and the recommendation reflects it. Check missing earlier findings,
answered questions, unsupported confidence, inconsistent recommendations and
whether the document can be read without opening an annex. Record reviewer type
and mode honestly; an inline review is not independent.

Record `review.outcome` as `pass` or `revise`. Each check has `status`
(`pass`, `fail`, or `not_reviewed`) and an evidence-bearing `rationale`.
List unresolved defects in `blocking_findings`, even when the rest of the brief
is good. Publication requires outcome `pass`, every check passed and an empty
blocking list. Fix the draft and review the newly rendered text before clearing
defects. Real-world uncertainty disclosed in the text is distinct from an
unresolved defect in the review. The validator enforces these explicit outcomes;
it does not infer approval from prose. Older packets without outcomes need a
fresh review and cannot establish a current reviewed brief.

Publish after each substantive review batch through the same validator and
publisher. An interim document must state that research continues and identify
the decision-relevant open question or coverage limit; it remains a useful
current snapshot, not a completed investigation. Newly captured material must
not support a claim until reviewed. Changes to evidence already supporting a
finding stale the publication until it is revised. Final delivery still requires
the requested scope and all pending dispositions to be resolved or honestly
closed.

For `scope_status: complete` under v2, store an actual separate reviewer record
under `cases/<id>/market_research/case_insights/reviews/` and bind it as
`independent_review`. The record identifies author, reviewer and task; binds the
exact rendered and inventory digests plus every reviewed source path/digest; and
states outcome and material findings. Review the original case concept, source
passages and roles, country/period, numeric context, answered deep dives,
counterevidence, founder fit and the recommendation. Resolve material errors or
make uncertainties visible before `pass`. Inline review remains valid for
progress snapshots, never for completed v2 delivery. Local identities are
inspectable records, not proof against dishonest authorship. A completed run
must itself be bound into the current insight snapshot; a different current
snapshot cannot close its delivery check.

The packet uses the case's current assessment and manifest revisions,
`document`, `source_bindings`, complete `coverage`, `question_coverage`,
`conflicts`, `numeric_claims` when relevant, an `impact` classification and a
`review` bound to rendered text and inventory digests. Set `scope_status` to
`progress` and provide `pending_summary` for an interim publication; use
`complete` only after final reconciliation. Run the validator on the
reviewed packet. It checks structure, coverage declarations, figures and
freshness; the reviewer owns semantic accuracy and materiality judgments.
For a case with no comparison yet, supply `comparison` with plain-language
`summary`, `principal_uncertainty` and `next_action`. If a current comparison
exists, retain those fields verbatim in a presentation-only insights refresh;
change assessed conclusions through `case-appraisal` first.

The packet is JSON. The shape below is illustrative: use the current inventory,
actual bindings and digest outputs; never copy its example values into a case.

```json
{
  "assessment_revision": 1,
  "manifest_revision": 2,
  "impact": "presentation_only",
  "comparison": {"summary": "Current scoped conclusion", "principal_uncertainty": "What remains unverified", "next_action": "The next decision-changing test"},
  "document": "# Actual case title\nLast updated: ...\n...",
  "source_bindings": [],
  "coverage": [
    {"path": "cases/example/market_research/.../report.md", "digest": "...", "disposition": "incorporated", "reason": "Explain the substantive use.", "section": "Customer and problem"}
  ],
  "question_coverage": [
    {"id": "market-size", "section": "Market and demand", "reason": "Explain how the answer was integrated."}
  ],
  "conflicts": [
    {"left": "source path", "right": "other source path", "scope": "same buyer and period", "resolution": "unresolved_disclosed", "rationale": "Explain both readings and the decision consequence.", "section": "Risks, conflicting evidence and open questions"}
  ],
  "review": {
    "reviewer_type": "analyst",
    "review_mode": "inline",
    "outcome": "pass",
    "blocking_findings": [],
    "summary": "State what was actually inspected.",
    "checks": {
      "accuracy": {"status": "pass", "rationale": "Source-to-claim review rationale."},
      "completeness": {"status": "pass", "rationale": "Input and question coverage rationale."},
      "contradictions": {"status": "pass", "rationale": "Cross-run comparison rationale."},
      "clarity": {"status": "pass", "rationale": "Standalone reader review rationale."}
    },
    "rendered_digest": "<from prepare>",
    "inventory_digest": "<from inventory>"
  }
}
```

Publish with `python3 scripts/case_workspace.py insights --workspace
<business-root> --case <id> --input <reviewed-packet.json> --decision-id <id>
--reason <reason>`. This uses the existing recoverable transaction. A mere
presentation rewrite does not revalidate a research stage. Changed concept,
economics or established recommendation uses `case-appraisal` or correction,
with existing invalidation; then refresh the insights. Research may continue
while consolidation is pending, but do not describe the old brief as current.

When source correction withdraws a supporting document, its numeric claims are
retired in the same transaction and preserved in history with the earlier text.
Claims in unchanged documents remain checked; a stale claim cannot be bypassed
by simply omitting its source from a new insights packet.

Before closing a substantive case task, check the published document with
`validate_case_insights.py --workspace <business-root> --case <id> --json` and
link it to the user. For focused answers outside a registered case, apply the
task-scope rules; do not create a case just to answer the question.

Source links are relative to `case_insights.md`. A shared source under the
Business root can be cited as `../../market_research/<source>.md`. Parent
segments are allowed while the target stays within that Business workspace;
missing files, filesystem escapes and symlink traversal are rejected.
