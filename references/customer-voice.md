# Customer voice from competitors and similar services

Apply when interpreting customer needs, motivations, praise or complaints about an existing service, or using them to refine a venture's segment, journey, risks or requirements. A narrow factual competitor lookup does not require a full study. Reuse current reviewed evidence when its entity, audience, product, geography and date fit; record gaps rather than manufacture coverage.

## Two complementary analyses, with topic-led discovery mandatory

Every substantive customer-input study runs **topic-led VOC discovery** first, even when competitors are known: search from the customer's job, trigger, problem, workaround and desired outcome without requiring an incumbent name.

Also run **entity-led customer-feedback analysis** once at least one competitor, substitute or similar company is verified; until then record it as `pending_entity_discovery`. It asks why, when and how identifiable customers use or reject the service, and what they praise, complain about, work around, repeat, switch or stop. It never replaces the topic-led pass.

Keep the two sampling frames and evidence counts separate; join them only in the U/R maps after source review. A complaint about an incumbent feature is not automatically an independent need; praise is not proof of the reason for buying.

Per verified entity, the source matrix covers independent review platforms, Google business ratings where a physical listing exists, the company's Facebook/Instagram comments, App Store and Google Play as separate lanes, external forums, and company-hosted testimonials as supplier context only. Missing handles, Place IDs or review profiles are discovery tasks, not evidence that a lane is inapplicable. Star averages, rating counts and supplier posts are context, not customer voice; separate the company's reply from the review author. Platform-ranked or API-limited subsets are convenience samples: report the retrieved denominator and never infer prevalence. Discover local review platforms at runtime for the entity's market; a platform's own authenticity claim is methodology context, not a truth label.

Commands (each script's `--help` is the procedure; the scripts enforce locale-scoped locators, denominators and reconciliation):

```bash
python3 scripts/evidence_scout/plan_customer_feedback.py --topic "<job/problem>" --customer-segment "<segment>" \
  --locale <CC>:<language> [--entities-json <verified-entities.json>] [--topic-cells-json <cells.json>] --out-dir <run>/customer-feedback
python3 scripts/evidence_scout/finalize_customer_feedback.py --plan <plan.json> --results <results.json> --out <coverage.json>
python3 scripts/evidence_scout/validate_customer_voc_synthesis.py --evidence <evidence.jsonl> --coverage <coverage.json> \
  --source-review <source-review.json> --customer-segment "<exact segment>" --synthesis <customer-voc-synthesis.json>
```

Missing or failed locales and platforms stay explicit gaps; useful scoped findings from accepted sources may still be synthesized. Zero accepted voice yields `insufficient_evidence`, not an empty successful study.

## Ownership and sequence

1. Identify and disambiguate the competitor, substitute or foreign analog first (domain, product, operating market). Reuse a verified shortlist or use competitor-scout; do not require a full landscape before listening to customers.
2. Evidence-scout owns customer-voice retrieval and source review. Competitor-marketing-analyzer owns supplier positioning, prices and promises, which cannot establish customer motives. Competitive-landscape-builder joins them without merging provenance.
3. With an unknown segment, explore broadly to form explicit segment/job hypotheses, then narrow. Keep adjacent/foreign voices labelled; never silently broaden the target to fill a quota.
4. Build the separate needs and requirements maps, then assess **each** mapped item before segment/journey/pain synthesis and before opportunity-risk-designer ranks assumptions. This is a research loop, not a new stage pass.

## Review the source and the claim separately

Preserve source URL, publication date (unknown if unavailable), retrieval date, source language, exact entity/product, geography, author context and evidence ID. Do not infer identity or collect private details. Distinguish quoted text from analyst paraphrase; link translations to the original wording.

Classify each voice as firsthand current/former customer, prospective user, observer/nonuser, supplier/affiliate or unresolved. Supplier-selected testimonials and paid promotion stay labelled even when they quote a customer. One person's posts, syndicated reviews and quoted replies are not independent customers. State what the author actually did, considered, praised or disliked, and separately what the analyst infers.

Record target/adjacent/unresolved segment fit with its reason. A foreign report can suggest a local interview hypothesis; it cannot validate the local target. Historical bugs, fees and eligibility rules need current verification. Source-access failures and zero collected records are coverage gaps, not evidence of no demand or no complaints.

Prospective-user and non-adopter evidence needs a concrete decision context and may support needs, barriers and evaluation requirements; it is never relabelled as product use, purchase or retention. Supplier, editorial and official-provider material cannot become customer voice.

## Type every reviewed statement (Mom Test)

Set `statement_type` on each accepted source review. Packets from `build_review_packet.py --summary <run>/summary.json` carry `statement_typing: true` and a Methodology section; carry it into the report so skipped providers read as coverage gaps.

| Type | Meaning | May support pain/demand? |
|---|---|---|
| `past_behaviour` | What they actually did or experienced | Yes |
| `commitment` | Time, reputation or money given up (a free meeting is not one) | Yes |
| `compliment` | Praise or encouragement | No |
| `fluff` | Generic or hypothetical talk ("I would definitely use that") | No |
| `feature_request` | A wished-for solution | No (lead for a follow-up question) |
| `unclassified` | Not yet judged or unclear | No |

The synthesis validator and claim-ledger checks reject pain/demand support from any other type.

## Separate the reasons, allow multiple motives

For each supported observation distinguish: why use the underlying category; why add this service instead of the default workaround; why this provider; and what sustains use or ends it (observed repeat payments differ from claimed future use and cohort retention). Code multiple motives where supported and **unknown** where not. Translated reward terms, praise for speed or an app install do not establish the mechanism, the need for an intermediary, willingness to pay or retention.

Search beyond the initial community: routine, dissatisfied/lapsed users, substitutes and non-adopters. Report scope and missing perspectives. Counts describe the reviewed sample only; never claim a motive is dominant or prevalent without a sampling basis and denominator.

## Separate customer needs from solution-use requirements

A **customer need** (U ID) is a desired outcome or problem that exists independently of our solution. A **solution-use requirement** (R ID) is what must be true for a solution to work acceptably. Keep separate maps; a shared episode does not make them one need. Preserve derivation where supported: `evidence ID → U need → R requirement → separate tests`. An R item may be a *supporting operational requirement, motivational root unknown*. Mark each item customer-stated, analyst-inferred or unknown, with source IDs. Do not invent deeper psychology to complete a map.

## Build both maps, then assess each item for our case

**Customer-needs map:** U ID · customer/trigger/source IDs · independent outcome · stated/inferred/unknown · current alternative and unmetness evidence · verdict (pursue/test/defer/not applicable/unknown) with reason.

**Solution-use requirements map:** R ID · use step/source IDs · required condition · linked U IDs or root unknown · stated/inferred/unknown · current performance · verdict (adopt/test/defer/not applicable/unknown) with reason.

Assess every distinct U and R item proportionately; a short insufficient-evidence assessment counts, silent omission does not. Do not double count a U item, its R derivatives or one person's posts. For U needs, keep occurrence, unmetness across alternatives, prevalence, target-country transfer and willingness to pay as separate claims. For R items, distinguish necessity, provider preference and differentiator, and a requirement from a user's suggested implementation; "adopt" selects a direction within authorized scope, not a feature build or stage pass.

Well-matched public accounts and checked alternatives can substantiate findings without interviews; interviews resolve remaining uncertainty. An unmet need or poorly served requirement does not by itself establish a commercial opportunity. Per company summarize who is identifiable, observed jobs, motives, praise, complaints, repeat/exit, target fit and evidence limits; leave unknowns unknown. For narrow follow-ups update affected items and reuse the rest.

## Hand off to pilot scope, smoke testing and GTM

Carry supported U/R IDs, evidence and confidence into the test/GTM brief; keep the handoff provisional where the strategy or pain gate has not passed. Deferred items record the evidence needed to reconsider them.

| Decision | Required handoff |
|---|---|
| Pilot scope | U outcomes investigated; R requirements included/excluded with reasons. Keep necessary operational R items even when their motivational root is unknown. |
| Smoke test | Lead with an evidenced U outcome; test R preferences separately. Qualified observable behavior with denominator, window and success/stop thresholds (experimental decisions, not market facts). A click, qualified signup, interview and price-bearing commitment are not interchangeable. |
| Recruitment | Screener on role, trigger and recent experience plus researched access channels from `interview-recruitment.md`. Offer no cash, vouchers, gifts or compensated panels unless the founder changes the preference; unpaid signups still require screening. |
| GTM | U evidence for segment, message and offer hypotheses; R evidence for promises, objections and delivery requirements. |
| Next uncertainty | The most consequential unresolved assumption and the cheapest suitable test. |

Preparing a test brief is distinct from launching it: publishing, outreach, advertising/distribution spend and live pilots keep their authorization requirements. A smoke page's purpose may be interview recruitment, message testing or demand testing: choose explicitly, and never present contact collection as paid demand validation.

## Customer-needs research method

Use for substantive market discovery, customer/problem validation and competitor feedback. Countries, languages, roles, companies and job vocabulary are runtime inputs.

### 1. Questions and coverage before themes

Record the decision, research questions, locales and plausible roles (user, buyer, payer, decision-maker, intermediary). Unknown roles are discovery questions, not reasons to demand a founder thesis. Extend topic cells with `--topic-cells-json` across routine journeys, painful episodes, workarounds, non-adoption, switching and exit; use translated customer vocabulary, not mechanically English phrases; explain the relevant cells rather than a full Cartesian grid. Record executed queries separately from proposed ones and widen after each batch. Provider success does not establish usable voice. Paid customer-evidence APIs are authorized without a monetary cap; failed credits require notification, fallback and a preserved gap, never an absence-of-demand conclusion.

Record sort order, filters, time window, pagination and provider subset limits per source; unknown is valid. Storefront or query locale is not the author's location or language.

### 2. Documents → speaker experiences → source review

Search snippets identify destinations; hydrate before accepting testimony. A full page is a document, not one customer's voice: split by speaker and episode with `build_experience_ledger.py` (it validates exact spans, not semantic accuracy, so inspect the whole document for missed voices). Count documents, experiences and independently attributable people separately. Write the digest-bound source-review sidecar against the experience file; `reviewed_voice.py` is shared by synthesis, claims and interview consumers. Explicit supplier attribution cannot be overridden.

### 3. Code and compare before making a needs map

Keep a versioned codebook (definition, include/exclude criteria, quoted instances, revision notes). Start from research questions, add unexpected codes, inspect outliers and compare context before combining themes. New studies use `customer-voc-synthesis.json` schema_version 2 (status `supported`, `scoped`, `provisional` or `insufficient_evidence`); the validator checks the fields. Structural validation checks provenance; an analyst must still judge whether each claim follows from the source. Retain excluded critical concepts with reasons.

For commercial, population or transfer claims use the claim ledger with `validate_synthesis.py --source-review <review.json> --customer-segment '<scope>'`. One located account establishes occurrence, not prevalence; mention counts cannot supply a missing sampling basis, alternatives assessment, price-bearing evidence or applicability basis.

#### Underserved and latent outcomes

Within U assessments distinguish dissatisfied users, nonconsumers blocked by cost/access/time/skill, overserved and adequately served customers. For a latent need retain observation → interpretation → competing explanation → disconfirming test. A workaround does not establish switching or payment intent. Never derive opportunity scores or prevalence from mention counts or invented ratings. `insufficient_evidence` differs from supported adequate service.

### 4. Partial findings and the next learning step

Execution, coverage and claim readiness are separate; report scoped findings without implying the unobserved market is covered. Match the method to the gap: missing sources → targeted discovery; trigger, motive, roles or handoffs → non-leading incident interviews; whether a solution works → observed task test; switching/payment → separately authorized behavioral test; current provider/legal facts → primary source. Interview selection keeps every reviewed material counterexample. No fixed number of confirmations validates a need. Stop with an explicit reason and keep study limits visible.

## Query design and refinement across research workflows

Use for substantive market, operator, competitor and community discovery; reuse current sources and reviewed vocabulary first.

1. Separate the research brief from short search phrases; record target country, search language, source language and audience independently.
2. Brainstorm local vocabulary and source locations, disambiguate terms that name unrelated industries, and do not translate one long English sentence and call it coverage.
3. Review candidates for distinct questions, native terminology, source fit and confirmation bias (an analyst review, not a permission gate; do not label inline review independent).
4. Preview the schedule with `--query-preview` (no provider calls or writes). Exact plans follow `schemas/pain-query-plan.schema.json`; run locales separately. Flags and allocation units: each collector's `--help`.

| Workflow | Useful evidence |
|---|---|
| Market problems | Located original customer experiences with situation, outcome and speaker boundaries |
| Founder/operator | Attributed operator actions and dated outcomes; corroborate success claims, preserve survivorship bias |
| Competitors | Verified entity/job/segment fit from source pages; supplier claims stay supplier claims |
| Communities | Verified source shape, audience, activity, locale and access route; indexed URLs alone are leads |

xAI output is model-mediated discovery requiring inspection of cited posts. After a probe, inspect relevant and rejected leads, failures and duplicates; separate result slots, unique URLs, original speakers and verified entities. Refine with reviewed vocabulary, bind the new revision to its parent digest, and retain failures. None of these mechanics proves prevalence, demand, competitor strength or a successful business.

### Judgment checks (no script enforces these)

- Sample favorable and unfavorable feedback and more than one time window; compare contrasting slices when an outage or platform ranking dominates. No equal star quotas, no representativeness claims.
- A forum post mentioning a brand is not automatically a usage report; do not infer authorship from sentiment or "I".
- HTTP success or extraction may contain only navigation, supplier replies, AI summaries or copied quotations; check original pages or API units.
- Include indirect accounts of a problem, not only explicit complaints. Generic positive wording retrieves supplier testimonials; seek successful episodes in discussion sources.
- A translated search result is not a new source-language experience; do not compare languages as if they sampled the same people.
- Independent plan review asks: is local wording plausible, are phrases supplier-oriented, are candidates paraphrases of one idea, is provider syntax supported?
- Do not pool baseline results into each candidate's score. Freeze before/after schedules before inspecting results; a later source-derived round is a refinement check, not an independent benchmark. Finding the seed thread again does not validate the revised query.
- Missing vocabulary is not negative customer evidence; test the exact failure before changing the classifier.
- Choose the next search from reviewed yield, not provider volume.
- Maintain competing hypotheses when evidence is insufficient and explain any changed recommendation.
- Preserve rare consequential cases and negative findings; a rare consequential need must not disappear under "convenience".
- Ask only a decision-changing founder question; use interviews for missing customer facts rather than asking the founder to invent them.

## Pain-query calibration: plan, challenge, probe, review, refine

Use before substantive collection when vocabulary is inferred, a locale/source is new, or prior results were mostly suppliers, duplicates or unrelated posts. A poor search can reflect wording, coverage, access, extraction or classification; it does not establish absence of pain.

1. **Plan:** 3–6 complementary query families covering triggers, consequences, workarounds, successful outcomes, non-adoption and switching. Per family record source-language phrases (source-derived with locators; translated wording labelled as hypotheses), likely source locations and why, a mix of audience-anchored and unanchored searches, and expected false positives. Two indexes finding one post are one observation.
2. **Review:** for substantive studies use a fresh independent reviewer when delegation is available, without telling it which formulation should win; otherwise label the inline review honestly. It checks plan quality and needs no user approval.
3. **Probe:** `collect.py --query-plan <plan.json> ... --query-preview`, then the same arguments without the flag plus a workspace or unique `--out-dir`. Compare candidates within the same provider/locale/depth; a skipped or failed query is untested coverage, not a zero-quality candidate. `summary.json` holds the per-provider query ledger.
4. **Review evidence before scoring:** hydrate, inspect speakers and boundaries, audit rejected leads in every language. Automated relevance and `user_pain` labels are provisional. Record planned, attempted, fetched, reviewed and unresolved counts with explicit denominators; keep unreviewed counts separate from negatives. Do not rank near-tied candidates from five results.
5. **Refine:** write a revised plan with a new `revision`, `revision_notes` and `previous_plan_digest`; include fresh queries beyond those used for tuning. A refined query can be worse; keep the evidence. Stop with an explicit reason; never claim full-web recall or saturation. Carry refined queries into the topic-led pass, run the entity-led pass where alternatives exist, and reconcile both with `finalize_customer_feedback.py`.

For partial manual review, name the population, sampled-out IDs, exclusion reasons, strata and method; claims use only reviewed accepted items.
