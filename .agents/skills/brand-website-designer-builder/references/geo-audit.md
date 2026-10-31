# GEO audit mode (route `geo-audit`)

Based on GEO Optimizer by Juan Camilo Auriti (MIT), pinned at commit
`7ecec864690ee430e954a95352130cf47e2c92cc`. Provenance and licence: `geo/VENDOR.md` and `geo/LICENSE` in this skill.
This mode is not GEO Optimizer or GeoReady and is not endorsed by their author.

## Scope

- Read-only. Never run `geo fix --apply`, never write robots.txt, llms.txt or schema into a site,
  and never publish anything. Fixes are proposals; [AEO/GEO visibility](aeo-geo-visibility.md) owns prioritisation.
- A score is the tool's readiness rubric, not a citation rate, ranking or traffic forecast.

## Stage checklist

1. Confirm a public or preview URL. The tool refuses localhost, private addresses and local build
   directories; ask for a deployed preview instead of scoring a directory.
2. Run the wrapper (below) and record the status.
3. Order findings (below), separating blocking issues from hygiene.
4. Hand off (below); "No change warranted" is a valid outcome.

## Run

```bash
python3 .agents/skills/brand-website-designer-builder/geo/geo_audit.py --url https://preview.example.com/ \
  --out <new-path>/geo-audit.json
```

- `status: ok` (exit 0): audit saved with tool version, pinned commit, raw JSON and boundary note.
- `status: tool_unavailable` (exit 2): the CLI is not installed. Report it; do not install globally
  and do not substitute a hand-made score. Project-local venv install: `geo/VENDOR.md`.
- `status: needs_public_url` (exit 2): deploy a preview or audit the production URL instead.
- `status: audit_failed` / `fail` (exit 1): tool or I/O error; the target stays unaudited.

Set `GEO_AUDIT_BIN` to the venv's `geo` binary when it is not on `PATH`. Use
`--max-pages N` (wrapper flag) to sample a sitemap; state the sampled pages in the report.

## What to report

Order findings by whether they can block AI search eligibility at all:

1. Access: final status 200, no `noindex`, Googlebot and search-tier bots (`OAI-SearchBot`,
   `Claude-SearchBot`, `PerplexityBot`) not blocked unless the owner chose to, CDN bot-blocking defaults.
   Training bots are a separate owner policy choice ([AEO/GEO visibility](aeo-geo-visibility.md), crawler policy).
2. Snippet controls: `nosnippet`, `max-snippet` below ~50, heavy `data-nosnippet` use.
3. Canonical, crawlable `<a href>` links, sitemap declared, rendered content not JS-only.
4. Content citability: direct answers to evidence-backed customer questions, named sources,
   verifiable figures, visible author/date where relevant. Do not rewrite solely for AI.
5. Entity consistency: Organization/Person facts match across site and profiles.
6. Hygiene only: llms.txt, `ai.txt`/summary endpoints, JSON-LD richness. Report as housekeeping,
   never as a visibility or ranking lever.

Why hygiene: Google's AI optimization guide (updated 2026-07-10, checked 2026-10-31) says AI text files
"will neither harm nor help" and no special schema is needed
(https://developers.google.com/search/docs/fundamentals/ai-optimization-guide); Ahrefs' matched study
(2026-05-11) found "no major uplift in citations" from adding schema (https://ahrefs.com/blog/schema-ai-citations/).
Keep valid schema for rich results and entity clarity where it matches visible facts.
Upstream uplift figures (Princeton GEO-bench, 2024) are benchmark scores, not citation rates; never quote them as gains.

## Handoff

Return: audited URL(s) and timestamp, tool version and commit, blocking issues, hygiene items,
items needing owner access (Search Console AI inclusion setting, CDN rules), and anything the tool
could not check.
An audit does not show whether engines cite the site; for that use the `competitor-monitoring` AI-answer panel
(`scripts/monitoring/ai_answer_probe.py`, live via `scripts/monitoring/ai_answer_collect.py`), whose rates are
descriptive observations, not rankings, demand or causal uplift from an audit fix.
