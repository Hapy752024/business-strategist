# Competitive landscape workflow

## 1. Brief and scope

Before any retrieval, inspect existing `projects/research/topics/*/manifest.json` and offer continuation of the matching workspace according to `references/workspace-lifecycle.md`. Capture service/offer, customer job, buyer, target segment, geography, price tier, known entities, analogous markets and capability questions. Ask one question only if a missing field would change lane assignment. Keep branding independent.

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
