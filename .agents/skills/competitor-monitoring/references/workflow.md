---
name: competitor-monitoring
description: Set up or run recurring competitor monitoring for pricing pages, homepage messaging, changelogs, docs, careers pages, SERPs, ads, web traffic trends, local/physical-location presence, and app-store changes. Use this skill whenever the user asks to monitor, watch, track, alert on, schedule, or diff competitor changes over time, especially with Apify, Similarweb-style traffic actors, Google Maps actors, or Sonar.
---

# Competitor Monitoring Workflow

Use this skill for recurring change detection. Do not use Evidence Scout provider aliases for monitoring; Evidence Scout is for validation evidence, while this skill is for competitor watchlists, scheduled runs, diffs, and alerts.

## Operating Stance

Separate observed changes from interpretation. A pricing-page edit, SERP movement, traffic estimate shift, review-count change, new job cluster, or app metadata change is a signal about competitor behavior, not proof of customer demand.

Ask one focused setup question at a time when required. Prefer a small watchlist over broad scraping: 3-5 competitors and 2-5 high-signal URLs per competitor are easier to interpret and cheaper to run.

## Inputs To Collect

Before spending credits or setting schedules, identify:

- Competitors or domains to monitor.
- URLs per competitor: homepage, pricing, features, changelog, docs, careers, reviews, app-store pages, and primary domains for traffic estimates.
- Local/physical-location scope when relevant: country, city, radius, categories, Google Maps place URLs, chain names, property names, or store/restaurant/clinic locations.
- Market keywords for SERP monitoring.
- Cadence: daily for pricing/reviews, weekly for messaging, jobs, content, and SERPs unless the user asks otherwise.
- Alert destination if needed: report file, Slack/webhook, email, or manual review.

## Procedure

1. Confirm the monitoring target: competitors, URLs, app IDs, keywords, cadence, and alert destination.
2. Validate the required provider credentials before running or scheduling paid calls.
3. Run a small smoke test and inspect the output schema.
4. Normalize rows with stable keys, timestamps, source URLs, provider run IDs, and input hashes.
5. Diff current output against the prior snapshot.
6. Write a concise report that separates observed changes from interpretation.

## Provider Choice

Use Apify when the source is a public website, SERP, social/profile page, directory, e-commerce page, careers page, or review page and an Actor/schema has been chosen.

Use `tri_angle/fast-similarweb-scraper` only for web-first competitor context:

- Rolling monthly visits.
- Bounce rate, pages per visit, time on site.
- Traffic sources.
- Top countries and top keywords.
- Global/category/country rank.

Treat Similarweb-style traffic data as estimated share-of-attention context. Do not infer churn from one traffic decline; require repeated movement, corroborating signals, and a plausible business explanation.

Use `compass/crawler-google-places` only for local, physical-location, retail, restaurant, clinic, hospitality, property, or REIT-style markets:

- Location count and coverage.
- Ratings, review counts, and review distribution.
- Popular times/live occupancy when available.
- Closure status, opening hours, price bracket, category, amenities.
- Review text/tags for local service gaps.

Do not run Google Maps enrichment for normal SaaS, pure digital products, or broad B2B ideas unless physical presence is part of the market.

Use Sonar when monitoring mobile app-store competitors:

- App rank/keyword movement.
- App reviews.
- Metadata, screenshot, release, price/IAP, or category changes.
- Revenue estimates as weak monetization context.

Use Firecrawl for one-off page snapshots or when the user does not need scheduled Apify Actor runs.

Do not use stock-trading sentiment actors such as Reddit ticker sentiment or Stocktwits sentiment for general market research. They are only relevant when the research question is explicitly about active traders, investor communities, trading products, or public-market narrative monitoring.

## Apify Workflow

For public website monitoring:

1. Choose the smallest suitable Actor first. Common defaults:
   - `apify/website-content-crawler` for homepage, pricing, feature, docs, changelog, and careers page text.
   - `apify/google-search-scraper` for keyword SERP and paid-result monitoring.
   - `tri_angle/fast-similarweb-scraper` for estimated web traffic and engagement trends on known competitor domains.
   - `compass/crawler-google-places` for local/physical-location market coverage, ratings, reviews, and popular-times context.
   - A specific review/social/e-commerce Actor only after checking its input and output schema.
2. Run a smoke test before scheduling.
3. Save raw dataset rows and a normalized snapshot with stable keys:
   - URL for pages.
   - `(competitor, keyword, result_url)` for SERPs.
   - Job ID or canonical job URL for roles.
   - Product URL/SKU for e-commerce.
4. Add `scrapedAt`, source URL, actor ID, run ID, and input hash to each normalized row.
5. Diff against the previous snapshot. Ignore nav, cookie banners, timestamps, and tracking parameters.
6. Report only material changes, with source links and the previous/current evidence.

## Similarweb Traffic Workflow

Use this workflow when the user has known competitor domains and wants web traction context.

1. Validate `APIFY_TOKEN` first:

```bash
python3 scripts/validate_apis/validate_apify.py
```

2. Run a smoke test on 2-3 known domains before scheduling.
3. Normalize these fields when present:
   - `name`, `url`, `category`, `globalRank`, `countryRank`, `categoryRank`.
   - `engagements.visits`, `engagements.bounceRate`, `engagements.pagePerVisit`, `engagements.timeOnSite`.
   - `trafficSources`, `topKeywords`, `topCountries`, `estimatedMonthlyVisits`.
   - `snapshotDate`, `scrapedAt`.
4. Compare only like-for-like monthly snapshots. Do not compare a fresh scrape for one domain against stale scrape dates for another.
5. Flag material movement only when it is repeated or large enough to matter, for example sustained visits decline, traffic-source mix shift, or branded-keyword loss.
6. Interpret carefully:
   - Traffic estimates are not customer counts.
   - Bounce rate is not churn.
   - A decline can come from seasonality, SEO changes, campaign spend, tracking changes, or Similarweb estimate noise.

## Google Maps Local Market Workflow

Use this workflow only when physical presence matters.

1. Validate `APIFY_TOKEN` first:

```bash
python3 scripts/validate_apis/validate_apify.py
```

2. Ask the user to narrow geography before spending credits: city/region, radius, categories, named chains, or direct place URLs.
3. Prefer direct place URLs or a small set of distinct search terms for smoke tests. Avoid long overlapping category lists that inflate cost and false positives.
4. Normalize these fields when present:
   - `title`, `categoryName`, `categories`, `address`, `city`, `state`, `countryCode`, `location`.
   - `totalScore`, `reviewsCount`, `reviewsDistribution`, `reviewsTags`, `price`.
   - `popularTimes` or live occupancy fields when present.
   - `permanentlyClosed`, `temporarilyClosed`, `openingHours`.
   - Review rows with `text`, `stars`, `publishedAtDate`, `likesCount`, `reviewUrl`.
5. Use review text and review tags as weak-to-medium local pain evidence only when complaints repeat across independent locations.
6. Treat review count and rating as market/context signals, not demand proof.

## Sonar Workflow

For app competitors:

1. Validate `SONAR_API_KEY` with:

```bash
python3 scripts/validate_apis/validate_sonar.py
```

2. Use stateless endpoints for one-off checks when app IDs are known:
   - Reviews for complaint/praise drift.
   - Revenue estimates for weak monetization context.
   - Keyword metrics/suggestions for ASO demand context.
3. Use org-scoped tracking and alerts only when the user explicitly wants ongoing app monitoring and understands the plan/credit implications.
4. Preserve whether a result came from iOS or Android, country, app ID/package ID, and retrieval date.

## Output

Write monitoring outputs under:

```text
research/evidence-scout/competitor-monitoring/<timestamp-topic>/
```

Recommended files:

- `watchlist.json`: competitors, URLs, app IDs, keywords, cadence, and provider choices.
- `raw/`: redacted provider responses.
- `snapshots/`: normalized current and prior snapshots.
- `changes.jsonl`: material changes with stable IDs.
- `report.md`: human-readable summary.

The report should include:

- Provider status and any missing credentials, quota, or permission issues.
- What changed, with source URLs and timestamps.
- Metric caveats, especially for estimated traffic, ratings, review volume, and occupancy.
- Why it might matter.
- What is still unknown.
- Recommended next action: ignore, watch, teardown, interview, or pricing/positioning response.

## Guardrails

- Monitor public pages or sources the user is entitled to access.
- Do not bypass authentication, paywalls, or private communities unless the user provides legitimate access and explicitly asks for it.
- Do not scrape at aggressive rates. Prefer scheduled provider runs with reasonable cadence.
- Do not treat likes, views, rankings, or competitor activity as demand proof.
- Do not treat Similarweb traffic declines as churn without corroboration.
- Do not collect Google Maps lead/contact enrichment unless the user explicitly wants lead generation; it is usually unnecessary for market validation.
- Do not add finance sentiment actors to this workflow unless the research topic is explicitly trader/investor behavior.

## Quality Checklist

- Provider status and credential failures are visible in the report.
- Every material change has a source URL and timestamp.
- Diffs ignore boilerplate, navigation, cookie banners, timestamps, and tracking parameters.
- The watchlist is narrow enough to interpret and cheap enough to repeat.
- Traffic and local-place metrics are labeled as estimates/context where appropriate.
- Google Maps runs are limited to markets where physical presence matters.
- Interpretation does not claim customer demand from competitor activity alone.
