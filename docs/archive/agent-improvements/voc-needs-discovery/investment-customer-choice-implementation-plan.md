# Investment customer-choice research: implementation plan

Date: 2026-09-16. Status: implemented in `financial-analyst`; final bounded
correction pass and repository validation passed.
Target: `/mnt/c/coding/investments/financial-analyst`.
This document is held in business-strategist as a cross-repository review handoff.

## Objective and governing decisions

For B2C companies and the consumer side of hybrids, establish why customers buy
from this company, whether they like the company and its product/service, and
whether they prefer it to alternatives. Explain what sustains or weakens the
company's competitive position. This is not unmet-needs or product-requirements
discovery, and does not introduce startup-validation gates.

Customer sentiment and investment implications are independent dimensions.
"I dislike them but renewed because switching is difficult" is negative sentiment,
self-reported renewal and evidence of a retention barrier for that customer. It
can be positive evidence for the company's position without implying affection,
product superiority, population-wide lock-in, durable pricing power or a wide moat.
Assess the barrier's reach, economic effect and durability rather than cancelling
the positive retention evidence because sentiment is negative.

The customer decision hierarchy is a research OUTPUT. It describes the criteria,
thresholds, trade-offs and constraints influencing actual decisions, by material
segment and purchase occasion. Distinguish first purchase, repeat purchase,
renewal and exit: reasons to join need not be reasons to stay.

## 1. Research and synthesis workflow

1. Scope material products, retail segments, markets, periods and buyer/payer/user
   roles. Keep consumer, merchant and advertiser conclusions separate in hybrids.
2. Discover company and competitor customer inputs, plus category discussions
   that reveal alternatives and decision context. Reuse current evidence;
   category discovery is scoped to the investment questions, not a venture study.
3. Review actual customer passages. Capture positive, negative and mixed accounts,
   company-favouring and competitor-favouring choices, switchers, stayers and
   rejected purchases where available. Do not sample only low ratings.
4. Code reasons and trade-offs before consulting typical hierarchy templates.
   Preserve unexpected criteria and contradictory experiences.
5. Answer separately: why buy the category; why choose this company; brand
   affinity; experienced satisfaction; comparative preference; staying/switching
   behaviour and its mechanism. An unknown answer remains unknown.
6. Derive the hierarchy from decision evidence, not frequency of mentions or
   star-rating averages. Show supported orderings, ties, thresholds, constraints
   and unknown relationships. Do not invent three priorities to fill a template.
7. Reconcile the hierarchy with competitive mechanisms and business metrics.
   State supporting evidence, counter-evidence, scope, confidence and what would
   change each investment conclusion.

Source coverage: use relevant review sites, forums and social customer comments;
include Google/Trustpilot and app stores when appropriate. Record company/product,
market, language, period, rating/sort filters and collection gaps. Comparable
competitor samples support comparisons; unmatched samples support only bounded
observations. Storefront is not proof of reviewer residence; app complaints are
not automatically evidence about the whole company. Separate duplicate accounts,
supplier replies, sponsored testimonials, creator and investor commentary.
Unknown author relationship is not automatically verified customer voice.

## 2. Evidence contract: extend existing artifacts

Use one new structured sidecar, `deep_dives/customer-choice-evidence.json`,
referenced by the existing B2C demand-signals deep dive and Stage 1 hierarchy.
Do not create a separate skill, database, collection stack or scoring service.

Top-level sections:

- `scope` and `coverage`: material segments/entities/markets/periods, retrieval
  routes, filters, exclusions, unavailable cells and reasons.
- `observations`: stable ID; registered source ID; retained source locator and
  exact supporting passage; source/publication and retrieval dates where known;
  speaker relationship and review basis; entity/product/segment/occasion/phase;
  roles; sentiment target; stated reason or comparison; behaviour evidence type.
- `claims`: question answered; scoped conclusion; supporting and contradicting
  observation IDs; unknowns; confidence and its basis. Keep analyst interpretation
  separate from the passage. Self-report, intention and independently measured
  behaviour have distinct labels; company-reported metrics retain attribution.
- `position_mechanisms`: preference/value advantage, habit/default, availability,
  switching barriers or another evidence-supported mechanism; competitive effect
  (`supportive`, `adverse`, `mixed`, `unclear`); financial channel; evidence links;
  breadth; durability; counter-evidence; erosion triggers; metrics to corroborate.

One observation may support several dimensions without being counted as several
customers. Mechanism labels are extensible, not mutually exclusive. No composite
sentiment-to-moat score or automatic valuation adjustment.

Extend the existing hierarchy, rather than maintaining a competing second one:

- Add decision phase, evidence-backed priority relationships and constraint roles.
- Add per-entry `basis`: `observed`, `inferred` or `prior`; record observation IDs
  for customer evidence and separate prior references for contextual assumptions.
- Add hierarchy `origin`: `evidence_derived`, `hybrid`, `prior_only` or `unresolved`.
- Preserve existing segment, threshold, company delivery, alternatives, trade-off,
  surplus, source, moat, financial and monitoring fields, allowing explicit unknowns.
- Require a rationale for priority ordering: explicit customer trade-offs,
  contextual comparisons or triangulated behaviour. Mention counts alone fail.

## 3. Typical hierarchies: provisional fallback, not predetermined answer

Maintain a small, versioned reference of contextual candidate hierarchies. Each
includes category, occasion, phase, source/basis, applicability, limitations and
disconfirming observations. If no defensible typical order exists, provide an
unranked checklist instead. No universal income/age/visibility ranking.

Use only after the scoped search is completed or blocked with a recorded coverage
gap. Select by closest decision context, not a company-name match. Explain why it
applies and retain customer evidence that changes it. Mixed evidence does not have
to produce one forced global order: split material contexts or leave ties.

Render fallback rows visibly as "Provisional typical hierarchy — not established
for this company." Prior references never satisfy customer-evidence requirements.
Prior-only or materially mixed unsupported conclusions remain partial and cannot
support an unqualified empirical Stage 1 Pass. Existing conditional-stage handling
remains available: do not block all useful analysis merely because VoC is scarce.
Research completion and strength of evidence are reported separately.

## 4. Investment interpretation rules

| Finding | Supported interpretation | Not established by this finding alone |
|---|---|---|
| Dislikes company; renewed because migration is difficult | Retention barrier; potentially investor-positive | Affection, superiority, company-wide moat or pricing power |
| Likes product but moved to a cheaper rival | Positive satisfaction; adverse realised retention in this case | Strong pricing power or durable loyalty |
| Chose company over a named rival for better reliability | Comparative preference on reliability in that context | Universal preference or market-share leadership |
| Stayed after a price rise because leaving was costly | Barrier and price-response evidence for this customer | Unlimited price tolerance or permanent protection |

Assess barriers by nature, magnitude and persistence: migration effort, lost data,
learning, integration/ecosystem, contract penalties, habit or limited alternatives
have different durations. Investigate competitor migration assistance, portability,
contract expiry or changing alternatives when relevant; this is economic durability
analysis, not an added compliance review.

Triangulate with reported retention/churn, repeat purchases, units/share, realised
prices, discounting and relevant acquisition/service costs. Profitable retention is
not established by retention alone; discount-supported renewal may have a different
economic implication. Missing corroboration reduces conclusion strength, not the
validity of the individual customer account. Do not turn review frequencies into
population estimates or treat correlation as proof of the proposed mechanism.

Remove automatic "not top three = downgrade moat" logic. A barrier can constrain
choice without being a desired feature or frequently mentioned purchase priority.
Judge protection through effects on customer decisions and defensibility instead.

## 5. Concrete implementation sequence and files

### A. Method and contract first

- Update `value-business-quality/references/customer-decision-hierarchy.md` and
  `references/workflow.md`: evidence-first hierarchy, partial orders, constraints,
  positive friction interpretation, remove mandatory top-three downgrade and
  categorical B2C visibility/demographic assumptions.
- Add one shared `references/customer-choice-evidence.md` under that skill,
  including the compact fallback catalogue; avoid unnecessary reference sprawl.
- Update `value-b2c-demand-signals/SKILL.md` and its workflow to own evidence
  collection and reviewed synthesis. Business quality consumes it and reconciles
  the hierarchy. Keep existing demand-proxy work but label it separately from VoC.

### B. Implement the minimal structured contract and validation

- Add a schema and substantive validator for the sidecar; validate source and
  observation references, required conclusions or explicit gaps, claim attribution,
  prior/evidence separation and material coverage accounting.
- Replace line-count/keyword acceptance in `scripts/validate_b2c_demand_signals.py`
  with sidecar/content validation for newly versioned runs. Validate the explicitly
  linked current artifact, not the first matching historical deep dive.
- Extend `.agents/skills/value-research-log/scripts/stage_research_packet.py`,
  `schemas/stage-research-packet.schema.json` and
  `scripts/validate_customer_decision_hierarchy.py`. Remove the artificial minimum
  of three preferences for the new B2C contract; allow supported partial orders.
- Retain registry reconciliation and existing customer-type/manifest checks.
  Structural validation does not certify semantic truth: reviewed interpretation
  and the evaluation below remain necessary.

### C. Wire the actual workflow and downstream consumers

- Inspect canonical `company-analysis/references/stage-matrix.json` and
  `stage-contracts.json`: ensure the B2C evidence pass precedes final hierarchy
  synthesis/Stage 1 close. Reconcile existing stage demand-signal uses rather than
  requiring duplicated collection at each stage; regenerate derived workflow docs.
- Update research-log `create_company_page.py` / `update_company_page.py` and
  affected templates: display observed hierarchy versus fallback, sentiment versus
  competitive mechanism, evidence scope and open uncertainties.
- Carry these distinctions into Stage 2 marketing/strategy and later financial
  assumptions. No silent confidence upgrade or automatic valuation premium.
- Version the new contract. Preserve old artifacts as legacy/unassessed; do not
  silently reclassify them as validated or migrate live company work. Pure-B2B
  workflows stay unchanged; hybrid consumers receive the B2C contract separately.
- Reconcile existing dirty target files carefully; no unrelated cleanup.

### D. Test and independently review substance

Extend `tests/test_customer_decision_hierarchy.py`; add focused sidecar/demand
validation tests and stage-close/company-page integration tests. Required cases:

1. Negative sentiment plus friction-driven renewal retains a supportive mechanism.
2. Same account cannot establish affection, superiority or broad pricing power.
3. Positive satisfaction plus switching remains adverse retention evidence.
4. Category demand cannot stand in for company choice; five stars is not preference.
5. Supplier praise cannot become customer voice; unsupported claim links fail.
6. Competitor-favouring and contrary evidence survives synthesis.
7. Different markets/periods/products cannot support an unqualified comparison.
8. A hierarchy with two supported criteria is valid; frequency alone cannot rank it.
9. Prior-only renders visibly and cannot satisfy empirical-completeness checks.
10. Context-specific evidence can revise a prior; unresolved order stays unresolved.
11. Acquisition versus renewal and buyer/payer/user conclusions stay separate.
12. Partial/no evidence and provider failures remain gaps, not negative demand.
13. Company-page and downstream outputs preserve evidence basis and uncertainty.
14. Legacy compatibility and existing pure-B2B behaviour are not regressed.

Also perform a bounded live evaluation across contrasting decision contexts (repeat
purchase, subscription/renewal and ecosystem purchase). Independently review held-out
customer passages and derived conclusions for attribution, motive, comparative
preference, hierarchy support and investment implication. Use the same evidence for
before/after comparison. Report concrete errors and unresolved source gaps; passing
synthetic tests is not proof of research quality or market representativeness.

Fresh adversarial review uses the owner's severity standard: blocker = unreviewed
source admitted or supplier content promoted to customer voice; significant =
materially distorted coverage, hierarchy or investment conclusion; minor/out of
scope = theoretical state attacks, architecture polish or unrelated optimisations.
Resolve relevant findings and rerun changed-path tests before claiming completion.

## Completion boundary

Done means the changed workflow executes end to end, preserves the distinctions
above in its final investor-facing output, passes relevant regressions and receives
no unresolved blocker/significant content-quality findings in a fresh review.
It does not mean reviews establish a moat, all companies have enough evidence, or
an investment recommendation has been validated. No active company research was
migrated or reclassified by this implementation.

## Implementation result

Implemented the shared method, `customer-choice-evidence.json` schema and semantic
validator, current-artifact binding, evidence-derived hierarchy contract, provisional
fallback handling, scoped observation linkage, comparable competitor coverage,
qualified investor-facing projection, and downstream marketing handoff.

Fresh adversarial review initially found one blocker and four significant content
gaps. One bounded correction pass closed them: supplier/creator/unknown observations
cannot establish customer hierarchy rows; prior-backed rows cannot masquerade as a
complete evidence-derived hierarchy; observation scope and synthesis links are
checked; comparative claims require comparable collected coverage; and projection
preserves evidence basis, confidence, breadth, durability, counterevidence, erosion
triggers and scoped implications.

Verification on 2026-09-16: 48 relevant tests passed; `python3 scripts/validate.py
--ci` passed all 49 skills and repository process evals; JSON parsing and
`git diff --check` passed. The general skill-creator validator rejects this
repository's pre-existing `user_invocable` frontmatter extension, so repository CI
is the authoritative structural validator here. No cross-host live portability
claim is made.

## Research basis and access notes

- Fresh full-context reviewer `investment_plan_content_review`: zero blocker or
  significant findings; no adjustment requested. Reviewed target validators,
  packet handling and stage-contract references directly because an impact-radius
  tool was unavailable. This approves plan substance, not implementation quality.

- Paul Klemperer, *Markets with Consumer Switching Costs*, Quarterly Journal of
  Economics, May 1987 ([paper](https://www.czaj.org/pub/teaching/IO/Markets%20with%20Consumer%20Switching%20Costs.pdf)),
  retrieved 2026-09-16. The model distinguishes transaction, learning and contractual
  switching costs, and explains how protection of an installed base can coexist
  with intense competition for new customers. It also cautions that acquisition
  competition can dissipate the gains. This supports analysing retention mechanisms
  and net economics separately; it does not validate any particular company's moat.
- Repository inspection on 2026-09-16 verified the current mandatory three-preference
  validator, automatic top-three moat downgrade and line-count/keyword B2C acceptance.
- Firecrawl search succeeded after network-sandbox escalation. A second surfaced
  journal article returned HTTP 403 when opened and was not used as evidence.
