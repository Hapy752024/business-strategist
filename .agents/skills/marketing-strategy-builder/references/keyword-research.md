

# Keyword research and keyword-to-page map

Owner: marketing-strategy-builder. Consumers: brand-website-designer-builder and social-digital-marketing-planner.

1. Seed problem, workaround and search-intent terms from the brief and available idea-grill/evidence runs; add verified competitor names from the landscape. Do not make the user supply a keyword map when research can produce one. Ask for missing business facts or choices only when they change the strategy. Do not turn segment prose into a keyword.
2. Expand with `python3 scripts/serper_fetch.py`, `collect.py --providers google_autocomplete`, and Google Trends as a relative-demand proxy. Record query, locale, date and raw results under `marketing/keywords/raw/`.
3. Classify intent, funnel stage, SERP shape and ranking source types. Volume values are provider estimates.
4. Cluster terms and assign one primary page per cluster with page type and conversion bridge.
5. Output `marketing/keywords/keyword-map.json` rows with cluster, primary/secondary terms, intent, stage, SERP notes, page type, target URL, priority, evidence refs and checked_at.
6. Website builds from the map; search ads use transactional clusters only.
