---
name: marketing
description: Build evidence-grounded marketing strategy, positioning, messaging, channels and campaigns; SEO keyword/page plans; social plans; or validate a content/channel idea. Use when the user asks how to market, launch or acquire demand.
compatibility: Requires the business-strategist repository and its shared repo-root `references/task-scope.md` contract.
---

# Marketing

The route ID picks the mode; read only that mode's reference.

| Route ID | Mode | Use when | Read |
|---|---|---|---|
| `marketing-strategy` | strategy | strategy, positioning, messaging, offer, funnel, channels, campaigns, ad copy | [strategy](references/strategy.md) in strategy scope |
| `seo-page-planning` | seo-page-planning | keyword research, keyword-to-page map, SEO content briefs | [SEO page planning](references/seo-page-planning.md) |
| `social-marketing` | social | organic or paid social plans, calendars, creative tests | [social](references/social.md) in strategy scope; [paid campaign planning](references/paid-campaign-planning.md) for budget and stop rules; [campaign execution](references/campaign-execution.md) |
| `social-media-idea-validator` | channel-validation | a content or channel idea needs a GO/PIVOT/KILL test | [channel validation](references/channel-validation.md), [founder playbooks](references/founder-playbooks.md) |

Strategy, SEO page planning and social are pain-gated with strategy-stage prerequisites; the router enforces them and records any audited override.

## Scope (strategy and social)

1. Read repo-root `references/task-scope.md`; reuse supplied context and select focused, execution or strategy scope.
2. Focused answers and copy, calendar or campaign execution use the supplied audience, offer, channel, tone, proof limits and CTA. Return only the requested deliverable; label material assumptions and ask only when a missing fact changes it. Do not reopen positioning, invent a channel strategy or require a strategy file for routine work.
3. Strategy scope reads the mode reference completely and reuses the active strategy record.

## Standing rules

- Ground channels in audience evidence; give each a job, budget cap and stop rule. Engagement is attention, not demand.
- Fill and read [product-marketing context](references/product-marketing-context.md) first when it exists.
- Never publish, post or spend without approval; a plan does not authorize launch.
- Verify current official platform specs before precise claims; paid scaling needs retained-value evidence.
- Mark unchecked evidence `[DATA UNAVAILABLE]`; cite dated sources.

## Shared references (when the stage needs them)

- Stage tools: `scripts/evidence_scout/search_journey.py`, `scripts/marketing/keyword_map.py merge`, `python3 -m scripts.brand.site_gate` (page launch gate), `scripts/marketing/verify_tracking.py` (before launch spend). External opportunities: earned-media-builder.
- repo-root `references/marketing-execution.md` (multi-step work, owner-only actions, reporting)
- repo-root `references/journey-activation-and-measurement.md` and repo-root `references/ad-platform-connections.md` (funnels, paid setup; neither authorizes spend)
- repo-root `references/seo-rule-pack.md` (SEO hygiene, linkable assets, visibility interventions); recordings: repo-root `references/ai-answer-recordings.md` (processor offline; no mandatory multi-engine program).
- repo-root `references/evidence-registry.md`, repo-root `references/strategic-positioning.md`, repo-root `references/customer-voice.md`, repo-root `references/customer-question-tracking.md`, repo-root `references/comparative-creative-analysis.md`
- repo-root `references/research-coaching.md` (chosen-idea continuation) and repo-root `references/interview-recruitment.md` (unpaid recruitment, zero-network route)

## Output

Focused/execution: the requested deliverable. Otherwise: the mode reference's output.
