---
name: brand-website-designer-builder
description: Build and maintain Next.js websites. Use for landing pages, responsive fixes, speed, technical SEO, LLM-EO, GEO audits, Stripe integration, browser testing, optional analytics, campaign tracking, or A/B experiments.
---

# Brand Website Designer-Builder

## Procedure

Follow [workflow](references/workflow.md) and the repository subproject contract.
Start standalone from the user's brief; consume Business/Branding only through explicit handoff.
Preserve business-linked gates and resumable website manifests.
Routes `geo-audit` and `stripe-best-practices` follow only that mode reference; page builds or changes need route `website-build`.

- New builds/redesigns: apply [reference-site and supplied-photo intake](references/reference-sites.md) before creative direction.
Ask once for admired sites and photos unless supplied or declined; design-preserving repairs skip intake.
- New builds: load preference profile/brand constraints, propose lightweight territories and obtain selection before expansion; pin stable Next.js.
- Imagery: apply [image sourcing and AI references](../brand-asset-producer/references/image-sourcing.md); verify stock rights; paid FAL needs an approved concrete need. Branding owns favicons; integrate its handoff.
- New build/release: apply [launch contract](references/launch-contract.md), [SEO/performance](references/seo-performance.md), [EU consent](references/consent-eu.md), [testing](references/testing.md).
Launch gate: `python3 -m scripts.brand.site_gate` on the served build, and `scripts/marketing/verify_tracking.py` before paid launch (workflow steps 9, 9a).
- Forms, wizards, accounts, embeds, analytics or personal-data changes: apply [privacy by design](references/privacy-design.md) before implementation.
- Sites with external resources: apply [external-link maintenance](references/external-link-maintenance.md), including the weekly CI checker and owner handoff.
- SEO checks and link-earning content (build only from a reviewed public-resource brief): apply repo-root `references/seo-rule-pack.md`.
- Repairs/audits: use [maintenance](references/maintenance.md), preserving design and unrelated work.
Visibility work also loads [AEO/GEO](references/aeo-geo-visibility.md), repo-root `references/seo-rule-pack.md` and repo-root `references/marketing-execution.md`; [DEO](references/deo-agent-readiness.md) only when applicable.
- Campaign-driven pages and result-led revisions: apply [campaign review handoff](references/campaign-review-handoff.md), binding audience, offer, claims, CTA and measurement to selected Marketing artifacts.
- Only when selected: [PostHog analytics](references/posthog.md), [A/B experiments](references/experimentation.md), [campaign tracking](references/campaign-tracking.md).
Never activate tracking silently.
- Prepare a reviewable PR/Preview; production, account connections, analytics activation and traffic allocation need owner authorization.

## Output
Return manifest, source/asset provenance, QA evidence, open gaps, release state and next action.

## Quality Checklist

Run build and real-browser responsive, accessibility, performance, state and visual gates plus independent quality review.
Production recording requires the complete release-bound launch assessment.
After each authorized deploy, run the production host probe and hand the owner the Search Console steps unprompted (launch-contract `production_host`, `search_console`).

- Optional measurement, reported as observations, never ranking or citation claims: [GEO audit](references/geo-audit.md) (vendored tool and licence in `geo/`) and the AI-answer panel (repo-root `references/ai-answer-recordings.md`).
- Stripe work, also inside builds: [Stripe](references/stripe.md).
- Validation page for a smoke test: apply [validation page](references/validation-page.md) and repo-root `references/smoke-test.md`; static single-CTA page, disclosure, no analytics without owner activation.
- Marketing work needing an owner action or third-party platform: use repo-root `references/marketing-execution.md`; keep local QA separate from externally verified outcomes.

Advertising-event implementation or repair: read repo-root `references/journey-activation-and-measurement.md` and verify per-platform mapping in selected destinations.
