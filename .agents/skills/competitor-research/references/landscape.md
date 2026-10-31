# Landscape mode (route `competitive-landscape`)

Coordinates scout and teardown work into a three-lane landscape. Do not treat all similar-looking entities as competitors. Branding and website handoffs are optional and never make research a prerequisite.

## Three lanes (the landscape checklist)

Run each lane independently:

- [ ] `competitive_market`: same customer job, buyer/segment and market; informs threats, table stakes and positioning.
- [ ] `similar_company`: same or similar service/model with a documented segment, demographic or geography mismatch; supports scoped commercial-precedent and transferability findings when purchases, repeat value or economics are reviewed. Existence alone stays existence-only.
- [ ] `capability_reference`: narrow website, brand, offer, social, YouTube, onboarding or trust reference; informs a named learning purpose only.

Treat discovery lane observations as provenance, not classification. Verify official service evidence before invoking the canonical classifier. Produce competitive conclusions only from verified first-lane entities.

## Stage gates

1. Brief and scope agreed before any retrieval.
2. Bounded discovery per lane; stop when two independent query formulations add no new candidate worth verification.
3. Official service evidence verified before classification.
4. Commercial and social analysis only for shortlisted entities.
5. Synthesis only from schema-validated entities; stop when `quality-gate.json` fails and report the missing evidence instead of filling templates.

## 1. Brief and scope

Before any retrieval, inspect existing `projects/*/market_research/manifest.json` and offer continuation of the matching workspace according to `references/workspace-lifecycle.md`. Capture service/offer, customer job, buyer, target segment, geography, price tier, known entities, analogous markets and capability questions. Ask one question only if a missing field would change lane assignment. Keep branding independent.

## 2. Classification contract

Score offer/job, target segment, buyer, geography, price tier and purchase substitutability independently as `strong`, `partial`, `none` or `unknown`. A direct competitor needs explicit service evidence plus strong job, segment, buyer and substitutability fit. Similar companies must show meaningful service/model overlap and an explicit segment, demographic or geography mismatch. A reference has a named capability purpose. Search-query overlap is never sufficient.

Keep `primary_lane` separate from `inspiration_roles`: an entity may be a direct competitor and a website reference. Keep source-page type separate from entity type. Blogs, directories, agencies, affiliates and review pages remain exclusions unless first-party evidence shows the entity actually sells the offer.

## 3. Bounded discovery

Run independent bounded query sets for each lane. Default to five competitive entities, three similar companies and three capability references. Preserve `lane_scope` and `scope_value` on every search observation. Domain deduplication may merge observations but must never select the final lane. Stop when two independent query formulations add no new candidate worth verification. Reuse fresh dated evidence; deep-enrich only shortlisted entities.

Use the existing discovery worker, passing Lane B/C scopes explicitly when known:

```bash
python3 scripts/evidence_scout/discover_competitors.py --topic "<service/job>" --customer-segment "<segment>" --analog-market "<other market>" --reference-capability "website" --reference-capability "YouTube" --limit 20
python3 scripts/evidence_scout/analyze_competitor_marketing.py --topic "<service/job>" --competitors-json "<run>/competitors.json" --deep --out-dir "<run>/marketing"
python3 scripts/evidence_scout/collect_social_presence.py --entities-json "<run>/competitors.json" --marketing-json "<run>/marketing/marketing_analysis.json" --observations-json "<approved-provider-observations.json>" --out "<run>/social-observations.json"
python3 scripts/evidence_scout/build_entity_landscape.py --competitors-json "<run>/competitors.json" --discovery-summary-json "<run>/summary.json" --marketing-json "<run>/marketing/marketing_analysis.json" --social-json "<run>/social-observations.json" --service "<service>" --job "<job>" --target-segment "<segment>" --geography "<market>" --out "<run>/entity-landscape.json"
python3 scripts/evidence_scout/build_landscape_artifacts.py --entities-json "<run>/entity-landscape.json" --marketing-json "<run>/marketing/marketing_analysis.json" --out-dir "<run>/landscape"
```

Omit `--observations-json` when no approved social sampling has been collected; the quality gate must then remain blocked rather than implying that linked profiles were checked.

## 4. Commercial and social analysis

For shortlisted entities record every service/package, target segment, exact currency/period/conditions or `not_found`, sales motion, CTA, proof and trust reducers. Discover official public profiles across relevant platforms. For each platform record canonical URL, status (`verified_active`, `verified_inactive`, `unverified`, or `not_found_in_checked_sources`), role, sampled window, formats, cadence and CTA. Followers, views and likes are public proxies, never performance proof. Paid/social providers require the repository approval policy.

The marketing analyzer may discover profiles explicitly linked from an official site; these remain `unverified` until checked. Use an approved public provider or manual source check to sample profile activity and content roles, then pass those observations to `collect_social_presence.py`. The normalizer merges and standardizes evidence; it never claims live retrieval.

## 5. Synthesis

Build artifacts only from schema-validated entities. Lane A matrices include only `verification_status=verified`. Lane B/C records require an observed pattern and named inspiration role; otherwise mark the record `needs_enrichment`. `quality-gate.json` blocks handoff while any candidate is unresolved or any required inspiration record is incomplete. A positioning hypothesis needs a customer need and a plausible reason to choose the entrant, supported by scoped evidence and a test. A competitor gap is required only when the claim specifically asserts an unmet outcome; familiar products and cumulative service/distribution advantages may support entry. Apply repo-root `references/strategic-positioning.md` to assess success within the founder's horizon rather than equating existing supply with saturation.

Include the marketing analyzer's visibility, sales, service and retention assessment in the existing positioning narrative. Preserve strengths and unknowns alongside weaknesses. Generated matrices alone do not complete this analyst review. For foreign entrants use the operator-playbook workflow to verify early customer acquisition and outcome evidence; current scale or funding is not proof of first-two-year success.

## Content inventory handoff

For content/SEO planning, `analyze_competitor_marketing.py --content-inventory --landscape entity-landscape.json` inventories verified entities' content (rules in [teardown](teardown.md#content-inventory-contentseo-planning-input)). Lanes map to `entity_type`: `competitive_market` → `competitor`, `similar_company` → `similar_company`, `capability_reference` → `capability_reference`; uncertain or excluded entities are not inventoried. Supplier content is not customer need; similar companies abroad are inspiration for format and structure only; a topic nobody covers is a demand question, not whitespace.

## Required artifacts

`entity-landscape.json`, `competitive-market-matrix.md`, `offer-price-matrix.json`, `social-presence.json`, `similar-company-inspiration.md`, `capability-reference-library.md`, `positioning-hypotheses.md`, `quality-gate.json`, and optional `competitive-insight-handoff.json`.

## Quality Checklist

- [ ] Every entity has one primary lane, a reason, source URLs and an evidence quality.
- [ ] Lane A alone supports competitive-pressure, pricing and whitespace conclusions.
- [ ] Lane B/C records adaptation, transfer risk and do-not-copy boundaries.
- [ ] Prices are sourced and dated or explicitly `not_found`; social status is not inferred from silence.
- [ ] Public follower/view metrics are labelled proxies, not performance proof.
- [ ] Provider failures and coverage gaps are visible before synthesis.
- [ ] Branding remains an optional handoff and never a research prerequisite.

For independent market, analog and capability lanes, use one `competitor-researcher` per lane with exclusive output directories and source packets. The coordinator owns classification, deduplication and positioning decisions.

## Commercial precedents

For substantive chosen-idea validation select informative comparison markets, search in their language, inspect independent customers and failed outcomes, and assess local transfer conditions; funding remains a separate capital signal. Apply repo-root `references/research-data-and-precedents.md` for reviewed purchase, repeat-use, economics, funding, closure and failed-expansion observations. Preserve `commercial_precedent` on shortlisted entities; the existing landscape builder retains and renders this structure. Funding and existence alone do not prove commercial success or local demand. Use explicit native-language queries where needed.

## Output and handoff

Return the required artifacts above with coverage gaps and the next validation test. For a registered Business case, pass material competitor findings, limits and disagreements to the case-insights owner under repo-root `references/case-insights.md`; keep detailed landscape audits in their normal artifacts.
