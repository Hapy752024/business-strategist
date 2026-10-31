# Website workflow

Existing-site repairs use `references/maintenance.md` without repeating creative selection. Every new site applies `references/launch-contract.md` and executable `references/testing.md`.
Page plans and content briefs draw on keyword-map rows (reviewed, or `keyword-map.proposed.json` marked provisional). Each brief names the inputs supporting it (search study, competitor/similar-company content, customer voice, social discussion) with refs and flags a `single_input` row; the customer and search questions the page must answer; and the SERP features it targets (PAA answers, FAQ blocks, comparison tables, AI-overview-citable summaries with sources). Retain or improve a matched existing page before creating another.

1. Inspect an explicit brand manifest or start a standalone brief. Do not trigger business research automatically.
2. Load/create `website-preferences.json`; separate brand-locked, user-stated, user-selected, and agent-inferred choices. Apply `reference-sites.md`: reuse supplied sites/photos or ask once, inspect actual references, and record accepted inspiration plus per-photo use modes. A user with no references/photos can proceed.
   Before sourcing or generating imagery, apply `../../brand-asset-producer/references/image-sourcing.md`; consume supplied assets and the imagery manifest, including permitted licensed-stock AI references and native imagegen handoff.
3. Resolve the current stable Next.js version with `scripts/resolve-next-stable.mjs`; pin it and the lockfile.
4. Produce two or three lightweight territories (tokens, layout sketch, type, imagery, motion, signature device). Use screenshots or small proofs, not three production builds.
5. Ask for selection unless the user delegated it. Record the decision and rationale in `website-manifest.json`.
6. Build the hero/navigation/primary CTA vertical slice, capture 375px and desktop screenshots, and fix concrete issues.
7. Complete every launch-contract item including Branding favicon handoff, EU consent, analytics, legal/contact inputs and measured performance. Missing owner inputs stay pending.
8. Run `scripts/validate-site.mjs`, Playwright/axe across mobile/tablet/desktop, keyboard and reduced-motion checks, visual review, and the independent `brand-quality-reviewer`.
9. Launch checklist gate: on the served production build, run `python3 -m scripts.brand.site_gate <base-url> --canonical-origin <production-origin> --site-dir <absolute-site-dir>` (evidence: `<absolute-site-dir>/qa/site-gate/`, never the agent repository) (pinned tools: `npm ci` in `scripts/brand`). It checks canonicals/robots/sitemap, `llms.txt` presence, Lighthouse budgets on sitemap URLs (performance ≥ 85, accessibility ≥ 95), Lighthouse agentic-browsing, axe on the top five routes and a DOM subset of the web interface guidelines. Exit 1, `fail` or `tool_unavailable` blocks launch; a `--skip CHECK=REASON` needs a recorded reason, e.g. `--skip agentic_browsing="<reason>"` while that experimental Lighthouse category misjudges the site. Coverage `limits` (such as no usable sitemap) mean the result is not site-wide. Verify with `scripts/brand/check_lighthouse.py <absolute-site-dir>/qa/site-gate/site-gate.json`. After an authorized production deploy only, `scripts/brand/indexnow_ping.py --confirm-deployed` may notify IndexNow.
9a. Verify tracking before launch spend: with analytics enabled on the real site, run `python3 scripts/marketing/verify_tracking.py <tracking-plan.json> --source ga4|posthog` (see `references/marketing-execution.md`, "Verify tracking before launch"); `not_ready` or `unconnected` blocks paid launch, not the site.
10. If requested, run experiment mode from `references/experimentation.md`.
11. Prepare a GitHub PR and Vercel Preview. Do not connect, merge, deploy production, enable analytics, or split traffic without approval.

The reference fixture at `fixtures/website/stellar-repair/` is the executable minimum: pinned stable Next.js, server-evaluated Vercel Flags SDK control/treatment, `FlagValues`, control-only production fallback, Preview-only overrides, axe, keyboard, responsive overflow, and screenshot evidence. Never use client `Math.random()` or `localStorage` for assignment.

## Output

Return the manifest path, selected direction/signature device, stack versions, asset provenance, QA status, Preview URL (if authorized), experiment status, open gaps, and next action.
