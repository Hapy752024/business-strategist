# Customer voice from competitors and similar services

Contents:
- [Two complementary analyses, with topic-led discovery mandatory](#two-complementary-analyses-with-topic-led-discovery-mandatory)
- [Ownership and sequence](#ownership-and-sequence)
- [Review the source and the claim separately](#review-the-source-and-the-claim-separately)
- [Separate the reasons, allow multiple motives](#separate-the-reasons-allow-multiple-motives)
- [Separate customer needs from solution-use requirements](#separate-customer-needs-from-solution-use-requirements)
- [Build both maps, then assess each item for our case](#build-both-maps-then-assess-each-item-for-our-case)
- [Hand off to pilot scope, smoke testing and GTM](#hand-off-to-pilot-scope-smoke-testing-and-gtm)
- [Execution boundary](#execution-boundary)

Apply when interpreting customer needs, motivations, praise or complaints about an existing service, or using those inputs to refine a venture's segment, journey, risks or requirements. A narrow factual competitor lookup does not require a full study. Reuse current reviewed evidence when its entity, audience, product, geography and date fit; record gaps rather than manufacture coverage.

## Two complementary analyses, with topic-led discovery mandatory

Every substantive customer-input study runs **topic-led VOC discovery** first,
even when competitors are already known. Search from the customer's job,
trigger, problem, workaround and desired outcome across forums, communities and
other relevant sources without requiring an incumbent name. This reduces the
risk of learning only the issues that existing products make visible.

Also run **entity-led customer-feedback analysis** whenever at least one
competitor, substitute or similar company has been identified and verified. If
no entity is known yet, record this analysis as `pending_entity_discovery`, run
competitor discovery, and start it once a usable shortlist exists. Entity-led
analysis asks why, when and how identifiable customers use or reject the
service, and what they praise, complain about, work around, repeat, switch or
stop. It must not replace the mandatory topic-led pass.

Keep the two sampling frames and evidence counts separate. Join them only in
the U/R maps after source review:

- Topic-led evidence mainly informs independent customer needs, triggers,
  alternatives and unknown entities, though it may also reveal requirements.
- Entity-led evidence can inform both independent needs and solution-use
  requirements. A complaint about an incumbent feature is not automatically an
  independent need; praise is not proof of the reason for buying.

For each verified entity, create an applicability and coverage matrix with at
least these source lanes: independent review platforms (for example Trustpilot
or a locally relevant equivalent), Google business/location ratings and review
text where the entity has a physical listing, the company's Facebook and
Instagram properties plus customer comments, Apple App Store reviews and
Google Play reviews as separate lanes where an app exists, external
forums/communities, and company-hosted testimonials/support
material as supplier context only. Each lane records `applicable`, `planned`,
`attempted`, `retrieved`, `reviewed`, `accepted`, `failed_or_blocked`, and the
reason for `not_applicable`. Missing handles, Place IDs or review profiles are
discovery tasks, not evidence that the lane is inapplicable.

Star averages, rating counts and supplier posts are context, not customer
voice. Separate the company's reply from the review author. Bind every item to
the exact entity, product/location and runtime `COUNTRY:language` market;
preserve unresolved matches. A locator reviewed for one locale does not
authorize another locale or app storefront.
Sample both favorable and unfavorable feedback and more than one time window
where coverage permits. Platform-ranked or API-limited review subsets are
convenience samples, so report the retrieved denominator and never infer
prevalence from them.

Create the initial matrix before entity-led collection:

```bash
python3 scripts/evidence_scout/plan_customer_feedback.py \
  --topic "<customer job/problem>" \
  --customer-segment "<segment>" \
  --locale <CC>:<language> \
  --entities-json <verified-entities.json> \
  --out-dir <research-run>/customer-feedback
```

The optional entity file is a list (or an object containing `entities`) with
`id`, `name`, `domain`, `lane` (`competitive_market`, `similar_company`, or
`substitute`), `sources` keyed by source lane, and reasoned `not_applicable`
entries. Omit `--entities-json` when none are verified: the artifact keeps
topic-led VOC required and records entity-led work as pending.
For capture-capable entity locators, use locale-scoped source objects such as
`{"locator":"official_handle","locales":["CH:de"],"review_status":"accepted","review_reason":"linked from the verified company domain"}`.
A plain string is sufficient for discovery planning but cannot authorize
capture. An accepted locator without explicit locale membership cannot
authorize any locale, and is never copied into other markets.

After collection and human source/author review, write one result per
`entity_id + locale + source_lane`, with a `locator_results` entry for every
accepted locator. Each locator records attempted/failed status and its own
retrieved, reviewed and accepted denominators plus the exact unique
`accepted_evidence_ids`; topic-led results carry the same accepted-ID ledger.
Lane totals must reconcile to their sum. Then run:

```bash
python3 scripts/evidence_scout/finalize_customer_feedback.py \
  --plan <customer-feedback-source-plan.json> \
  --results <customer-feedback-results.json> \
  --out <customer-feedback-coverage.json>
```

Coverage schema v2 separates execution, coverage and claim readiness. Bind topic
results to the plan's topic_matrix cell IDs; global legacy results remain
unscoped. Missing/failed locales or platforms remain explicit gaps while useful
scoped findings from accepted sources may be synthesized. Invalid denominators,
unreviewed captures or supplier voice still block. Zero accepted voice yields
insufficient_evidence, not an empty successful study. Apply
the Customer-needs research method section below for the version-2 research contract. After
building separate U and R objects, validate them and their sampling-frame links:

```bash
python3 scripts/evidence_scout/validate_customer_voc_synthesis.py \
  --evidence <evidence.jsonl> --coverage <customer-feedback-coverage.json> \
  --source-review <source-review.json> --customer-segment "<exact segment>" \
  --synthesis <customer-voc-synthesis.json>
```

The synthesis validator accepts only source-review entries that are bound to
the evidence file and segment, identify firsthand customer voice, and have an
original customer-review/statement/community role with a non-supplier voice
status and intent. Missing original role/voice fields fail closed.
It also reconciles every topic-led evidence ID to the finalized topic ledger
and every entity-led ID to the finalized entity, locale, lane and locator.

Discover review platforms at runtime for the entity's market and business
model; do not assume every platform contains every company. Non-exhaustive
starting points include Trustpilot across markets; ProvenExpert, eKomi,
AUSGEZEICHNET.org and golocal in Germany; Trusted Shops for relevant ecommerce
entities; and Avis Vérifiés, Custplace, PagesJaunes and Opinion System in
France. Search for additional local or sector-specific platforms when the
entity/category warrants it, while excluding hospitality- or restaurant-only
sites unless the investigated case itself requires them. Record whether reviews
are open, invited, transaction-linked, aggregated from other platforms, or
unresolved; a platform's own authenticity claim is methodology context, not a
blanket truth label for every review.

## Ownership and sequence

1. Identify and disambiguate the relevant competitor, substitute or foreign analog first. Confirm its domain, product and operating market; similar names are not interchangeable. Reuse a verified shortlist or use competitor-scout when identification is needed. Do not require a full landscape before listening to customers.
2. Evidence-scout owns independent customer-voice retrieval and source review. Competitor-marketing-analyzer owns supplier positioning, prices and promises; these explain the offer but cannot establish customer motives. Competitive-landscape-builder joins these distinct inputs without merging their provenance.
3. If the segment is unknown, explore broadly to form explicit segment/job hypotheses, then narrow retrieval by hypothesis, country, role and trigger. With a known target, start with targeted queries. Keep useful adjacent/foreign voices labelled; never silently broaden the target to fill a quota.
4. Build separate customer-needs and solution-use requirements maps below, then assess **each** mapped item for this venture before final segment/journey/pain synthesis and before opportunity-risk-designer ranks assumptions and tests. Service-customer-perspective-challenger uses the reviewed buying contexts; interview-bridge turns remaining uncertainties into neutral probes. This is a research loop, not a new stage pass or mandatory extra skill invocation for every follow-up.

## Review the source and the claim separately

Preserve source URL, publication date (unknown if unavailable), retrieval date, source language, exact entity/product, geography, author context and evidence ID. Use public pseudonyms or a source-local identifier for deduplication; do not infer identity or collect private details. Distinguish quoted text from analyst paraphrase and retain raw/run provenance where available. Link translations to the original wording and preserve ambiguous meanings.

Classify each voice as firsthand current/former customer, prospective user, observer/nonuser, supplier/affiliate or unresolved. Supplier-selected testimonials and paid/affiliate promotion stay labelled even when they quote a customer. A forum post mentioning a brand is not automatically a usage report; one person's posts, syndicated reviews and quoted replies are not independent customers. State what the author actually did, considered, praised or disliked, and separately what the analyst infers.

Record target/adjacent/unresolved segment fit with its reason. Country, business model, personal versus business use, product vintage and transaction journey matter. A foreign business owner's report can suggest a local interview hypothesis; it cannot validate the local target. Historical bugs, fees and eligibility rules require current verification before describing current product behavior. Source-access failures and zero collected records are coverage gaps, not evidence of no demand or no complaints.

## Type every reviewed statement (Mom Test)

Set `statement_type` on each accepted source review (the review layer holds the judgement; raw collector records may only carry `unclassified`). Packets from `build_review_packet.py` carry `statement_typing: true` and, with `--summary <run>/summary.json`, a Methodology section (queries per provider with locale, providers attempted or skipped with status and reason, key recorded or not as the collector logged it, sampling frames, date range); carry it into the report so skipped providers read as coverage gaps; reference the packet from the source-review file via `source_packet` (or start the file with `statement_typing: true`); every accepted review then requires the field. Older reviews without it count as `unclassified` and warn but do not block. A review file is new-style (typing required) if it carries `statement_typing: true`, references a typed packet via `source_packet`, has `schema_version` >= 2, or is dated 2026-10-30 or later. The same check applies to claim-ledger `supporting_evidence` for occurrence, pattern, unmetness, prevalence and willingness_to_pay claims.

| Type | Meaning | Example | May support pain/demand? |
|---|---|---|---|
| `past_behaviour` | What they actually did or experienced | "Last month I re-keyed 40 invoices by hand." | Yes |
| `commitment` | Time, reputation or money given up | "I paid 90 CHF for a template; intro'd my boss." An agreed meeting with no cost is not a commitment. | Yes |
| `compliment` | Praise or encouragement | "Great idea, I love it." | No |
| `fluff` | Generic or hypothetical talk | "I would definitely use that." / "I always..." | No |
| `feature_request` | A wished-for solution | "It should have an export button." | No (lead for a follow-up question) |
| `unclassified` | Not yet judged or unclear | Snippet without context | No |

The synthesis validator rejects any U/R item whose `evidence_ids` cite a statement that is not `past_behaviour` or `commitment`.

## Separate the reasons, allow multiple motives

For each supported observation, distinguish:

| Decision | What to establish |
|---|---|
| Underlying tool/category | Why use a card, loan, accounting tool or other underlying product? |
| Intermediary/job | Why add this service instead of the direct/default workaround? What specific barrier does it remove? |
| Provider choice | Why select this provider rather than another way to perform that job? |
| Repeat, switch or exit | What sustains use, and what event ends it? Distinguish observed repeat payments from claimed future use and cohort retention. |

Code multiple motives where supported and use **unknown** where they are not. For payment services, possible codes include ordinary ongoing rewards, welcome offer, recurring or annual spend threshold, shortfall top-up, payment timing/liquidity, acceptance/access, convenience/reconciliation and reliability/trust. These are hypotheses to check, not a compulsory fintech-only taxonomy or an assumption that rewards dominate.

“Bonus”, “points” and translated reward terms do not necessarily mean a signup or threshold promotion. Resolve from the original context or keep the mechanism unknown. A business owner may seek travel rewards without having a cash shortage. Praise for speed or support supports a provider-choice requirement; it does not by itself explain why an intermediary is needed or demonstrate willingness to pay its fee. An app installation, account signup or a few repeated bills is not a retention cohort.

Search beyond the initial community's interest: include routine users, dissatisfied/lapsed users, substitutes and non-adopters where reachable. A rewards forum over-samples reward motivations. Report the search scope and missing perspectives. Do not claim a motive is exclusive, dominant or prevalent without a suitable sampling basis and denominator; counts describe the reviewed sample only. Several motives can coexist for the same customer and change over time.

Reviewed firsthand perspectives use explicit labels: `customer`,
`former_customer`, `prospective_user`, or `nonadopter`. Prospective-user and
non-adopter evidence needs a concrete decision context and may support needs,
barriers and evaluation requirements; it must not be relabelled as product use,
purchase or retention. U/R synthesis perspectives must exactly equal the
perspectives of their contributing reviewed evidence; unsupported customer or
usage labels are rejected.
An unfamiliar local forum or independent-review domain may be promoted after
semantic source review records its source kind and rationale. Supplier,
editorial and official-provider material cannot become customer voice. A
heuristic misclassification may be corrected using a located original passage
and author-context evidence through the shared reviewed_voice contract; explicit
supplier attribution remains excluded.

## Separate customer needs from solution-use requirements

A **customer need** is a desired outcome or problem that exists independently of our proposed solution. A **solution-use requirement** arises when evaluating or using a solution: what must be true for that solution to work acceptably. Keep these as separate analytical objects and maps; a shared evidence episode does not make them the same need.

For example, **meet obligations while preserving cash for other commitments** is an independent need if the customer evidence supports it. **Know whether the recipient received this payment** is a solution-use requirement. **Obtain desired travel at an affordable net cost** can be a need if the customer states that outcome; earning points is then a mechanism. Accept a card, install an app or earn points may describe means rather than the independent outcome. Ask what the means achieves in the actual source, and preserve the stated mechanism with an unknown underlying outcome when the source does not say. Do not invent deeper psychology or cash shortages to make the map complete.

Use the existing evidence ledger and deep-dive narrative; no separate database is required. Give independent needs **U IDs** and solution-use requirements **R IDs**. Preserve derivation links where supported:

`evidence ID / observed episode → U need (if evidenced) → R requirement (if evidenced or explicitly inferred) → separate tests`

An R item may link to several U items, or be a **supporting operational requirement, motivational root unknown**. Do not force every payment-status or receipt complaint into an inferred purchase motivation. Mark each item as customer-stated, analyst-inferred or unknown, with source IDs and reasons. Praise for helpful support can inform an R item without establishing a new U need or willingness to pay.

Example: a payer reports a failed-payment notice while their card shows a pending hold → **R1: determine payment state and whether retrying is safe** → candidate behavior that distinguishes authorization, settlement and failure → test comprehension and reconciliation in a failed-payment scenario. The report alone does not establish why the payer originally needed the intermediary. Do not relabel the hold as a settled duplicate charge or count R1 as an additional independent customer pain.

## Build both maps, then assess each item for our case

Build the maps before selecting favored themes. Combine duplicate items within each map but retain source links, conflicting reactions and distinct contexts. Use these compact templates in the current deep dive:

**Customer-needs map**

| U ID | Customer / trigger / source IDs | Independent desired outcome or problem | Stated / inferred / unknown | Current alternative and unmetness evidence | Assessment link | Verdict / next test |
|---|---|---|---|---|---|---|
| U1 | Identified role/context or unknown | Outcome that can be described without our solution | Attribution and reason | What fails today, or unknown | U1 assessment | pursue / test / defer / not applicable / unknown, with reason |

**Solution-use requirements map**

| R ID | Evaluation/use step / source IDs | Required outcome or condition when using a solution | Linked U IDs or operational root unknown | Stated / inferred / unknown | Current solution performance | Assessment link | Verdict / next test |
|---|---|---|---|---|---|---|---|
| R1 | Identified episode/context or unknown | Requirement distinct from a proposed feature | U1 if supported; otherwise supporting operational requirement, motivational root unknown | Attribution and reason | Met / poorly served / unknown, with evidence | R1 assessment | adopt / test / defer / not applicable / unknown, with reason |

Deep-dive **every distinct U and R item**, proportionately; a short explicit nonapplicability or insufficient-evidence assessment counts, silent omission does not. Do not double count a U item, its R derivatives or multiple posts from the same person as independent pain observations or customers.

For each **U need**, assess:

- **User and moment:** segment/role, trigger, independent desired outcome and observed behavior; preserve unknowns.
- **Evidence and transfer:** source quality, contrary observations and country/product/date fit. Distinguish occurrence, inadequacy of substitutes, prevalence, target-country transfer and willingness to pay as separate claims.
- **Unmetness and value:** how well current alternatives achieve the outcome, consequence of the remaining gap and observed willingness to pay/switch. A complaint about an incumbent does not prove the customer's need is unmet across alternatives.
- **Relevance and disposition:** why this venture could address the outcome, the key evidence gap, and pursue/test/defer/not applicable/unknown with a reason. This is a hypothesis choice, not a validation pass.

For each **R requirement**, assess:

- **Use context and derivation:** which evaluation or use episode creates it, whose requirement it is, and its supported U links or unknown motivational root.
- **Performance and alternatives:** what acceptable performance means, evidence of satisfaction or failure, current competitor behavior and country/product/date fit. Distinguish a requirement from a user's suggested implementation.
- **Importance and feasibility:** whether it is necessary for successful use, a provider preference or a potential differentiator; evidence for that distinction, material cost, dependencies and constraints. Leave unresearched importance or estimates unknown.
- **Relevance and disposition:** adopt/test/defer/not applicable/unknown with reason and a suitable performance/comprehension test. “Adopt” selects a requirement direction within authorized scope, not an automatic feature build, differentiation claim or stage pass.

Well-matched public customer accounts, observed behavior and checked alternatives can substantiate particular needs or requirements without interviews. Interviews are one way to resolve remaining uncertainty, not a universal prerequisite for every finding. Record **unmet customer need** separately from **poorly served solution-use requirement**. Neither automatically establishes an unmet commercial opportunity: an alternative may already satisfy the need, the user may not switch, or meeting the requirement may be ordinary service quality rather than a reason to buy.

Only after both assessments, prioritize relevant need hypotheses and requirement tests. Keep both maps linked from the current README; link R items to their actual sources as well as any U derivation. Maintain mapped scope when evidence or founder constraints change. For narrow follow-ups, update affected items and explicitly reuse unaffected assessments rather than repeat the full study.

For each company, summarize **who is identifiable; observed jobs and use; motives by decision; praise; complaints; repeat/exit; target fit; evidence limits**. If a field is unknown, leave it unknown. Update the current README and relevant segment, journey and pain hypotheses with what changed and what did not. Explain any changed recommendation; maintain competing hypotheses when evidence is insufficient. Ask only a decision-changing founder question, and use interviews to establish missing customer facts rather than asking the founder to invent them.

## Hand off to pilot scope, smoke testing and GTM

For sufficiently supported, relevant U needs and R requirements, carry their distinct IDs, evidence and confidence into the existing test/GTM brief. Keep the handoff provisional where the applicable strategy or pain gate has not passed. For deferred or unsupported U/R items, record the evidence needed to reconsider them rather than quietly adding them to a pilot.

| Decision | Required handoff |
|---|---|
| Pilot scope | Identify the U outcomes the pilot investigates and separately include/exclude R requirements needed for that test. Keep necessary operational R items even when their motivational root is unknown, with the reason documented; record dependencies and exclusions. |
| Smoke test | Lead with an evidenced U outcome; test an R preference separately when relevant instead of presenting usability interest as proof of the U need. Specify a qualified observable behavior, with denominator, test window and explicit success/stop thresholds. Thresholds are experimental decisions, not researched market facts. Distinguish a click, qualified signup, interview attendance and price-bearing commitment; one cannot substitute for another. |
| Recruitment | Define a screener based on the target role, trigger and recent experience, plus researched access channels using `interview-recruitment.md`. Offer no cash, vouchers, gifts or compensated panels unless the founder changes the preference; unpaid signups still require screening. |
| GTM | Use U evidence for segment, outcome message and offer hypotheses; use R evidence for service promises, evaluation objections and delivery requirements. State whether evidence supports each choice. Praise for an incumbent feature does not automatically justify differentiation or demand claims. |
| Next uncertainty | Name the most consequential unresolved assumption and the cheapest suitable evidence/test, which may be further desk verification, interviews or an authorized behavioral experiment. |

Preparing a scoped test brief is distinct from launching it. Publishing, outreach, advertising/distribution spend and live pilot operations retain their authorization requirements; commitment work retains existing stage gates. A smoke page's purpose may be qualified interview recruitment, message testing or demand testing: choose explicitly and measure that purpose instead of treating contact collection as paid demand validation.

## Execution boundary

The catalog and route packet bind this reference to relevant specialists; route validation rejects missing or invalid bound files. The caller reads applicable references before dispatch. These checks establish availability and routing, not that an LLM correctly interprets every source or obeys the research method. The existing source-review and stage gates remain authoritative; this reference does not automatically pass them. Live semantic quality needs review of actual research outputs.

## Customer-needs research method


Use for substantive market discovery, customer/problem validation and competitor
feedback, not a narrow factual lookup. This is the shared research contract;
the sections above own source planning and U/R distinctions. Countries,
languages, roles, companies and job vocabulary are runtime inputs.

### 1. Questions and coverage before themes

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

### 2. Documents → speaker experiences → source review

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

### 3. Code and compare before making a needs map

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

#### Underserved and latent outcomes

Within existing U-need assessments distinguish dissatisfied users, nonconsumers blocked by cost/access/time/skill, overserved customers who may accept less complexity, and adequately served customers. Apply only relevant sampling lenses. Link situation, desired outcome, actual alternative (including doing nothing/informal help), shortfall and consequence to reviewed experiences.

For a latent need retain observation → interpretation → competing explanation → disconfirming test in the existing `inference_rationale`, assessment and next-investigation fields. Silence or adaptation can conceal a consequential shortfall or reflect low urgency; a workaround does not establish switching/payment intent. Compare importance and satisfaction separately. Never derive opportunity scores or population prevalence from mention counts or invented survey ratings. `insufficient_evidence` differs from supported adequate service. Preserve rare consequential cases and negative findings.

Method sources checked 17 September 2026: [Strategyn](https://strategyn.com/outcome-driven-innovation/), [Christensen Institute](https://www.christenseninstitute.org/blog/to-build-a-new-market-overcome-these-4-barriers/), [interview-to-jtbd](https://github.com/lowwwbank/interview-to-jtbd). Use the local evidence ledger rather than adding another extraction tool.

### 4. Partial findings and the next learning step

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

### Method and implementation sources

Checked 2026-09-16: [GOV.UK analysis of research sessions](https://www.gov.uk/service-manual/user-research/analyse-a-research-session),
[question-driven research planning](https://www.gov.uk/service-manual/user-research/plan-user-research-for-your-service),
[LangExtract source grounding](https://github.com/google/langextract),
[QualCoder](https://github.com/ccbogel/QualCoder),
[Argilla](https://github.com/argilla-io/argilla).
These inform the located-span, codebook and suggestion/review patterns; no
third-party package is required and their performance is not claimed here.

## Query design and refinement across research workflows

Use for substantive market, operator, competitor and community discovery. A focused factual lookup does not require a full calibration experiment. Reuse current sources and reviewed vocabulary before collecting again.

### Before collection

1. Separate the research brief from short search phrases. Record target country, search language, original source language and intended audience independently. A translated result or English-language author does not establish residence or native language.
2. Brainstorm both vocabulary and source locations: local category names, acronyms, customer/operator situations, substitutes, counterexamples, and places where the relevant people or organizations publish. Disambiguate terms that name unrelated industries. Do not translate one long English sentence and call it coverage.
3. Review the candidate set for distinct questions, native terminology, source fit, missing lanes and confirmation bias. This is an analyst review, not another user permission gate. Preserve rationale and unresolved language judgments; do not label inline review independent.
4. Preview the executable schedule. Give each selected candidate an allocation; retain skipped and failed queries. Keep geography, provider, depth and period comparable when comparing strategies. An expanded source set is a changed sampling frame, not a language-only improvement.

### Evidence questions differ by workflow

| Workflow | What to search and review | What counts as useful evidence |
|---|---|---|
| Market problems | Jobs, triggers, workarounds, satisfactory outcomes and non-adoption; independent topic discovery before known-company feedback | Located original customer experiences, with situation, outcome and speaker boundaries |
| Founder/operator | First customers, decisions, economics, retention, failed channels and early-stage constraints; named operators and local interview/podcast vocabulary | Attributed operator actions and dated outcomes; corroborate success claims and preserve survivorship bias |
| Competitors | Same-market providers, non-software substitutes, explicit cross-market analogs and named capability references | Verified entity/job/segment fit from source pages; supplier claims remain supplier claims |
| Communities | Local member vocabulary and source names, separately for forums, Facebook groups and pages | Verified source shape, audience, activity, locale and access route; indexed URLs alone are leads |

### Execution controls

- `collect.py`, `discover_market_problems.py`, and `research_founder_playbooks.py` support `--topic-keywords`, `--segment-keywords`, `--query-plan`, `--query-limit`, `--results-per-query`, `--max-http-requests`, and `--query-preview`. A preview performs no provider calls or project writes.
- Exact plans use `schemas/pain-query-plan.schema.json` (shared for customer, operator and competitor searches). Each query binds provider, locale, candidate ID, intent and seed origin. Run locales separately. Source-derived seeds require locators; use `previous_plan_digest` and revision notes for a follow-up round.
- Collector allocations apply per provider. Set `--limit` high enough for every selected exact query's allocation. HN, GitHub, autocomplete, YouTube, X and ScrapeCreators accept these plans. Query caps retain unexecuted rows. GitHub appends issue/date filters; X appends language/retweet filters. These transformations are retained in raw requests. YouTube allocations cap retained records including metadata/comments/transcripts; raw captures preserve the larger response. Optional ScrapeCreators comments have a separate cap, and requested entity/community captures retain their own controls.
- xAI receives one seed per prompt; its underlying searches are not observable exact-query execution. Its output remains model-mediated discovery requiring inspection of cited posts.
- Operator defaults use separate source-language situations in English, German, French, Spanish and Italian. For another language supply `--operator-keywords` and a local `--topic-keywords`, or an exact plan. Non-English automatic runs require local topic keywords. The default provider set is `serper_search,youtube,hn`; choose alternatives explicitly. Seed translation and query quality still need review.
- Competitor discovery supports the same exact plan format with mandatory `lane_scope` (`competitive_market`, `similar_company`, `capability_reference`) and `scope_value` on each row. Providers are `brave_search` and `firecrawl`. Its `--query-limit` applies per provider per lane; `--results-per-query` is search depth. Existing lane limits control the final shortlist, not which queries run. All discovered candidates and query outcomes remain in the raw audit. Firecrawl requests country, but does not enforce original language.
- Community discovery keeps its locale-specific seed/source-term controls and complete lane coverage check. Use `--query-preview` before execution. Optional `--query-review` binds analyst notes and source-derived vocabulary to the signed discovery audit; it does not authorize capture or replace direct source review.

Community review JSON shape:

```json
{
  "revision": "round-2",
  "previous_plan_digest": "<SHA256 from prior query_plan.json>",
  "review_notes": "Why these vocabulary/source changes address observed misses",
  "seeds": [{
    "locale": "<COUNTRY:language>",
    "seed": "<exact locale seed passed on the CLI>",
    "seed_origin": "source_derived",
    "seed_locators": ["<source URL plus post/paragraph locator>"]
  }]
}
```

### After a probe

Inspect relevant and rejected leads, actual outbound requests, failures, duplicates and source content. Separate query-result slots, unique URLs, original speakers and verified entities. Successful extraction may contain only navigation, supplier replies, AI summaries or copied quotations. Check original pages/API units before accepting an experience or operator account.

Refine with vocabulary and locations observed in reviewed sources. Keep the original run immutable, bind the new revision to its parent digest, and compare newly useful sources against rediscovered seed pages. Record negative and satisfactory outcomes. Refinement may worsen results; retain the failure rather than implying improvement from more queries. Stop when the decision has sufficient coverage or name the unresolved gap. None of these mechanics proves prevalence, demand, competitor strength or a successful business.

## Pain-query calibration: plan, challenge, probe, review, refine

Use before substantive customer-problem collection when vocabulary is inferred,
when researching a new locale/source, or when prior results are mostly suppliers,
editorial material, duplicates or unrelated posts. Reuse current reviewed work.
A poor search can reflect wording, source/index coverage, access, extraction or
classification; it does not establish absence of pain.

### 1. Plan what and where to search

Reuse the source plan from `plan_customer_feedback.py --topic-cells-json` and
the Customer-needs research method above. Identify relevant locale, job,
role, journey moment, source family and query-intent cells; avoid a compulsory
Cartesian grid. Begin with supplied experiences, reviewed prior evidence, or a
small neutral discovery pass when local vocabulary/source locations are unknown.

Brainstorm distinct query families covering triggers/decisions, consequences,
workarounds, successful outcomes, non-adoption and switching. Include indirect
accounts of a problem, not only explicit complaints. As a starting point, try
3–6 complementary families; expand when a decision-relevant perspective is missing.
For each family record:

- Source-language phrases, local acronyms, everyday/technical terms, spelling
  variants and relevant dialect/code-switching. Translation can propose terms;
  do not depend solely on untested literal translation. Preserve source-derived
  phrases with locators and label invented/translated wording as hypotheses.
- Where those episodes may appear and why: candidate local forums, communities,
  Q&A, public comments, or verified entity-feedback sources. Check audience and
  access rather than treating a platform name or a `forum` suffix as coverage.
- A mixture of audience-anchored and unanchored searches. Source review establishes
  target membership; people need not name their audience category in every post.
- Expected useful evidence and likely false positives. Keep shared baselines
  separate from candidate comparisons, and keep topic/entity sampling frames separate.

Use existing community discovery and capture review where applicable. Indexed
community candidates are not automatically authorized or accessible capture targets.
Web indexes are retrieval routes; two indexes finding one post are one observation.

Treat geography, search language, original post language and displayed translation
as separate fields. A translated search result is not a new source-language
experience. Retrieve the original post where possible; retain useful local
acronyms/code-switching, and label unsupported-language or translation-only
coverage. Do not compare languages as if they necessarily sampled the same people.

Check ambiguity before adding emotion words: a local term may name several jobs
or industries. Use a concrete product, event or action to disambiguate it. Split
combined category phrases into separate customer episodes. For the actual first
scheduled queries, check distinct situations and sources, not only different
intent suffixes on the same broad topic. Generic positive wording can retrieve
supplier testimonials; seek successful episodes in discussion sources as well.

### 2. Review the plan before collection

For substantive studies, use a fresh independent reviewer when delegation is
available and authorized. Give it the research question, roles/locales, sampling
cells, query families, source candidates and known evidence, without telling it
which formulation should win. Ask for specific omissions and edits:

- Is local wording plausible? Are concepts and journey moments missing?
- Are audience constraints too restrictive, or phrases overly supplier-oriented?
- Does the plan cover consequences, workarounds and successful/contrary cases?
- Are source locations plausible for the audience, and provider syntax supported?
- Are apparently diverse candidates only paraphrases of one idea?

Resolve concrete defects, retain exploratory searches where uncertainty remains,
and record rationale. If delegation is unavailable, perform a separate inline
review and label it honestly; do not claim independence. Review checks plan quality,
not expected search performance. It does not require new user approval.

### 3. Execute exact, comparable probes

Use `collect.py --query-plan` for attributable calibration. The input follows
`schemas/pain-query-plan.schema.json`. Its exact queries replace generated queries;
no topic baseline, automatic suffix or audience term is added. Each row specifies
one provider. The selected provider set must exactly match the file, and all rows
must match explicit `--geo`/`--language`; run different locales separately.

Illustrative French relocation probe, not verified customer wording or a required
provider choice:

```json
{
  "schema_version": 1,
  "revision": "round-1",
  "review": {"mode": "inline", "notes": "Illustration only; complete substantive review for the actual study."},
  "queries": [
    {"query_id": "q1", "candidate_id": "deposit-delay", "query": "caution non rendue déménagement forum", "provider": "serper_search", "locale": "FR:fr", "intent": "pain", "source_family": "local_forums", "seed_origin": "generated"},
    {"query_id": "q2", "candidate_id": "successful-resolution", "query": "récupéré ma caution après déménagement", "provider": "serper_search", "locale": "FR:fr", "intent": "successful_alternative", "source_family": "local_forums", "seed_origin": "generated"}
  ]
}
```

Link rows to existing sampling cells with optional `cell_id`; record source-derived
vocabulary with `seed_origin: source_derived` and nonempty `seed_locators`.
Use provider-specific query rows when syntax differs. Query IDs and provider/query
pairs must be unique. `review` is analyst notes, not authenticated approval.
`source_family` and `intent` describe the planned search; inspect returned sources
before assigning their actual type, audience or experience.

Preview first (offline, no credentials, collection or workspace writes):

```bash
python3 scripts/evidence_scout/collect.py \
  --topic '<research question>' --customer-segment '<target segment>' \
  --query-plan '<query-plan.json>' --geo FR --language fr \
  --providers serper_search --query-limit 2 --results-per-query 5 --limit 10 \
  --query-preview
```

To collect, use the same arguments without `--query-preview`, add the actual
`--workspace`/`--case` or a unique `--out-dir`, and choose an appropriate `--days`
for recency-aware providers. Keep each round's artifacts separate.

Explicit plans support Reddit, Brave, Serper, Firecrawl, HN, GitHub, autocomplete,
YouTube, X, xAI discovery and ScrapeCreators keyword searches. Other routes retain
their existing workflows. xAI receives a seed prompt, not a verifiable exact
underlying search. See Query design and refinement above for
provider allocation units and wrapper controls.
`--query-limit` selects the first N declared rows **per provider**. Every selected
query gets `--results-per-query` (1–10). `--limit` remains the per-provider record
cap and must cover all selected allowances; insufficient allocations fail before
collection. These bounds are reproducible sample allocations, not spending caps.

Compare candidates within the same provider/locale/source lane at the same depth
and relevant time window. Then compare source strategies separately. Do not pool
baseline results into each candidate's score. A query-limit omission or failed
provider is untested coverage, not a zero-quality candidate.

For a before/after test, freeze the current automatic schedule as well as any
historical baseline before inspecting results. Replay them with the same provider,
locale and depth; record actual search times. Separate the effects of wording,
source restrictions, extraction routes and classification changes. A later
source-derived round is a refinement check, not an independent causal benchmark.

The preview and saved `query_plan.json` contain provider schedules, allocations,
locale limitations, the input plan and its digest. `summary.json` contains the
actual per-provider `query_ledger`: query/candidate IDs, attempted/status,
returned/inspected counts, result URLs and record IDs. Evidence memberships retain
multiple discovery paths for a repeated record. `new_record_count` is marginal
within that provider's execution order, not independent-person or customer count.
The run snapshot is an output wrapper; pass its `input_plan` as a new input only
after intentional revision, not the entire wrapper.

For generated full-pass searches, use short `--topic-keywords`, review the mixed
anchored/unanchored schedule, and inspect any unsupported-language warning. Generic
preview explicitly lists providers outside its scheduling support. Exact plans
can include a short or long expression deliberately; the collector never rewrites it.

### 4. Review source evidence before scoring

Hydrate promising snippets, inspect complete pages and speakers, and apply the
existing experience ledger and source-review process. Classify reviewed firsthand
target/adjacent experiences, supplier/editorial material, unrelated results and
unresolved fit. Check a sample of rejected items for multilingual false negatives.
Automated relevance and `user_pain` labels are provisional.

Audit rejected leads in every language: a specialist keyword list may recognize
one language or acronym spelling and silently discard another. Preserve original
labels, record corrections with the shared source-review contract, and test the
exact failure before changing the classifier. Missing vocabulary is not negative
customer evidence. Retrieval quality and classifier retention are separate scores.

Check that extraction retained author/post boundaries and substantive text. HTTP
success can return only navigation; a forum can contain supplier replies, quoted
other speakers, or an AI-generated summary. None is automatically firsthand voice.
Use an available source API if the extractor explicitly does not support that site;
keep each attempt and the final capture provenance. Do not repeatedly retry a known
unsupported route. Thread pagination and API comment subsets remain coverage limits.

In the research plan's calibration notes record per candidate:

- Planned, attempted, fetched, unavailable, reviewed and unresolved counts.
- Reviewed target-experience precision with an explicit denominator; display
  unavailable/unreviewed counts separately rather than hiding them as negatives.
- Deduplicated useful experiences, marginal discoveries and source/role/journey
  coverage, including rare consequential episodes and contrary cases.
- Evidence IDs, source locators and existing review decisions supporting the counts.

Do not rank near-tied candidates confidently from five results or select solely
for precision. Retain complementary searches. Cross-provider duplicates and
unknown speaker independence require review; no automatic person deduplication
or convenience-sample prevalence estimate is justified.
Also report confirmed episode-bearing documents over all returned unique URLs as
a lower bound when review is partial, separately from precision among reviewed
documents. Retain query-result slots, unique documents and distinct speaker
episodes as different denominators. Old experiences may establish occurrence or
teach wording; record their dates and avoid treating them as current product facts.

### 5. Refine and validate on fresh searches

After each probe batch diagnose gaps: ambiguous wording, excessive constraints,
wrong source, unfamiliar local vocabulary, access failure, extraction loss,
unsupported locale, duplicates or unresolved target fit. Use reviewed material to
learn phrases, events, alternatives and source locations with their provenance.
Supplier pages may supply vocabulary but remain supplier context.

Write a revised query plan with stable candidate IDs for the same hypothesis,
new query IDs for changed searches, a new `revision`, `revision_notes`, and the
prior `input_plan_digest` as `previous_plan_digest`. Record dropped/retained/added
families and why in the research plan. Preserve original scope and contrary cases.
Try at least one evidence-driven revision when gaps remain; include fresh queries
or sources beyond those used to tune the plan. If no revision is useful, record why.
Record which reviewed documents are new to the study. Finding the seed thread again
does not validate the revised query; inspect off-topic returns and newly found
experiences, including successful and non-adoption cases. A refined query can be
worse or merely complementary; retain the evidence instead of declaring a winner.

Stop with an explicit reason: scoped questions sufficiently answered, mainly
repeat evidence, unresolved access, or a more informative next method. Do not
claim full-web recall or saturation. Carry the refined queries and source cells
into the broader topic-led pass; do not regenerate solely from the original brief.
Run the separate entity-led pass when verified alternatives exist. Reconcile
both with the source plan via `finalize_customer_feedback.py`; a provider selection
or successful capture cannot complete semantic feedback analysis.

Choose the next search from reviewed yield, not provider volume. Compare distinct
reviewed episodes and independent origins by customer role, locale, journey
moment, source family and outcome. Keep unknown independence visible. Search
snippets and creator/supplier material do not satisfy a customer-episode gap.
For each unresolved material question, state what observation would distinguish
the plausible explanations, then add a small linked refinement using customer
wording or an applicable source locator.

For partial manual review, the result row must name the exact population, selected
and sampled-out IDs, exclusion reasons, strata, review method, reviewed items,
rejection audit and limitations. Counts alone cannot establish a sample. Claims
may use only reviewed accepted items; sampled-out material cannot support
prevalence. Stop expanding a cell only when its decision-relevant questions have
reviewed support or explicit limits, applicable source families have honest
outcomes, and recent inspected sources add no new distinction. This is a bounded
conclusion for the declared scope, never proof of market saturation or absence of
pain.
