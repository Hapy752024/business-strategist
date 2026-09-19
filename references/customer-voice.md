# Customer voice from competitors and similar services

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
`voc-research-method.md` for the version-2 research contract. After
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
