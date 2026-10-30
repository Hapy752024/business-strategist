---
name: geo-audit
description: Audits a public site or deployed preview for AI-search citability issues with the pinned GEO Optimizer CLI. Use when a site needs a GEO check; treats llms.txt and schema as hygiene, not ranking levers.
---

# GEO audit

Based on GEO Optimizer by Juan Camilo Auriti (MIT), pinned at commit
`7ecec864690ee430e954a95352130cf47e2c92cc`. See [VENDOR.md](VENDOR.md) and [LICENSE](LICENSE).
This skill is not GEO Optimizer or GeoReady and is not endorsed by their author.

## Scope

- Input: a public URL, or a build deployed to a public preview URL. The upstream tool refuses
  localhost and private addresses; it cannot audit a local build directory.
- Output: one audit file plus a short issue list handed to `brand-website-designer-builder`
  (its AEO/GEO visibility procedure owns prioritisation and owner actions).
- Read-only. Never run `geo fix --apply`, never write robots.txt, llms.txt or schema into a site,
  and never publish anything. Fixes are proposals for the website owner workflow.
- A score is the tool's readiness rubric. It is not a citation rate, ranking or traffic forecast.

## Run

```bash
python3 .agents/skills/geo-audit/scripts/geo_audit.py --url https://preview.example.com/ \
  --out <new-path>/geo-audit.json
```

- `status: ok` (exit 0): audit saved with tool version, pinned commit, raw JSON and boundary note.
- `status: tool_unavailable` (exit 2): the CLI is not installed. Report it; do not install globally
  and do not substitute a hand-made score. Installation into a project-local venv is in VENDOR.md.
- `status: needs_public_url` (exit 2): deploy a preview or audit the production URL instead.
- `status: audit_failed` / `fail` (exit 1): tool or I/O error; the target stays unaudited.

Set `GEO_AUDIT_BIN` to the venv's `geo` binary when it is not on `PATH`. Use
`--max-pages N` (wrapper flag) to sample a sitemap; state the sampled pages in the report.

## What to report

Order findings by whether they can block AI search eligibility at all:

1. Access: final status 200, no `noindex`, Googlebot not blocked, search-tier bots
   (`OAI-SearchBot`, `Claude-SearchBot`, `PerplexityBot`) not blocked unless the owner chose to.
   Training bots (`GPTBot`, `ClaudeBot`, `Google-Extended`) are a separate owner policy choice.
   Check CDN bot-blocking defaults too.
2. Snippet controls: `nosnippet`, `max-snippet` below ~50, heavy `data-nosnippet` use.
3. Canonical, crawlable `<a href>` links, sitemap declared, rendered content not JS-only.
4. Content citability: direct answers to evidence-backed customer questions, named sources,
   verifiable figures, visible author/date where relevant. Do not rewrite solely for AI.
5. Entity consistency: Organization/Person facts match across site and profiles.
6. Hygiene only: llms.txt, `ai.txt`/summary endpoints, JSON-LD richness. Report as housekeeping,
   never as a visibility or ranking lever.

Upstream content-method uplift figures (Princeton GEO-bench, 2024) are relative visibility scores
from a research benchmark, not citation rates on current engines. Do not quote them as expected gains.

## Evidence for the hygiene stance

- Google, "AI optimization guide" (updated 2026-07-10, checked 2026-10-31): machine-readable AI
  text files "will neither harm nor help" visibility because "Google Search ignores them";
  "Structured data isn't required for generative AI search, and there's no special schema.org markup".
  https://developers.google.com/search/docs/fundamentals/ai-optimization-guide
- Ahrefs, matched difference-in-differences study (2026-05-11; 1,885 pages that added JSON-LD vs
  matched controls): "Adding schema produced no major uplift in citations on any platform";
  AI Mode and ChatGPT changes were within noise. https://ahrefs.com/blog/schema-ai-citations/
- Keep valid schema for rich-result eligibility and entity clarity where the markup matches
  visible facts; that is a separate reason from AI citation.

## Measuring outcomes (optional)

An audit does not show whether engines cite the site. If the owner needs that, use the
AI-answer panel owned by the `competitor-monitoring` route
(`scripts/monitoring/ai_answer_probe.py`; live answers via
`scripts/monitoring/ai_answer_collect.py`). Panel rates are descriptive observations of
declared prompts, not rankings, demand or causal uplift from an audit fix.

## Handoff

Return: audited URL(s) and timestamp, tool version and commit, blocking issues, hygiene items,
items needing owner access (Search Console AI inclusion setting, CDN rules), and anything the tool
could not check. "No change warranted" is a valid outcome.
