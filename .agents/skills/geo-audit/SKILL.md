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

Order findings by whether they can block AI search eligibility at all: access (status 200, no `noindex`, search-tier bots not blocked), snippet controls, canonical and crawlable links, content citability, entity consistency, then hygiene only.
`llms.txt`, `ai.txt` and JSON-LD richness are hygiene, never a visibility or ranking lever: Google's AI optimization guide (2026-07-10) says AI text files neither harm nor help, and Ahrefs' matched study (2026-05-11) found no major citation uplift from schema.
Checks, sources and quotes: [reporting detail](references/workflow.md).
For citation outcomes, use the `competitor-monitoring` AI-answer panel; its rates are descriptive, not causal.

## Handoff

Return: audited URL(s) and timestamp, tool version and commit, blocking issues, hygiene items,
items needing owner access (Search Console AI inclusion setting, CDN rules), and anything the tool
could not check. "No change warranted" is a valid outcome.
