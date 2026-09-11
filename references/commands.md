# Full Command Reference

Extended CLI command variants for each skill. Prefer the AGENTS.md shorthand for common use; load this reference when the full variant set is needed.

## Evidence Scout

### Default providers

```bash
python3 scripts/evidence_scout/collect.py --topic "<topic>" --customer-segment "<segment>" --problem-keywords "<pain phrase 1>,<pain phrase 2>" --workaround-keywords "<workaround 1>,<workaround 2>" --hypothesis-id H1 --days 30 --limit 20 --providers default
```

### With social enrichment (paid, ask first)

```bash
python3 scripts/evidence_scout/collect.py --topic "<topic>" --customer-segment "<segment>" --problem-keywords "<pain>" --workaround-keywords "<workaround>" --hypothesis-id H1 --days 30 --limit 20 --providers default,social
```

### Facebook/Instagram social evidence (ScrapeCreators, paid — ask first)

```bash
# Public Facebook groups + Instagram hashtags for pain evidence
python3 scripts/evidence_scout/collect.py --topic "<topic>" --customer-segment "<segment>" --problem-keywords "<pain>" --providers scrapecreators --fb-groups "<public-group-url>" --ig-hashtags "<tag1,tag2>" --social-comments

# Competitor/niche Facebook pages and Instagram profiles for content intel
python3 scripts/evidence_scout/collect.py --topic "<topic>" --customer-segment "<segment>" --providers scrapecreators --fb-pages "<page-url>" --ig-handles "<handle1,handle2>" --fb-max-posts 15
```

## Competitor Ads Intelligence

```bash
# Known competitors (free official Meta Ad Library; EU/UK/EEA commercial ads only)
python3 scripts/evidence_scout/collect_ads.py --topic "<topic>" --competitors-json "projects/<topic>/market_research/solution_alternatives/runs/<run>/competitors.json" --countries DE,AT,CH --limit 20

# Keyword mode — discover WHO advertises
python3 scripts/evidence_scout/collect_ads.py --topic "<topic>" --keywords "<keyword 1>,<keyword 2>" --countries DE --limit 30

# Non-EU market or missing Meta token — Apify fallback (paid, requires --approve-paid after user approval)
python3 scripts/evidence_scout/collect_ads.py --topic "<topic>" --keywords "<keyword>" --countries US --providers auto --approve-paid
```

### China-market coverage (public only)

```bash
python3 scripts/evidence_scout/collect.py --topic "<topic>" --customer-segment "<segment>" --problem-keywords "<pain>" --workaround-keywords "<workaround>" --hypothesis-id H1 --days 30 --limit 20 --providers default,china_public --geo CN --language zh
```

### With local extraction (crawl4ai)

```bash
python3 scripts/evidence_scout/collect.py --topic "<topic>" --customer-segment "<segment>" --problem-keywords "<pain>" --workaround-keywords "<workaround>" --hypothesis-id H1 --days 30 --limit 20 --providers default,crawl4ai --local-extract-url-limit 5
```

### With document ingestion (markitdown)

```bash
python3 scripts/evidence_scout/collect.py --topic "<topic>" --customer-segment "<segment>" --problem-keywords "<pain>" --document-paths "path/to/doc.pdf,https://example.com/report" --providers default,markitdown --document-limit 5
```

### App-store enrichment (Sonar, paid — ask first)

```bash
python3 scripts/evidence_scout/collect.py --topic "<topic>" --customer-segment "<segment>" --problem-keywords "<pain>" --providers default,sonar --sonar-apps ios:<app_id>,android:<package_name>
```

## Market Problem Discovery

### Start a discovery run

```bash
python3 scripts/evidence_scout/discover_market_problems.py --topic "<market or domain>" --focus "<optional rough hunch>" --geo AUTO --language AUTO --collect
```

### Finalize after synthesis

```bash
python3 scripts/evidence_scout/discover_market_problems.py --finalize --run-dir "<run path>" --candidate-count <0-7>
```

### Narrow scope discovery

```bash
python3 scripts/evidence_scout/discover_market_problems.py --topic "<market>" --focus "<hunch>" --problem-keywords "<pain 1>,<pain 2>" --workaround-keywords "<workaround 1>" --collect
```

## Competitor Discovery

```bash
python3 scripts/evidence_scout/discover_competitors.py --topic "<topic>" --customer-segment "<segment>" --known-competitors "<optional comma-separated names>" --limit 20

# Add Lane B and Lane C scopes explicitly (lane provenance is preserved per source observation)
python3 scripts/evidence_scout/discover_competitors.py --topic "<topic>" --customer-segment "<segment>" --analog-market "<other country or segment>" --reference-capability "website" --reference-capability "YouTube" --limit 20
```

## Competitor Marketing Analysis

```bash
python3 scripts/evidence_scout/analyze_competitor_marketing.py --topic "<topic>" --competitors-json "projects/<topic>/market_research/solution_alternatives/runs/<run>/competitors.json" --limit 10

# Analyze only one lane
python3 scripts/evidence_scout/analyze_competitor_marketing.py --topic "<topic>" --competitors-json "projects/<topic>/market_research/solution_alternatives/runs/<run>/competitors.json" --lane similar_company --limit 5
```

## Lane-aware landscape artifacts

```bash
python3 scripts/evidence_scout/collect_social_presence.py --entities-json "<competitors.json>" --marketing-json "<marketing_analysis.json>" --out "<run>/social-observations.json"
python3 scripts/evidence_scout/build_entity_landscape.py --competitors-json "<competitors.json>" --discovery-summary-json "<discovery-summary.json>" --marketing-json "<marketing_analysis.json>" --social-json "<run>/social-observations.json" --service "<service>" --job "<customer job>" --target-segment "<segment>" --geography "<country/market>" --out "<run>/entity-landscape.json"
python3 scripts/evidence_scout/build_landscape_artifacts.py --entities-json "<entity-landscape.json>" --marketing-json "<marketing_analysis.json>" --out-dir "<run>/landscape"
```

## Founder/Operator Playbooks

```bash
python3 scripts/evidence_scout/research_founder_playbooks.py --topic "<topic>" --archetype "<business archetype>" --customer-segment "<segment>"
```

## Interview Kit (interview-bridge)

```bash
python3 scripts/evidence_scout/build_interview_kit.py --run-dir "projects/<topic>/market_research/pain_points/runs/<run>" --limit 8
```

## Whitespace Matrix

```bash
python3 scripts/evidence_scout/build_whitespace_matrix.py --topic "<topic>" --evidence-jsonl "projects/<topic>/market_research/pain_points/runs/<run>/evidence.jsonl" --competitors-json "projects/<topic>/market_research/solution_alternatives/runs/<run>/competitors.json"
```

## Infrastructure

### Validate APIs

```bash
python3 scripts/validate_apis/run_all.py
```

### Capability lookup

```bash
python3 scripts/capability_lookup.py --question "<research need>" --compact
```

### Provider doctor

```bash
python3 scripts/evidence_scout/provider_doctor.py --json
```

### Setup validation

```bash
bash scripts/validate_setup.sh
```

### Initialize project workspace

```bash
python3 scripts/evidence_scout/init_project.py --project "<project>" --customer-segment "<segment>"
```
# Strategy execution review

Run from the repository root. KPI definitions in `schemas/strategy-plan.schema.json` require `direction: at_least` or `at_most`; do not assume larger values are better. Existing plans must add direction before validation.

```bash
python3 scripts/strategy_review.py validate --plan <strategy-plan.json>
python3 scripts/strategy_review.py freeze --plan <strategy-plan.json> --output <baseline.json>
python3 scripts/strategy_review.py weekly-review --plan <strategy-plan.json> --baseline <baseline.json> --observations <observations.json>
```

Freeze before collecting results. Baseline creation refuses overwrite. Review rejects changed experiment/KPI definitions; preserve the baseline and start a new experiment revision when rules change. Numeric observations use the numerator/denominator field names. For scoped KPIs, include `_metadata` keyed by KPI name with matching `window`, `currency`, and/or `cohort`; cohort observations also require `mature: true`. Missing, invalid, mismatched, or immature observations return `incomplete`, never success. Commitments may include `completed_at`; uncompleted commitments are reported as pending or overdue. The report retains the supplied strategic verdict for founder review; it does not infer a business verdict from a ratio alone.


## Bounded evidence collection

`collect.py` now defaults to `--max-http-requests 100` for calls through the shared HTTP helper. Reaching the cap stops later providers, preserves collected records, marks the run blocked, and exits 2. `summary.json` includes `request_budget`, `collection_complete`, and structured `remaining_tasks`; `report.md` lists unfinished provider/quality work. Resolve these tasks before claiming complete coverage. This limit excludes SDK/CLI traffic and implicit redirects, and is not a dollar or wall-clock budget.

Identical successful GETs are reused only when the response explicitly supplies a positive HTTP `max-age`, capped at 60 seconds and adjusted for `Age`. Credentials and headers are part of the in-memory cache identity. POSTs, failures and non-cacheable responses stay live. The bounded cache is cleared at run end and is never written to disk. Use `--fresh-http` to disable reuse. No automatic retries or cross-run cache were introduced.
