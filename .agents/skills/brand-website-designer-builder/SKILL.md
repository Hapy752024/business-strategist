---
name: brand-website-designer-builder
description: Build and maintain Next.js websites. Use for landing pages, responsive fixes, speed, technical SEO, LLM-EO, browser testing, optional analytics, campaign tracking, or A/B experiments.
---

# Brand Website Designer-Builder

## Procedure

Follow [workflow](references/workflow.md) and the repository subproject contract.
Start standalone from the user's brief; consume Business/Branding only through explicit handoff.
Preserve business-linked gates and resumable website manifests.

- New builds/redesigns: apply [reference-site and supplied-photo intake](references/reference-sites.md) before creative direction.
Ask once for admired sites and available photos unless already supplied or declined; inspect and record the references.
Design-preserving repairs do not restart intake.
- New builds: load preference profile/brand constraints, propose lightweight territories and obtain selection or delegated selection before expansion.
Resolve/pin stable Next.js; server components by default.
- For imagery, apply [image sourcing and AI references](../brand-asset-producer/references/image-sourcing.md): support supplied photos as-is or as AI guidance, verify stock rights, and use the available native imagegen skill before provider-specific alternatives.
Licensed stock may inspire AI imagery when the planned use is permitted.
- Use approved assets; paid FAL needs an approved concrete need.
Branding owns favicon production through brand-asset-producer; website integrates the handoff.
- New build/release: apply [launch contract](references/launch-contract.md), [SEO/performance](references/seo-performance.md), [EU consent](references/consent-eu.md), [testing](references/testing.md).
Launch gate: `python3 -m scripts.brand.site_gate` on the served build, and `scripts/marketing/verify_tracking.py` before paid launch (workflow steps 9, 9a).
- For forms, wizards, accounts, embeds, analytics or changes to personal-data use, apply [privacy by design](references/privacy-design.md) before implementation.
Minimize collection and use layered, timely information; distinguish notices from consent and test actual data handling.
- For sites with external resources, apply [external-link maintenance](references/external-link-maintenance.md): derive the inventory from published content, retain referring pages, classify uncertain checks and automatically create or update GitHub Actions CI with a weekly schedule and manual trigger.
Include the runnable checker, reports and owner handoff; instructions alone are incomplete delivery.
Preserve an explicit user opt-out or an existing equivalent CI provider.
- SEO checks (hreflang, drift, programmatic pages, schema, llms.txt): apply repo-root `references/seo-rule-pack.md`.
- Content that earns links and AI citations (statistics pages, calculators, checklists per journey stage): apply repo-root `references/seo-rule-pack.md` and build only from a reviewed public-resource brief.
- Repairs/audits: use [maintenance](references/maintenance.md), preserving design and unrelated work.
Visibility work also loads [AEO/GEO](references/aeo-geo-visibility.md), repo-root `references/seo-rule-pack.md` and repo-root `references/marketing-execution.md`; [DEO](references/deo-agent-readiness.md) only when applicable.
- Campaign-driven pages and result-led revisions: apply [campaign review handoff](references/campaign-review-handoff.md), binding audience, offer, claims, CTA and measurement to the selected Marketing artifacts.
- Only when selected: [PostHog analytics](references/posthog.md), [A/B experiments](references/experimentation.md), [campaign tracking](references/campaign-tracking.md).
Analytics and experiments are optional; never activate tracking silently.
- Prepare a reviewable PR/Preview; production, account connections, analytics activation and traffic allocation retain owner authorization.

## Output
Return manifest, source/asset provenance, QA evidence, open gaps, release state and next action.

## Quality Checklist

Run build and real-browser responsive, accessibility, performance, state and visual gates plus independent quality review.
Structural checks do not prove site quality or compliance.
Production recording requires the complete release-bound launch assessment.
After each authorized deploy, run the production host probe and hand the owner the Search Console steps (launch-contract `production_host`, `search_console`); do not wait for the owner to ask.
Optional measurement after launch or on a preview URL: the `geo-audit` route (AI-citability issues) and the AI-answer panel in repo-root `references/ai-answer-recordings.md`. Report them as observations, never as ranking or citation claims.

- Validation page for a smoke test: apply [validation page](references/validation-page.md) and repo-root `references/smoke-test.md`; use a static single-CTA page with disclosure and no analytics without owner activation.
- When selected marketing work requires an owner action or third-party platform, use repo-root `references/marketing-execution.md` and keep local QA separate from externally verified outcomes.

For selected advertising-event implementation or repair, read repo-root `references/journey-activation-and-measurement.md` (shared repository dependency).
Bind the canonical business occurrence and per-platform mapping to campaign context; verify Meta Pixel eventID/CAPI event_id, Google goal duplication and TikTok Pixel/Events API alignment in the actual selected destinations.
