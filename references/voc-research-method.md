# Customer-needs research method

Use for substantive market discovery, customer/problem validation and competitor
feedback, not a narrow factual lookup. This is the shared research contract;
`customer-voice.md` owns source planning and U/R distinctions. Countries,
languages, roles, companies and job vocabulary are runtime inputs.

## 1. Questions and coverage before themes

Record the decision, research questions, requested locales and plausible roles:
user, buyer, payer, decision-maker, intermediary or supporting person. Unknown
roles/segments are discovery questions, not reasons to demand a founder thesis.
Always run topic-led discovery. Discover entities/substitutes through customer
accounts; verify identity, then add entity feedback. Do not search only for
competitor complaints.

Use `plan_customer_feedback.py` for both passes, including when no entity is
known. Extend its locale cells with `--topic-cells-json`: each object contains
`locale`, `job`, `role`, `source_family` and `query_intent` where decision-relevant.
Include routine/successful journeys, painful episodes, workarounds, non-adoption,
switching and exit. Translate actual customer vocabulary; do not mechanically
use English phrases in every market. Forum/Facebook discovery and locally
relevant review sites must be considered. Inapplicability needs a reason;
missing locators are discovery work. Do not make every Cartesian combination
mandatory: explain the relevant sampling cells for this study.

Record executed queries separately from proposed queries. Review unattempted
cells after each batch; widen or change searches using customer vocabulary,
unexpected alternatives and missing perspectives. Firecrawl/Serper balance the
early query intents; other provider schedules require explicit inspection.
Provider success does not establish usable voice. Paid customer-evidence APIs
are authorized without a monetary cap; failed credits require notification,
fallback and a preserved gap, never an absence-of-demand conclusion.

Within each source record sort order, rating/text filters, time window,
product/version, pagination, returned/accessibly available totals and provider
subset restrictions. Unknown is valid. Compare contrasting relevant slices
when a recent outage or platform ranking dominates, or bound conclusions to
that slice. Do not impose equal star quotas or claim representativeness.
Storefront/query locale is not the author's location or language.

Apple RSS has a country storefront, not a language filter. Multiple requested
languages in one country produce a country:und capture and explicit unresolved
language coverage. To use a review in one requested language cell, source review
adds `language_review` with language, exact supporting_passage and rationale.
The validator resolves that scoped membership without rewriting the original
capture; unsupported other language cells remain gaps.

## 2. Documents → speaker experiences → source review

Search snippets identify destinations; hydrate before accepting testimony.
Full extracted pages are documents, not one customer's voice. Preserve raw
content. Split by speaker and episode, including separate supplier replies and
quoted third-party statements. Do not infer authorship from sentiment or “I”.

Use the existing collector for reviewed targeted sources. Generic independent
review/forum entity pages use:

```bash
python3 scripts/evidence_scout/collect.py \
  --topic '<job>' --customer-segment '<segment>' \
  --sampling-frame entity_led_feedback --subject-entity-id '<id>' \
  --customer-feedback-source-plan '<plan.json>' \
  --entity-source-url '<exact reviewed URL>' \
  --entity-source-lane external_forums_communities \
  --geo '<CC>' --language '<language>' --providers firecrawl
```

For documents, propose an annotations JSON array containing `document_id`, exact
`start`/`end` character offsets, `quote`, source-local `speaker_id` (or unknown),
`speaker_basis`, and `speaker_role` (`customer_candidate`, `supplier`,
`quoted_other`, `unresolved`). Optional `observations` identify triggers,
actions, alternatives, outcomes and consequences: each records `attribution`
(`observed`, `inferred`, `unknown`); observed fields need `supporting_quote`,
inferences need `rationale`. Keep chronology, conditions and negation intact.

```bash
python3 scripts/evidence_scout/build_experience_ledger.py \
  --documents '<capture/evidence.jsonl>' --annotations '<episodes.json>' \
  --out '<analysis/evidence.jsonl>'
```

The helper validates exact spans, not semantic accuracy or episode recall.
Inspect the whole document for missed voices/rare consequential episodes.
Translations retain `original_quote`; inferred geography requires an explicit
basis. Unknown independence stays unknown. Count documents, experiences,
incidents and independently attributable people separately. Do not merge
cross-site identities speculatively. The same observation reached through both
sampling frames is one observation with multiple discovery memberships.

Write the digest-bound source-review sidecar against the *experience* evidence
file. `reviewed_voice.py` is shared by synthesis, claims and interview consumers.
Keep original classifications intact. Correct heuristic editorial/competitor
labels only with a reviewed local source kind, rationale, exact
`supporting_passage` and `author_context_basis`; correcting an irrelevant label
also needs `relevance_correction_rationale`. Explicit supplier attribution
cannot be overridden. Known creator/quoted-other material is not customer voice.
Reviewer proposals, unresolved entries and accepted firsthand voice stay distinct.

## 3. Code and compare before making a needs map

Maintain a versioned codebook with each code's definition, inclusion/exclusion
criteria, source-linked quoted instances and revision notes. Start from research
questions, then add unexpected codes. One experience may have several motives;
unexplained motivation remains unknown. Inspect outliers and compare context,
role, journey moment, alternative and outcome before combining themes.

New studies use `customer-voc-synthesis.json` schema_version 2 with status
`supported`, `scoped`, `provisional` or `insufficient_evidence`, the existing
topic/entity ID lists and U/R arrays, plus `codebook` and `next_investigations`.
Each U/R retains existing fields and adds:

- `context`: U uses role, trigger, current_alternative, observed_behavior,
  consequence; R uses role, use_episode, acceptable_outcome, actual_performance.
  Use the string `unknown` when unsupported.
- `scope`: collection_locales, segment_relations, applicability_limits. These
  bind the actual sources; target-country transfer is a separate claim.
- `assessment`: unmetness, confidence_rationale, disposition, next_question.
  Assess occurrence, importance, current satisfaction, alternatives and payment
  separately. A rare consequential need must not disappear under “convenience”.
- `inference_rationale`, `counter_evidence_ids` (or counter_search_scope), and
  `code_ids`. Review recommendation-changing contrary cases explicitly.

`codebook` contains version, revision_notes and codes; each code has id,
definition, include_when, exclude_when, instances (`evidence_id`, `quote`).
`next_investigations` contain question, method, reason and decision_change.
Retain unresolved/excluded critical concepts with reasons in the narrative;
do not quietly discard them to improve a neat map.

Finalize coverage, then run `validate_customer_voc_synthesis.py`. Structural
validation checks provenance and scoped fields; an analyst must still judge
whether each claim follows from the source. Legacy maps report
`legacy_unassessed`; never silently upgrade their review quality.

For commercial/population/transfer claims use the existing claim ledger,
`validate_synthesis.py --source-review <review.json> --customer-segment '<scope>'`.
Specify claim_type and scope, with confidence_assessment explaining provenance,
target_fit, independence, context, recency, counterevidence and coverage.
One located account can establish occurrence, not prevalence. Prevalence needs
a sampling_basis; unmetness needs alternatives_assessment; willingness_to_pay
needs price_bearing_behavior_evidence; transfer needs applicability_basis.
Mention counts and strong-sounding prose cannot supply these missing facts.

### Underserved and latent outcomes

Within existing U-need assessments distinguish dissatisfied users, nonconsumers blocked by cost/access/time/skill, overserved customers who may accept less complexity, and adequately served customers. Apply only relevant sampling lenses. Link situation, desired outcome, actual alternative (including doing nothing/informal help), shortfall and consequence to reviewed experiences.

For a latent need retain observation → interpretation → competing explanation → disconfirming test in the existing `inference_rationale`, assessment and next-investigation fields. Silence or adaptation can conceal a consequential shortfall or reflect low urgency; a workaround does not establish switching/payment intent. Compare importance and satisfaction separately. Never derive opportunity scores or population prevalence from mention counts or invented survey ratings. `insufficient_evidence` differs from supported adequate service. Preserve rare consequential cases and negative findings.

Method sources checked 17 September 2026: [Strategyn](https://strategyn.com/outcome-driven-innovation/), [Christensen Institute](https://www.christenseninstitute.org/blog/to-build-a-new-market-overcome-these-4-barriers/), [interview-to-jtbd](https://github.com/lowwwbank/interview-to-jtbd). Use the local evidence ledger rather than adding another extraction tool.

## 4. Partial findings and the next learning step

Execution completeness, coverage and claim readiness are separate. A missing
market/platform is a visible gap, not a reason to suppress all useful findings.
Report scoped findings without implying the unobserved market is covered.
Zero accepted voice yields insufficient_evidence and named next questions,
not manufactured U/R objects or “no demand”. Invalid attribution still blocks.

Select the method for the missing knowledge:

| Unanswered question | Suitable next investigation |
| --- | --- |
| Missing local/community sources or accessible perspectives | More targeted discovery or a different retrieval route |
| Trigger, motive, decision roles, real sequence or handoff | Non-leading incident interviews or contextual observation |
| Whether a solution works acceptably | Observed task/usability test with an R criterion |
| Switching/payment behavior | Separately authorized behavioral/price-bearing test |
| Current provider/legal/operational fact | Verify the relevant primary source |

Interview selection keeps all reviewed material_counterexample cases and then
adds distinct perspectives, stages, jobs, alternatives and outcome_statuses.
Inspect `interview-selection.json`; a numeric limit is not a justification for
silently omitting a decision-changing contrast. Incorporate interview episodes
in the same evidence/review/codebook process. No fixed number of confirmations
validates a need and one refutation does not erase other contexts.

Stop with an explicit reason: scoped questions answered, mostly duplicates,
unresolved access, or a more informative next method. Keep study limits visible.
Unpaid recruitment and launch/outreach authorization remain unchanged.

## Method and implementation sources

Checked 2026-09-16: [GOV.UK analysis of research sessions](https://www.gov.uk/service-manual/user-research/analyse-a-research-session),
[question-driven research planning](https://www.gov.uk/service-manual/user-research/plan-user-research-for-your-service),
[LangExtract source grounding](https://github.com/google/langextract),
[QualCoder](https://github.com/ccbogel/QualCoder),
[Argilla](https://github.com/argilla-io/argilla).
These inform the located-span, codebook and suggestion/review patterns; no
third-party package is required and their performance is not claimed here.
