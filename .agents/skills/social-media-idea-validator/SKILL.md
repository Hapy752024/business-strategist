---
name: social-media-idea-validator
description: Validate a social media, content, or channel idea before investing production effort. Use when the user asks whether a content series, YouTube/TikTok/LinkedIn channel, podcast, SEO topic cluster, newsletter, or social campaign concept is worth pursuing for their business. Checks audience presence, demand evidence, founder-format fit, differentiation and white space, and channel economics, then returns a GO / PIVOT / KILL verdict with a low-cost test plan. NOT for building the full social or digital marketing plan after validation → use `social-digital-marketing-planner`. NOT for overall marketing strategy, segmentation, or positioning → use `marketing-strategy-builder`. NOT for validating the underlying business idea → use `idea-grill`.
---

# Social Media Idea Validator

## Success Criteria
- **Quantitative:** triggers on >=90% of "is this social/content idea worth it" queries; completes in <=15 tool calls; every GO verdict cites at least one demand signal and one audience-presence signal; zero verdicts without an explicit test plan and stop rule.
- **Qualitative:** verdicts follow the founder evidence base (practitioner patterns, not vibes); ideas are killed or pivoted when demand evidence is missing; the user can execute the low-cost test within one week.

## Workflow

1. Read `references/workflow.md` for the six validation gates and evidence instruments.
2. Read `references/founder-playbooks.md` for the practitioner evidence base (SaaS, fintech/insurtech, professional services).
3. Restate the idea as a testable claim: audience, platform, format, promise, conversion event.
4. Run the gates in order: audience presence → demand evidence → founder-format fit → differentiation/white space → channel economics → sustainability. Stop early on a hard KILL.
5. Return the verdict with evidence, confidence, and a one-week low-cost test.

## Output

Produce: idea restatement, gate-by-gate evidence table, GO / PIVOT / KILL verdict with confidence, the cheapest test that would change the verdict, stop rules, and source list with dates. Mark missing evidence `[DATA UNAVAILABLE]` instead of filling gaps from memory.
