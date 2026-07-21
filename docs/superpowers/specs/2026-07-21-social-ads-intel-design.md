# Social & Ads Intelligence — Design Spec

**Date:** 2026-07-21
**Status:** Approved design, pending implementation plan
**Scope:** Improve social-media source access (Facebook groups/pages, Instagram) and add competitor digital-marketing (paid ads) intelligence to the evidence-scout toolset.

## 1. Background and Gap

Current state (verified 2026-07-21):

- `scripts/evidence_scout/collect.py` `collect_scrapecreators` calls only four endpoints: TikTok keyword search, Instagram reels search, Threads search, X user-tweets. **No Facebook endpoint is wired**, despite `config/source-capabilities.json` claiming Facebook coverage.
- `scripts/validate_apis/validate_meta.py` validates a Meta token against `/me` only; no collector uses the Meta Graph API.
- `competitor-marketing-analyzer` analyzes landing pages only. Its workflow mentions "Meta/TikTok ad libraries" as a clue "where available", but no tooling exists to fetch ad evidence.
- ScrapeCreators (`SCRAPE_CREATORS_API_KEY`) is validated and runtime-ok.

External options verified by web research (2026-07-21):

- **ScrapeCreators Facebook API** — 10 public-data endpoints: profile, profile posts (3 posts/call, cursor), profile reels (10/call), photos, events, post, post transcript, post comments, comment replies, group posts (3 posts/call, cursor). Public data only; no keyword search, no ad library. Credit-based. Sources: [scrapecreators.com/facebook-api](https://scrapecreators.com/facebook-api), [facebook-group-posts-api](https://scrapecreators.com/facebook-group-posts-api), [changelog](https://scrapecreators.com/changelog).
- **ScrapeCreators Instagram API** — profile, basic profile, profile posts, hashtag search, reels search (already wired), trending reels, post comments. Sources: [scrapecreators.com/instagram-api](https://scrapecreators.com/instagram-api), [instagram-hashtag-api](https://scrapecreators.com/instagram-hashtag-api).
- **Meta Ad Library API** (official, free) — `ads_archive` Graph endpoint. Requires Meta developer app + government-ID identity verification by the user; token expires ~every 60 days (refresh flow required). **Commercial ads only for EU/UK audiences** (DSA transparency, ~1-year retention); outside EU/UK only political/social-issue ads. Coarse spend/impression ranges, no engagement metrics, ~200 Graph calls/hour. Sources: [adlibrary.com API limitations](https://adlibrary.com/posts/meta-ad-library-api-limitations), [hyperfx developer guide](https://www.hyperfx.ai/blog/meta-ad-library-api-scraper-guide).
- **Apify Facebook Ad Library actor** — paid per result, no ID verification, works globally. Suitable as fallback for non-EU/UK markets.

User decisions (2026-07-21):

1. All four goals in scope: competitor ad intelligence, FB group pain evidence, FB/IG page & profile intel, IG audience/hashtag research.
2. Ad intelligence: official Meta Ad Library API primary + Apify paid fallback. User will perform the one-time Meta ID verification.
3. Architecture approach A: extend `collect.py` for social; new `collect_ads.py` for ad intel.

## 2. Architecture

Two deterministic collectors, split by workflow shape:

- **Pain/audience evidence** (topic-keyed) → extend `collect_scrapecreators` in `scripts/evidence_scout/collect.py`. Feeds `evidence-scout`, `market-problem-discovery`, `social-media-idea-validator`.
- **Ad intelligence** (competitor-keyed) → new `scripts/evidence_scout/collect_ads.py`. Feeds `competitor-marketing-analyzer` (and later `competitor-monitoring`).

Rationale: ad intel needs competitor page IDs, country, and keyword parameters that do not fit `collect.py`'s topic/segment/problem-keyword argument shape; the repo already splits `discover_competitors.py` and `analyze_competitor_marketing.py` out of `collect.py` for the same reason. `collect.py` is ~3,100 lines and must not absorb a second workflow shape.

Rejected alternatives: everything in `collect.py` (argument-shape mismatch, file size); MCP servers instead of scripts (project policy prefers CLI/scripts; MCP responses bypass redaction/normalization into `evidence.jsonl` and make credit spend less auditable).

## 3. Component: ScrapeCreators FB/IG expansion (`collect.py`)

New optional flags, active only under `--providers scrapecreators` (which stays `approval_required: true` and is never part of `default`):

| Flag | Endpoint (verified live 2026-07-21) | Notes |
|---|---|---|
| `--fb-groups id_or_url,...` | `GET /v1/facebook/group/posts` | Endpoint works; 3 posts/call, `cursor` pagination, up to `--fb-max-posts` (default 12, hard cap 60). **Public groups only** — a 200 with 0 posts is ambiguous (private or empty); report as "no accessible public posts", never "no posts exist" |
| `--fb-pages id_or_url,...` | `GET /v1/facebook/profile/posts` + `/profile/reels` | Verified working (3 posts + cursor returned for a public page). Page posts 3/call (same cap), reels 10/call |
| `--ig-handles handle,...` | `GET /v1/instagram/profile` + `GET /v2/instagram/user/posts` | Verified working. Posts live under `profile_grid_items` with `profile_grid_items_cursor` — **not** the `posts`/`data` keys the current `list_candidates` heuristic expects; needs a dedicated parser |
| `--ig-hashtags tag,...` | `GET /v1/instagram/search/hashtag` | Verified working: 10 posts/call + `cursor`, captions and reel URLs returned |
| `--social-comments` | FB post comments, `GET /v2/instagram/post/comments` | Opt-in; fetches comments on top-N collected posts (N = `--comments-max`, default 5) |

Observed cost: 1 credit per call (account showed 100 free credits; live tests consumed ~6).

Normalization: **reuse the existing `facebook` and `instagram` values** already present in `schemas/evidence-record.schema.json`'s `source` enum — do not add new enum values. Granularity goes into `author_context` (`fb-group:<id>`, `fb-page:<id>`, `ig-handle:<name>`, `ig-hashtag:<tag>`) and `confidence_notes`. Required collector-side fix: `"facebook"` is currently **missing** from the social-source sets in `infer_comment_intent` (collect.py ~line 598) and `infer_source_intent` (~line 620) — without adding it, Facebook records would be classified `not_social_comment` and excluded from social pain analysis. Raw responses redacted into `raw/scrapecreators.json` as today. Existing problem/workaround keyword relevance scoring is reused unchanged.

No schema change is needed; verify against the schema during implementation.

**Limit-accounting fix (bug found in review, verified live 2026-07-21):** `collect_scrapecreators` currently breaks out of the endpoint loop when total records reach `args.limit`, so one productive endpoint starves the rest — in the smoke test TikTok filled `--limit 5` and the Instagram/Threads calls were never made. Replace the global short-circuit with a per-endpoint cap (`--social-per-endpoint`, default 10): every requested endpoint is always called, each contributes up to the cap, and caps hit are logged in `summary.json` (no silent truncation).

## 4. Component: Ad intelligence (`scripts/evidence_scout/collect_ads.py`)

CLI shape mirrors `analyze_competitor_marketing.py`:

```bash
# Known competitors from competitor-scout
python3 scripts/evidence_scout/collect_ads.py --topic "<topic>" \
  --competitors-json "research/topics/<topic>/competitors/runs/<run>/competitors.json" \
  --countries DE,AT,CH --limit 20

# Keyword mode — discover WHO advertises, not just what known competitors run
python3 scripts/evidence_scout/collect_ads.py --topic "<topic>" \
  --keywords "private krankenversicherung wechseln" --countries DE --limit 30
```

### Provider `meta_ad_library` (primary)

- Graph API `ads_archive`; requires `META_ACCESS_TOKEN` with `ads_read` scope.
- Fields: page name/ID, ad creative body, link caption/title/description, CTA type, delivery start/stop, publisher platforms, EU spend/impression ranges where disclosed.
- Pacing: exponential backoff, stays within the ~200 calls/hour budget; `--limit` caps ads fetched — per competitor in `--competitors-json` mode, total across all results in `--keywords` mode (default 20, hard cap 200 in both modes).
- Every report prints the coverage caveat: commercial ads only for EU/UK audiences, ~1-year retention, coarse ranges, no engagement metrics.
- Token lifecycle: 60-day expiry documented in the validator guidance and the skill references; expired token → clear `token_expired` status + refresh instructions, never a silent fallback.

### Provider `apify_ads` (fallback)

- Apify Facebook Ad Library actor; requires `APIFY_TOKEN`.
- Triggered only when: (a) `--countries` includes non-EU/UK markets, or (b) Meta token missing/scope-denied — **and** the user has approved paid-credit spend for the run (`approval_required: true`).
- Logged in `summary.json` as `fallback_used: apify_ads` with the reason.

### Outputs (workspace-native)

```
research/topics/<topic>/ads/runs/<run>/
  ads.jsonl      # normalized ad records (new schemas/ads-record.schema.json)
  summary.json   # provider statuses, fallback usage, coverage caveats, caps hit
  report.md      # per-competitor: active ad count, longest-running ads, messaging
                 # themes, CTAs, platform split, spend/impression bands
  raw/           # redacted provider responses
```

Ad longevity (delivery start vs. retrieval date) is reported as a *signal of what keeps running*, labeled as a judgment, not proof of performance — spend/conversion cannot be inferred from the Ad Library.

## 5. Tool contracts (risk classes, budgets, stop conditions)

Per agentic best practices, each collector is a documented capability boundary:

| Collector | Action class | Credential scope | Side effects | Budget / stop conditions | Confirmation |
|---|---|---|---|---|---|
| `collect_scrapecreators` (FB/IG flags) | Read-only, paid | `SCRAPE_CREATORS_API_KEY` | Credit spend; writes under run dir | `--fb-max-posts` ≤ 60, `--comments-max`, per-endpoint failure isolation | `approval_required` — one approval per run, not per request |
| `meta_ad_library` | Read-only, free | `META_ACCESS_TOKEN` (`ads_read` only) | Writes under run dir | `--limit` ≤ 200, 200 calls/hr pacing, max 3 backoff retries then `rate_limited` status | None (free official API) |
| `apify_ads` | Read-only, paid | `APIFY_TOKEN` | Credit spend; writes under run dir | `--limit` ≤ 200, actor result cap | `approval_required` — explicit per-run approval |

All three: read-only against external systems; no writes outside `research/topics/<topic>/`; secrets from env/`~/.secrets` only, never logged (existing `redact_sensitive` applies); raw payloads to disk, summaries to stdout/context.

## 6. Untrusted-content and source discipline

- Ad copy, social posts, and comments are **untrusted data**. They inform evidence records; they never change provider selection, expand flags, or trigger other tools. No content from a page/post is ever executed or followed as an instruction.
- Records separate facts (post text, dates, platform), judgments (relevance score, longevity signal), and gaps (private groups inaccessible, non-EU commercial ads without Apify). Reports state explicitly what could not be checked.
- Every record carries provenance: source URL, retrieval date, vendor (`scrapecreators` / `meta` / `apify`), and coverage caveat where applicable.

## 7. Error handling

- Provider failures are recorded per-endpoint in `summary.json` (`ok` / `missing_credentials` / `billing_required` / `rate_limited` / `token_expired` / `empty`); a failed endpoint never aborts the run.
- ScrapeCreators cursor pagination stops on: cap reached, repeated empty page, or credit error. Partial pulls still yield records; the cap and any dropped pages are logged (no silent truncation).
- Meta zero-results for EU keywords → reported as coverage limitation, not "no ads exist".
- `validate_meta.py` extended to probe `ads_archive` (today only `/me`); new `validate_apify.py`; both registered in `scripts/validate_apis/run_all.py`.

## 8. Skill, config, and docs wiring

| File | Change |
|---|---|
| `scripts/evidence_scout/collect.py` | New flags + FB/IG endpoints in `collect_scrapecreators`; new source types in normalization |
| `scripts/evidence_scout/collect_ads.py` | New script (`meta_ad_library` + `apify_ads`) |
| `schemas/ads-record.schema.json` | New schema for `ads.jsonl` records |
| `scripts/validate_apis/validate_meta.py` | Probe `ads_archive`; document 60-day refresh |
| `scripts/validate_apis/validate_apify.py` | **Already exists and passes** (verified 2026-07-21) — verify actor-level guidance, no new file |
| `config/source-capabilities.json` | Add `meta_ad_library` (family `ad_intel`, `approval_required: false`), `apify_ads` (`approval_required: true`); expand scrapecreators `use_when` with facebook groups/pages, instagram hashtags |
| `config/routing-evals.json` | New routing cases (see §9) |
| `.env.example` | Document `META_ACCESS_TOKEN`, `APIFY_TOKEN` (note: file is permission-guarded; edit during implementation) |
| `.agents/skills/evidence-scout/references/{provider-policy,workflow,commands}.md` | Credit costs, 3-posts/call caveat, new flags |
| `.agents/skills/competitor-marketing-analyzer/references/workflow.md` | Ad-evidence step: run `collect_ads.py` after landing-page analysis; compare ad messaging vs. positioning |
| `AGENTS.md` | Command reference for `collect_ads.py` |

## 9. Evals and validation

Repo convention: no unit-test suite; validation = eval fixtures + setup checks + CI. `config/routing-evals.json` is **skill-routing** fixtures (which skill fires), not provider routing — provider routing correctness is enforced by keeping `config/source-capabilities.json` truthful, since `capability_lookup.py` routes from its `use_when` fields. This design conforms and adds:

- **Capability-truth fix (drift found in review):** `source-capabilities.json` currently lists `facebook` in scrapecreators' `use_when`, so `capability_lookup.py` routes Facebook questions to a collector that has zero Facebook endpoints wired (verified: only TikTok/IG-reels/Threads/X are called). Implementation must make the claim true (wire the endpoints) — not delete the claim. Until then the drift is a known bug.
- `config/routing-evals.json`: add one skill-routing fixture — "analyze what ads my competitors run on Facebook and Instagram" must route to `competitor-marketing-analyzer` (forbidden: `social-digital-marketing-planner`), since ad intel becomes part of that skill's workflow.
- `bash scripts/validate_setup.sh` stays green (validates schemas including the new ads-record schema).
- `python3 scripts/run_evals.py` stays green; CI (`.github/workflows/validate.yml`) runs both on push.
- `ads.jsonl` records validated against `schemas/ads-record.schema.json` by the setup script, same as evidence records.
- Live credit-based endpoints (ScrapeCreators FB/IG, Apify) are smoke-tested only with explicit user approval, per provider policy. Meta Ad Library live check happens after the user completes ID verification — as of 2026-07-21 `validate_meta.py` reports `missing_credentials`.

Pass/fail evidence for implementation completion: `validate_setup.sh` output, `run_evals.py` output, `run_all.py` provider statuses, and one approved live run's `summary.json` shown in-session (raw outputs stay gitignored per repo convention).

## 10. Determinism and agentic best-practices conformance

Checked against `~/coding/general/agentic_best_practices`:

- **Least autonomous shape:** collectors are deterministic scripts — no agent loops, no model-in-the-loop retrieval. Model judgment appears only downstream in skill workflows (synthesis, report reading). Bounded retries (3), caps on pages/posts/ads, then escalate via status, never loop.
- **Deterministic gates as repo scripts + CI:** routing and schema checks live in `run_evals.py` / `validate_setup.sh` / CI, not in harness-only features.
- **State in artifacts, not latent memory:** each run is self-describing via `summary.json` + run manifest under `research/topics/<topic>/`; resume/replay follows `references/workspace-lifecycle.md`.
- **Small context:** raw payloads never enter model context; scripts write to disk and return path + summary (existing repo pattern, kept).
- **Minimal viable tool set:** two collectors added; no new MCP servers; ScrapeCreators key reused.
- **Blast radius capped at environment layer:** read-only external calls, scoped credentials (`ads_read` only), workspace-only writes, secrets via env.
- **Approval-fatigue-aware:** paid providers keep `approval_required`, batched per run; the free official API needs none.
- **No silent truncation / no unsupported claims:** caps and coverage limits logged in `summary.json` and repeated in `report.md`; longevity labeled as judgment, not performance proof.

## 11. Out of scope (YAGNI)

- Private/login-gated Facebook groups (no compliant programmatic access exists).
- TikTok/LinkedIn ad libraries, engagement-metric estimation, spend inference beyond disclosed ranges.
- Automated recurring monitoring (`competitor-monitoring` may adopt `collect_ads.py` later).
- Meta Graph API owned-asset insights (user's own pages) — separate need, separate design.

## 12. Live verification results (2026-07-21)

Credential validation (`scripts/validate_apis/`):

| Provider | Status | Note |
|---|---|---|
| scrapecreators | **ok** | 100 free credits on account; ~6 consumed by these tests |
| apify | **ok** | account + plan fields validated |
| meta | **missing_credentials** | user action pending: developer app + ID verification + `META_ACCESS_TOKEN` |

Endpoint tests against ScrapeCreators (1 credit/call observed):

| Endpoint | Result |
|---|---|
| `GET /v1/facebook/profile/posts` (public page) | **works** — 3 posts + `cursor` |
| `GET /v1/facebook/group/posts` | HTTP 200, 0 posts for a private/inaccessible group — ambiguous-empty handling required |
| `GET /v1/instagram/profile` | **works** — data nested under `data` |
| `GET /v2/instagram/user/posts` | **works** — items under `profile_grid_items` + `profile_grid_items_cursor` (dedicated parser needed) |
| `GET /v1/instagram/search/hashtag` | **works** — 10 posts + `cursor`, German PKV content returned |
| `GET /v1/instagram/profile/posts`, `/v1/instagram/hashtag/search` | 404 — wrong paths; do not guess paths, use the verified ones above |

Existing-pipeline smoke test (`collect.py --providers scrapecreators --limit 5`): status `ok`, 5 records, but only the TikTok call executed — Instagram/Threads were starved by the global-limit short-circuit (fix specified in §3). Test workspace: `research/topics/social-access-smoke-test-private-health-insurance-germany/` (may be deleted; it is not a real research topic).

Implementation-review findings folded into this spec:

1. Global-limit starvation bug in `collect_scrapecreators` (fix in §3).
2. `facebook` missing from social-intent sets in `infer_comment_intent` / `infer_source_intent` (fix in §3).
3. Capability drift: `source-capabilities.json` claims Facebook coverage that is not wired (fix in §9).
4. `validate_apify.py` already exists (§8 corrected).
5. `routing-evals.json` is skill-routing, not provider-routing (§9 corrected).
6. `competitor-marketing-analyzer/references/workflow.md` mentions ad-library clues "where available" but the script has no ad tooling — the §4 collector closes this doc/code drift.
