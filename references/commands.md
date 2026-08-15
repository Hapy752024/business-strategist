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
python3 scripts/evidence_scout/collect_ads.py --topic "<topic>" --competitors-json "research/topics/<topic>/competitors/runs/<run>/competitors.json" --countries DE,AT,CH --limit 20

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
```

## Competitor Marketing Analysis

```bash
python3 scripts/evidence_scout/analyze_competitor_marketing.py --topic "<topic>" --competitors-json "research/topics/<topic>/competitors/runs/<run>/competitors.json" --limit 10
```

## Founder/Operator Playbooks

```bash
python3 scripts/evidence_scout/research_founder_playbooks.py --topic "<topic>" --archetype "<business archetype>" --customer-segment "<segment>"
```

## Interview Kit (interview-bridge)

```bash
python3 scripts/evidence_scout/build_interview_kit.py --run-dir "research/topics/<topic>/evidence/runs/<run>" --limit 8
```

## Whitespace Matrix

```bash
python3 scripts/evidence_scout/build_whitespace_matrix.py --topic "<topic>" --evidence-jsonl "research/topics/<topic>/evidence/runs/<run>/evidence.jsonl" --competitors-json "research/topics/<topic>/competitors/runs/<run>/competitors.json"
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

### Initialize topic workspace

```bash
python3 scripts/evidence_scout/init_topic.py --topic "<topic>" --customer-segment "<segment>"
```