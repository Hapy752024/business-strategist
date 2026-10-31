# Earned media workflow

## Procedure

Discovery: start with a named audience/job, market/language, useful public destination and selected objective. If no suitable asset exists, explain that gap and propose a resource brief; do not invent an asset or start a website rebuild. Search using existing repository search tools, relevant publications/associations in reviewed research and optional catalogue candidates. Retain exact source passages and dated captures. Classify business profiles, reviewed product listings, editorial references and paid partnerships separately.

Competitor-link prospecting: `python3 scripts/marketing/competitor_backlinks.py --competitor <domain> ... --own <own-domain> --out <new-dir>` (DataForSEO, metered, read the printed estimate) lists domains linking to named competitors, minus those already linking to the property. Treat every row as a candidate needing the qualification below; flagged rows (scraper pages, image or empty anchors) are normally rejected with that reason.

Two further discovery lanes:
- AI-cited roundups: for the audience's buying or planning question, find which roundup/list pages AI answers cite (recorded AI-answer visibility through the `competitor-monitoring` skill; live collection is capped), then treat each cited page as a candidate only where the asset fills a reader need the list misses; propose the exact entry text. Retain the answer capture (surface, prompt, date) and the roundup passage.
- Missing visual: find text-heavy pages for the audience where one named section would be clearer with a chart or diagram; propose that one graphic, built only from the page's own facts or cited primary sources. Ask the author before producing it; paid asset generation needs its own approval. Preparation includes the image, alt text and credit wording.

Use `python3 scripts/marketing/earned_media.py validate <opportunities.json> --base <marketing-root>` to validate reviewed opportunity records. Public catalogue entries and Links exports are candidate sources. Their claims are not destination verification. Preserve source provenance; review official domains and current rules independently.

Preparation: choose only reviewed qualified opportunities. Assemble an exact pitch/listing with destination, contact route, audience benefit, substantiated facts, eligibility, fees/renewals, account dependencies, authorization basis and observable completion. Use `python3 scripts/marketing/earned_media.py prepare <opportunity.json> --base <marketing-root> --material <relative-file> --out <plan.json>` to produce a version-2 proposed action. Preparing an action does not authorize it. Use separate send/submission and placement actions when both are required; preparation-only scope can complete on its own evidence.

Verification: use `python3 scripts/marketing/verify_links.py --source <public-page> --target <expected-destination> --id <observation-id> --out <new-run-directory>`. Immutable output includes capture.html and observation.json. Use `--evidence-root <marketing-root>` when the run is nested there so capture bindings are rooted correctly. Distinguish present, absent, access-limited and fetch-error. HTTP verification performs no JavaScript. Rendered fallback for untrusted public pages is disabled; an authorized manually retained DOM can be reviewed with method provenance and explicit limitations.

Link ledger: `python3 scripts/marketing/link_ledger.py --base <business-root> <init|import-candidates|import-links|set|record|check|report>` keeps one row per source page at `marketing/earned_media/link-ledger.json` (prospect, pitched, promised, live, lost, rejected, declined). Pitches and promises are set by hand with dates; only a recorded `verify_links.py` observation moves a row to live or lost; `check --max N` runs those observations for due rows; `report` lists overdue follow-ups (one pitch, 7+ days, no reply).

Keep positive reply, live anchor, backlink-provider observation, search indexing, referrals and qualified customer outcomes separate. Relative/base href resolution and rel attributes are observations, never a guarantee of ranking credit. Dates are actual capture dates; do not backdate first-seen.

## Output

Publish applicable records, prepared materials, capture bindings and execution plan through the existing Marketing publisher. It checks staged bytes and unchanged disk evidence in the same transaction. No duplicate approval/sent/completed authority belongs in opportunity records. Version-1 plans remain legacy; earned-media preparation/verification uses version 2.

For outcome review, use existing aggregate export normalization and decision records, tying the reviewed action to compatible windows and confounders. Optional ideas do not block the requested deliverable. A required placement stays pending until its own captured observation is valid.

## Quality Checklist

No autonomous sends, account creation, subscription purchase or recurring jobs are implemented. Stop contact proposals after rejection/opt-out; preserve exclusions across later packets. Reject duplicate opportunity IDs and deduplicate source/destination pairs. Unknown or inaccessible sources remain gaps. Reports must not claim this workflow produces ranking uplift or is a running service.
