# GEO audit reporting detail (moved from SKILL.md)

### What to report

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

### Evidence for the hygiene stance

- Google, "AI optimization guide" (updated 2026-07-10, checked 2026-10-31): machine-readable AI
  text files "will neither harm nor help" visibility because "Google Search ignores them";
  "Structured data isn't required for generative AI search, and there's no special schema.org markup".
  https://developers.google.com/search/docs/fundamentals/ai-optimization-guide
- Ahrefs, matched difference-in-differences study (2026-05-11; 1,885 pages that added JSON-LD vs
  matched controls): "Adding schema produced no major uplift in citations on any platform";
  AI Mode and ChatGPT changes were within noise. https://ahrefs.com/blog/schema-ai-citations/
- Keep valid schema for rich-result eligibility and entity clarity where the markup matches
  visible facts; that is a separate reason from AI citation.

### Measuring outcomes (optional)

An audit does not show whether engines cite the site. If the owner needs that, use the
AI-answer panel owned by the `competitor-monitoring` route
(`scripts/monitoring/ai_answer_probe.py`; live answers via
`scripts/monitoring/ai_answer_collect.py`). Panel rates are descriptive observations of
declared prompts, not rankings, demand or causal uplift from an audit fix.
