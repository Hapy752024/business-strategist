---
name: competitor-research
description: Discover competitors and substitutes, build a three-lane competitive landscape, or tear down a known competitor's offer, pricing, CTAs and social usage. Use for competitor lists, landscapes, positioning white space or competitor pages.
---

# Competitor Research

One skill, one mode per former competitor specialist. The route ID picks the mode; read only that mode's reference.

| Route ID | Mode | Read |
|---|---|---|
| `competitor-discovery` | scout | [scout](references/scout.md) |
| `competitive-landscape` | landscape | [landscape](references/landscape.md), plus scout and teardown as its lanes need them |
| `competitor-analysis` | teardown | [teardown](references/teardown.md) |

Sibling skills: `competitor-monitoring` owns recurring watchlists and diffs; `evidence-scout` owns customer voice; `brand-website-designer-builder` builds websites.

## Standing rules

- Search before answering; search results are candidate evidence, not truth. Preserve source URLs, snippets and dates.
- Apply repo-root `references/customer-voice.md` for query design before broad collection; keep supplier claims separate from customer experience.
- Classify entity type and source-page type separately; rate evidence quality before competitor strength.
- Blogs, directories, affiliates, agencies and review pages are exclusions unless first-party evidence shows they sell the offer.
- Only verified Lane A (`competitive_market`) entities support competitive-pressure, pricing and whitespace conclusions; similar companies and capability references inform transfer and inspiration only.
- Copy is positioning, not proof of demand or performance. Followers, downloads, press and ad longevity are weak evidence.
- Provider failures, billing errors and fallback-only evidence are coverage gaps; state them before interpreting the set.
- Say "I don't know" or mark `uncertain`/`not_found` instead of guessing; ask one focused question only when the answer would change classification.
- Parallel lanes use one `competitor-researcher` agent each (`.claude/agents/competitor-researcher.md`) with exclusive output directories; this skill owns classification, deduplication and positioning.

## Scripts

`scripts/evidence_scout/discover_competitors.py` (scout), `analyze_competitor_marketing.py` (teardown, content inventory), `collect_social_presence.py`, `build_entity_landscape.py` and `build_landscape_artifacts.py` (landscape). Commands and flags are in the mode references.

## Output

Scout: classified competitor array, exclusions and teardown candidates. Landscape: lane-aware entity landscape, service/price matrix, social-presence table, positioning hypotheses, inspiration library and quality gate. Teardown: sourced positioning and marketing-mix tables, differentiation hypotheses, weak claims to avoid and evidence gaps. Ask the user exactly one question at a time.
