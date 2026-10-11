

# Keyword research and keyword-to-page map

Owner: marketing-strategy-builder. Consumers: brand-website-designer-builder and social-digital-marketing-planner.

1. Seed problem, workaround and search-intent terms from the brief and available idea-grill/evidence runs; add verified competitor names from the landscape. Do not make the user supply a keyword map when research can produce one. Ask for missing business facts or choices only when they change the strategy. Do not turn segment prose into a keyword.
2. Expand with `python3 scripts/serper_fetch.py`, `collect.py --providers google_autocomplete`, and Google Trends as a relative-demand proxy. Record query, locale, date and raw results under `marketing/keywords/raw/`.
3. Classify intent, funnel stage, SERP shape and ranking source types. Volume values are provider estimates.
4. Cluster terms and assign one primary page per cluster with page type and conversion bridge.
5. Output `marketing/keywords/keyword-map.json` rows with cluster, primary/secondary terms, intent, stage, SERP notes, page type, target URL, priority, evidence refs and checked_at.
6. Website builds from the map; search ads use transactional clusters only.

## Versioned page decisions

Use `schemas/keyword-map.schema.json` and `python3 scripts/marketing/keyword_map.py <map.json> --base <marketing-root>`. Keep `keywords/keyword-map.json` inside Marketing. Each row retains real query/locale/date source bindings, intent, existing/proposed URL, retain/improve/create/consolidate/retire decision, missing information, original contribution, internal links, conversion bridge and priority rationale. Improve a sufficient existing page before creating another. Conflicting primary assignments within one locale require an explained reviewed exception. Estimated volume needs provider and date; unknown stays null. Consolidation/retirement records intentional redirect treatment without applying it.

Publish the map through the existing Marketing transaction; evidence is validated from staged or persisted bytes. Legacy maps need reviewed conversion before this contract can certify use. Public-resource briefs optionally extend content briefs with audience/job, utility, source bindings, original-versus-compiled contribution, limitations, public-use suitability, destination and maintenance responsibility. Consume only current reviewed handoffs. Promotion is a separately selected task; a finished internal study does not authorize publishing its contents.
