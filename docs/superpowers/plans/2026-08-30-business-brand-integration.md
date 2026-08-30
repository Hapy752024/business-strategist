# Business Strategist + Brand Designer Integration Implementation Plan

**Date:** 2026-08-30

**Status:** Proposed implementation plan

**Destination repository:** `/mnt/c/coding/general/business-strategist`

**Source repository:** `/mnt/c/coding/general/brand_designer` at `62fee9b8483ac9c36246d2666c225d599108d925`

**Implementation note (2026-08-30):** Foundation implementation is complete in this repository: the 15 source branding skills are imported with progressive-disclosure wrappers, independent business/brand/website routing and manifests are live, the business-to-brand snapshot and validation path exists, and the preference-led Next.js/FAL/Vercel/A-B website skill scaffolding and offline gates are installed. Remaining items in this document are release-time integrations requiring an explicitly selected GitHub/Vercel target or paid-provider approval.

## 1. Objective

Turn `business-strategist` into one portable, multi-harness business-building system that can:

1. Discover and validate customer problems and business ideas.
2. Build evidence-grounded strategy, GTM, marketing, pilots, and operating plans.
3. Run every current branding skill independently, without requiring business research.
4. Optionally continue from a validated business into a customer-segment-informed brand.
5. Produce approved brand strategy, logos, assets, tokens, motion, components, guidelines, and exports.
6. Art-direct, build, quality-check, experiment on, and optionally deploy a distinctive branded website as the final stage.

The implementation must improve determinism, token efficiency, evidence quality, resumability, and behavioral evaluation. It must not migrate or reinterpret existing research or existing brand-project outputs.

## 2. Locked Product Decisions

These decisions are inputs to implementation, not open design questions:

- Branding has two equally valid entry modes:
  - **Standalone:** start from a user-supplied or interview-built brand brief.
  - **Business-linked:** import a structured snapshot from an existing business workspace.
- Standalone branding must never require market discovery, idea validation, or evidence collection first.
- Completing business validation must not automatically start branding. The agent offers branding as a next path and waits for the user to choose it.
- A business-linked brand reuses confirmed segment, buyer, pain, positioning, offer, objections, trust, geography, and evidence references. It asks only for missing brand-specific decisions.
- All 14 current `brand-*` skills and `setup-multiharness-project` are imported in the first merge. Do not remove or consolidate them during migration.
- Preserve each imported skill's current name. Optimize descriptions only after behavior is stable and baseline comparisons exist.
- Add one new public orchestrator: `business-strategist`.
- Add one new production skill: `brand-website-designer-builder`. It combines preference capture, art direction, production engineering, visual QA, and optional experiment preparation; it is not a generic section-template generator.
- Keep `brand-frontend-app-designer` for product/app screens; do not overload it with marketing-site conversion, SEO, and site-delivery responsibilities.
- The website target is the newest stable Next.js App Router release resolved at scaffold time and pinned exactly in the lockfile. As of 2026-08-30, the official docs report Next.js `16.3.3`; never select a canary/pre-release implicitly.
- The default delivery path is a user-selected GitHub repository connected to Vercel: pull requests create Preview deployments, and the protected production branch creates Production deployments only after approval and gates pass.
- Simple A/B testing is an optional mode of the website skill, implemented with a server-evaluated control/treatment flag and a single declared conversion event. It never activates production traffic or analytics without approval.
- FAL is an optional shared generated-media provider for brand and website assets. It uses `FAL_AI_API_KEY` only from a server/local environment, never browser code, and every paid generation remains budgeted and explicitly confirmed.
- Retain `research/topics/<slug>/` and `brand-projects/<slug>/` as compatible output roots. Do not move historical workspaces automatically.
- External deployment, paid providers, image purchases, package installation, authenticated MCP connections, and writes into another repository require just-in-time user approval.

## 3. Scope Boundaries

### In scope

- Agent/skill architecture and routing.
- Skill import and multi-harness wiring.
- Machine-readable project, handoff, brand-stage, approval, and artifact contracts.
- Research evidence/claim quality improvements.
- Brand workflow consistency and safe asset promotion.
- A new preference-aware website art-direction, Next.js build, GitHub/Vercel delivery, QA, and optional A/B-test workflow.
- Structural, deterministic, behavioral, token, latency, and visual evaluation.
- Backward-compatible handling of existing workspace paths.

### Out of scope

- Reading, modifying, migrating, or reassessing existing research outputs.
- Moving existing `brand-projects/` outputs into this repository.
- Deploying, enabling analytics, or starting a production experiment without just-in-time approval.
- Building authenticated applications, payments, ecommerce, or customer databases as part of the initial webpage skill.
- Installing optional tools or MCPs without approval.
- Deleting or archiving the source repository before acceptance gates pass.

## 4. Preconditions and Safety Gate

Both repositories currently have uncommitted work. Implementation must not begin with an unrecorded copy operation.

### Required preconditions

1. Ask the user how the current changes should be preserved: commit, named patch, or worktree snapshot.
2. Record the destination commit, source commit, dirty file lists, and checksums in `docs/migrations/brand-designer-import-manifest.json`.
3. Preserve the two modified source files explicitly:
   - `.agents/skills/brand-asset-producer/scripts/export-logo-package.py`
   - `.agents/skills/brand-exporter/scripts/create-brand-agent-skill.py`
4. Create a dedicated integration branch after the user-selected preservation step.
5. Capture baseline test, routing, token, duration, and tool-call data before modifying skills.
6. Keep the source repository unchanged until the integrated version passes final acceptance.

### Baseline commands

```bash
PYTHONDONTWRITEBYTECODE=1 bash scripts/validate_setup.sh
PYTHONDONTWRITEBYTECODE=1 python3 scripts/run_evals.py --verbose
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider
```

Run the first two in `business-strategist` and the third in `brand_designer`. Store machine-readable baseline summaries under a gitignored `eval-workspaces/brand-integration/baseline/` directory.

## 5. Target Architecture

```text
User request
   |
   v
business-strategist orchestrator
   |
   +-- business research / validation / strategy track
   |      |
   |      +-- optional business-to-brand.json snapshot
   |
   +-- standalone brand track --------------------------+
   |                                                    |
   +-- business-linked brand track ---------------------+
                                                        v
                                             brand-designer
                                                        |
             discovery -> brand research -> strategy -> assets
                                                        |
                 tokens -> motion -> components -> app screens
                                                        |
              website art direction -> Next.js build -> visual QA
                                                        |
                         optional A/B package -> GitHub/Vercel release
                                                        |
                                             export/guidelines
```

### Control plane

Add a thin project control plane without moving existing track data:

```text
projects/<slug>/
  project-manifest.json        # links active business and brand workspaces

research/topics/<slug>/
  manifest.json                # existing business/research stage truth
  ...

brand-projects/<slug>/
  brand-manifest.json          # brand stage, approval, artifact truth
  website-preferences.json     # versioned user taste and anti-preferences
  website-manifest.json        # stack, concept, build, experiment, release truth
  business-to-brand.json       # optional immutable input snapshot
  stages/                      # working history
  logos/, colors/, ...         # approved canonical delivery
  website/                     # optional built webpage
```

`projects/`, `research/`, `brand-projects/`, and behavioral eval outputs remain gitignored. Schemas, templates, skills, scripts, and fixtures are committed.

### State ownership

- `project-manifest.json` owns links and active-track selection only. It does not duplicate stage details.
- The existing research manifest remains authoritative for business/research stages.
- `brand-manifest.json` is authoritative for requested brand deliverables, stages, approvals, artifacts, and finalization.
- `website-manifest.json` is authoritative for the website preference snapshot, selected concept, exact stack, generated assets, QA, experiment configuration, Git commit, and deployment state.
- Markdown documents are human-readable outputs, not workflow state.
- An explicit snapshot prevents later business-workspace edits from silently changing an approved brand direction.
- The controller/orchestrator is the sole manifest writer. Parallel workers write disjoint artifacts and return result packets; the controller commits state transitions serially.
- Every manifest carries a monotonic `manifest_revision`. Writes use atomic replace plus compare-and-swap against the expected revision; a conflict stops and is resolved explicitly instead of silently applying last-write-wins.
- Workspace links are repository-relative when the target is inside this repository. External targets use a normalized absolute path plus `external: true`; neither form may contain credentials or secret query parameters.

## 6. New and Updated Contracts

### 6.1 `schemas/project-manifest.schema.json`

Required fields:

- `schema_version`, `project_id`, `slug`, `created_at`, `updated_at`.
- `active_track`: `business`, `brand`, `website`, or `none`.
- Optional `business_workspace` and `brand_workspace` paths.
- `links` containing immutable source snapshot IDs rather than copied conclusions.
- `next_action` and `open_blockers`.

### 6.2 `schemas/business-to-brand.schema.json`

Required top-level fields:

- `schema_version`, `snapshot_id`, `created_at`, `source_workspace`, `source_manifest_version`.
- `business_identity`: name, category, offer, geography, language.
- `segment`: customer, buyer/user split, trigger, reachability.
- `job_and_pain`: job, pain, urgency, workaround, alternatives.
- `positioning`: frame of reference, promise, differentiation, reasons to believe.
- `buying_context`: objections, trust requirements, proof, risk, expected decision path.
- `customer_language`: supported phrases with evidence IDs.
- `channels_and_contexts`: where the segment discovers, evaluates, and buys.
- `field_provenance`: status per field: `evidence_backed`, `user_confirmed`, `inference`, `assumption`, or `unresolved`.
- `evidence_refs`, `coverage_gaps`, and `user_overrides`.

Validation rules:

- A missing field does not block standalone branding.
- An integrated workflow may proceed with unresolved fields only when the brand stage does not depend on them or the user confirms an explicit assumption.
- Do not label the whole business “validated.” Preserve confidence per field.

### 6.3 `schemas/brand-manifest.schema.json`

Required fields:

- Project identity and workspace path.
- Entry mode: `standalone` or `business_linked`.
- Requested deliverables and excluded deliverables.
- Current stage and next action.
- Stage states for discovery, research, strategy, logo, color, typography, imagery, tokens, motion, components, frontend app, website, marketing, QA, guidelines, and export.
- Approval records: option ID, approver, timestamp, notes, superseded IDs.
- Artifact records: ID, path, type, stage, status, SHA-256, provenance, license/rights status, source inputs, and generated derivatives.
- Open gaps, accepted residual risks, and completion state.

Completion requirements are scope-aware. A logo-only project must not fail because motion or components were not requested.

An approval exists only when the user states it explicitly or when a previously validated approval record is imported. Agent preference, a high quality score, or lack of objection never counts as approval.

### 6.4 `schemas/claim-record.schema.json`

Each material research claim records:

- `claim_id`, `claim_type`: observation, inference, hypothesis, recommendation.
- Supporting and counter-evidence IDs.
- Independence count and duplicate clusters.
- Geography, segment, freshness, and applicability.
- Confidence and confidence rationale.
- Missing critical sources and the decision affected.

### 6.5 `schemas/website-preferences.schema.json`

Record user taste without pretending inferred style is confirmed preference:

- Preference profile ID, version, locale, and last-confirmed timestamp.
- Brand-locked constraints and their originating brand artifact IDs.
- Visual spectra: restrained/expressive, minimal/layered, editorial/product-led, geometric/organic, warm/cool, polished/raw, static/kinetic, and familiar/experimental.
- Desired content density, typography personality, imagery mode, motion appetite, and accessibility needs.
- Liked references with the specific quality liked; disliked references and anti-patterns with the reason disliked.
- Provenance for every choice: `brand_locked`, `user_stated`, `user_selected`, or `agent_inferred`.

High-impact inferred preferences require confirmation before concept selection. Profiles are project-scoped and never transferred between users implicitly.

### 6.6 `schemas/website-manifest.schema.json`

Required fields:

- Preference profile and approved brand artifact references.
- Exact Next.js, React, Node, package-manager, and lockfile versions plus resolver source and check timestamp.
- Creative territories, selected territory, decision record, signature visual device, and approved variation ID.
- FAL request/model/seed/prompt/hash/provenance records for generated assets.
- Pages, locales, content status, CTA and conversion-event contract.
- Build, accessibility, performance, responsive screenshot, and human visual-review results.
- Optional experiment: hypothesis, single changed variable, control/treatment, allocation, audience, primary metric, guardrails, start/stop rule, status, and cleanup state.
- GitHub repository/branch/commit and Vercel project/environment/deployment URLs; secrets and access tokens are forbidden.

## 7. Implementation Workstreams

### Workstream A — Baseline, import manifest, and dependency hygiene

#### A1. Add migration records

Create:

- `docs/migrations/brand-designer-import-manifest.json`
- `docs/migrations/brand-designer-path-map.md`

The manifest records source commit, dirty-file hashes, included tracked files, exclusions, destination paths, and import status.

#### A2. Import tracked capabilities only

Import:

- `.agents/skills/brand-*`
- `.agents/skills/setup-multiharness-project`
- Brand skill unit/eval fixtures.
- Cross-harness sync script logic that is still needed after adaptation.

Exclude:

- `brand-projects/`
- `.brand-tools/`
- `awesome-design/`
- `other/`
- `.pytest_cache/`, `.firecrawl/`, local settings, caches, secrets, and generated artifacts.

#### A3. Normalize test/dependency setup

Create:

- `requirements-dev.txt` for deterministic test tooling such as pytest.
- `requirements-brand.txt` for optional Pillow, CairoSVG, and PyMuPDF export support.

Update `.github/workflows/validate.yml` to install declared test dependencies rather than relying on runner defaults. Add a separate optional brand-tools job; the core job must not require image-export binaries.

#### A4. Keep every commit green

In the same commit that imports a brand skill:

- Reduce its `SKILL.md` to the destination's entry-file budget.
- Move repeated generic success-criteria prose into a shared reference.
- Add a destination-format `evals/evals.json`.
- Namespace or relocate its tests so discovery remains deterministic.

Do not land an intermediate commit that imports 15 skills while knowingly breaking `validate_setup.sh`.

### Workstream B — Shared orchestration and token-efficient routing

#### B1. Add `business-strategist`

Create:

```text
.agents/skills/business-strategist/
  SKILL.md
  references/workflow.md
  references/routing.md
  evals/evals.json
```

Its job is to determine the minimum useful workflow and hand off to existing specialist skills. It must not re-embed their procedures.

#### B2. Add machine-readable routing

Create:

- `config/skill-catalog.json`
- `config/workflow-routes.json`
- `scripts/route_workflow.py`

Catalog entries define intent, exclusions, prerequisites, artifacts, side-effect class, cost class, and next valid skills. Explicit user intent and active manifest state route deterministically. The model asks one question only when two routes would materially change the work.

Required boundary cases:

- Broad market exploration -> `market-problem-discovery`.
- Specific idea pressure test -> `idea-grill`.
- Direct brand request with no business workspace -> `brand-designer` standalone.
- Brand request with selected business workspace -> offer standalone versus linked snapshot if intent is unclear.
- Completed validation -> offer branding; do not invoke automatically.
- Existing approved brand + marketing/corporate website request -> `brand-website-designer-builder` with a linked brand snapshot.
- Direct website request without a brand workspace -> `brand-website-designer-builder` standalone; capture a compact brand/taste brief rather than forcing research.
- Product/app workflow -> `brand-frontend-app-designer`, not the website skill.
- Competitor website analysis -> competitor skill, not the website skill.
- A/B-test request for an existing site -> the experiment mode of `brand-website-designer-builder`; do not redesign the site unless requested.

#### B3. Compact always-loaded instructions

Update `AGENTS.md` by replacing long skill catalogs and command detail with stable policy and pointers. Do not append the source `AGENTS.md` wholesale. Preserve current uncommitted business instructions through exact-context patches.

Update `references/workspace-lifecycle.md` and the startup check at the same time. Startup discovery must list relevant business, brand, and linked project workspaces according to the user's intent; a brand-only request must not be forced through an unrelated research-workspace prompt. Exact slug matches still require an explicit continue-versus-new decision.

Target:

- `AGENTS.md`: approximately 100-140 lines.
- Each `SKILL.md`: at or below the repository's 30-line budget unless the validator is deliberately revised with evidence.
- Load only the selected workflow and relevant references.

#### B4. Measure routing and context cost

Record:

- Metadata tokens before and after import.
- Selected skill correctness.
- Number of skill/reference files opened per task.
- Total tokens and tool calls for representative workflows.

Do not consolidate imported skills merely to hit an arbitrary token target. Consolidate later only if behavioral data shows that routing collisions or metadata overhead cause material harm.

### Workstream C — Resumable project and brand state

#### C1. Add shared project helper

Create `scripts/project_workspace.py` with:

- Project creation and linking.
- Atomic, revision-checked JSON writes with one controller as the state owner.
- Existing-workspace discovery.
- Cross-track next-action lookup.
- Portable path normalization and validation for internal and external links.
- No automatic deletion or movement of legacy workspaces.

Adapt, but do not break, `scripts/evidence_scout/workspace.py`.

#### C2. Rewrite brand workspace management

Update `brand-workspace-manager` so workspace creation derives folders from requested deliverables and the brand-manifest schema. Its stage list must include motion, components, QA, guidelines, and website where requested.

Add commands for:

- `create`
- `resume`
- `archive-stage`
- `record-option`
- `approve-option`
- `promote --dry-run`

Archiving stays recoverable. Existing canonical files are never overwritten silently.

#### C3. Make promotion approval-aware

Replace whole-directory promotion with artifact-ID promotion:

```bash
python3 <promotion-script> <project-dir> --artifact-id <id> --dry-run
python3 <promotion-script> <project-dir> --artifact-id <id> --confirm
```

The script verifies:

- Artifact status is approved.
- Hash matches the approved record.
- Destination is within the project directory.
- Destination conflicts are reported before writing.
- Superseded/rejected options cannot be promoted.
- Derivative exports link back to the approved source master.

Promotion copies the candidate to a temporary destination, verifies its hash and type there, then atomically replaces the destination only under the recorded conflict policy. A mismatch leaves the canonical artifact unchanged.

### Workstream D — Business research quality and deterministic synthesis

#### D1. Freeze current collector behavior before refactoring

Add characterization tests for existing CLI flags, provider-status outputs, redaction, relevance classification, and path contracts. This protects current uncommitted provider work.

#### D2. Split the 3,814-line collector by responsibility

Create modules under `scripts/evidence_scout/core/`:

- `records.py`
- `normalization.py`
- `relevance.py`
- `source_intent.py`
- `deduplication.py`
- `quality.py`
- `summaries.py`

Keep `collect.py` as the compatible CLI/orchestrator until parity tests pass. Move provider adapters incrementally; do not combine the refactor with semantic scoring changes in one commit.

#### D3. Separate item quality from claim strength

Evidence records gain:

- Stable `evidence_id` and `schema_version`.
- Published and retrieved timestamps.
- Canonical URL and content hash.
- Thread/author/source independence keys with privacy-safe hashing.
- Duplicate cluster ID.
- `signal_quality`: directness, specificity, authenticity confidence, recency, and relevance.

Deprecate per-record `strong` as demand validation. Claim strength is computed only after grouping independent evidence and counter-evidence.

#### D4. Extract domain rules

Move insurance-specific classification from the general collector into a versioned domain rule pack with fixtures. Add a registry that selects a pack only when topic/segment evidence supports it. The default core remains domain-neutral.

#### D5. Add claim ledger and synthesis validator

Create:

- `scripts/evidence_scout/build_claim_ledger.py`
- `scripts/evidence_scout/validate_synthesis.py`
- `schemas/claim-record.schema.json`

The agent may synthesize claims, but finalization is deterministic:

- Every material claim references existing evidence IDs.
- Supporting and counter-evidence are separated.
- Duplicate posts do not count as independent support.
- Provider/editorial/competitor content cannot become customer-pain proof.
- Confidence does not exceed the available independent evidence.
- A no-opportunity result is valid and must not be forced into 3-7 candidates.
- “No counter-evidence found” is valid only with the exact checked scope: sources/providers, queries, geography, date range, and failed routes. It means absence within that scope, never proof that counter-evidence does not exist.

#### D6. Tighten discovery completion gates

Update `discover_market_problems.py` finalization so headings and candidate count are necessary but not sufficient. Require a valid claim ledger and source-coverage summary. Provider failures affect confidence according to whether the source was critical, substitutable, or optional for the decision.

#### D7. Add decision-first stop rules

Research plans record:

- Decision to make.
- Critical claim types.
- Required geography/freshness.
- Source roles and substitutions.
- Budget and paid-provider approvals.
- Stop conditions: sufficient decision confidence, evidence saturation, exhausted approved routes, or user stop.

### Workstream E — Import and repair the complete brand skill set

#### E1. Preserve skill identity and independent use

Import and keep directly invocable:

- `brand-designer`
- `brand-discovery-interviewer`
- `brand-workspace-manager`
- `brand-guideline-researcher`
- `brand-typography-researcher`
- `brand-strategy-director`
- `brand-asset-producer`
- `brand-ui-kit-producer`
- `brand-motion-designer`
- `brand-ui-component-producer`
- `brand-frontend-app-designer`
- `brand-quality-reviewer`
- `brand-exporter`
- `brand-guidelines-writer`
- `setup-multiharness-project`

#### E2. Align every package contract

Make these derive from the same manifest and requested-deliverable set:

- Package structure reference.
- Workspace creation.
- Promotion.
- Audit.
- Finalization gate.
- Exporter.
- Guidelines writer.
- Claude hooks and other harness adapters.

No path may assume the shell is already inside `brand-projects/<name>/`. Resolve the active project explicitly.

#### E3. Capability-specific preflight

Replace the global all-tools preflight with requested capabilities:

- Discovery/strategy: no export or image-generation dependency.
- Logo vector production: SVG tools only.
- Raster/PDF/EPS export: optional brand requirements and system tools.
- Generated imagery: shared provider routing for FAL and the existing OpenRouter path. Prefer no provider until the art direction identifies a concrete asset need; then show model, estimated maximum cost, output count, and retention before confirmation.
- Components/website: Node/package-manager and target stack checks.
- Figma/Storybook/Chromatic: optional, official/trusted, and connected only with approval.

Preflight reports `available`, `optional_missing`, and `blocking_missing` for the requested stage. Missing optional tooling never blocks unrelated work.

#### E4. Adaptive alternatives and bounded iteration

Replace blanket “exactly three alternatives” rules with:

- One implementation for a tightly approved direction.
- Two alternatives for a narrow tradeoff.
- Three alternatives for consequential exploratory choices.

The manifest records the option count and why it was appropriate. Keep the existing three-round maximum unless the user explicitly extends it.

#### E5. Rights and provenance

Every font, image, icon, logo master, and generated derivative records:

- Source URL or generation provider/model.
- Retrieval/generation date.
- License or rights status.
- Preview-only versus approved-for-delivery state.
- File hash and derivative relationship.
- For FAL: endpoint/model ID, request ID, seed where available, exact prompt/negative prompt, dimensions, lifecycle headers, local-download timestamp, and original response hash.

Search visibility and previews are not licenses. Any purchase or paid license remains a separate confirmed action.

#### E6. Add one secure FAL adapter

Create a shared adapter used by `brand-asset-producer` and `brand-website-designer-builder`; do not duplicate provider code inside both skills.

- Accept the repository-standard `FAL_AI_API_KEY` and map it internally to the SDK credential without writing either name or value into generated code, manifests, logs, or browser bundles.
- Default to queue-backed generation for reproducibility and reliability; pin the selected endpoint/model in each generation record.
- Run locally or server-side only. Reject `NEXT_PUBLIC_FAL_*`, client-side credentials, and direct browser calls.
- Before each paid batch, generate a dry-run manifest with requested variants, sizes, model, expected maximum calls/cost, and an approval ID.
- Download approved output immediately into the project, validate MIME/type/dimensions, compute SHA-256, and apply the same promotion workflow as other brand assets.
- Use short media retention and no stored request payload when appropriate. Do not send private customer data, unreleased source assets, faces, or personal data without a separate disclosure and approval.
- If runtime image generation is later requested, route it to a separate security-reviewed server endpoint with authentication, rate limits, abuse controls, spend caps, and lifecycle handling; it is outside the initial website skill.

### Workstream F — Optional business-to-brand continuation

#### F1. Add handoff builder and validator

Create:

- `scripts/brand/build_business_to_brand_handoff.py`
- `scripts/brand/validate_business_to_brand_handoff.py`
- `templates/business-to-brand.json`

The builder reads only the selected business workspace and emits a draft snapshot. It never selects a workspace by latest timestamp across topics. The user reviews unresolved/inferred fields before the brand uses them as constraints.

#### F2. Update `brand-designer` entry behavior

On start:

1. Detect an explicitly supplied brand workspace or handoff.
2. If neither exists, start standalone brand discovery.
3. If a valid handoff exists, summarize imported confirmed constraints and unresolved brand choices.
4. Ask only the first material missing question.
5. Never rerun business research unless the user explicitly asks to refresh or challenge the evidence.

Brand-specific benchmark, reference, font, and license research remains available. It is not business-idea validation.

#### F3. Add provenance-aware strategy rules

`brand-strategy-director` may express confirmed positioning visually. It must not silently convert an inferred differentiation or unresolved customer claim into a brand fact. Territories label which choices come from evidence, user preference, or creative recommendation.

### Workstream G — Add `brand-website-designer-builder`

This skill owns a complete marketing/corporate website outcome: eliciting taste, translating brand strategy into a singular art direction, building the real Next.js site, conducting screenshot-based critique, and preparing an approved GitHub/Vercel release. It stays independently usable when no business or brand workspace exists.

#### G1. Skill structure

Create:

```text
.agents/skills/brand-website-designer-builder/
  SKILL.md
  references/workflow.md
  references/preference-profile.md
  references/creative-direction.md
  references/anti-template-review.md
  references/content-and-conversion.md
  references/fal-assets.md
  references/nextjs-vercel.md
  references/experimentation.md
  references/i18n-and-rtl.md
  references/output-contract.md
  references/qa.md
  scripts/resolve-next-stable.mjs
  scripts/scaffold-site.mjs
  scripts/capture-responsive.mjs
  scripts/validate-site.mjs
  scripts/validate-experiment.mjs
  evals/evals.json
```

Keep `SKILL.md` as a short router. It loads preference/creative references for design, FAL only when generated media is requested, experimentation only for A/B requests, and deployment only after local acceptance.

Draft trigger description:

> Build visually distinctive, production-grade Next.js marketing and corporate websites from an approved brand or a standalone user taste brief. Use whenever the user asks for a landing page, branded website, company site, visually stunning or unique web experience, website redesign, GitHub-to-Vercel delivery, or a simple website A/B test—even if they do not explicitly mention branding.

The website skill coordinates existing specialists instead of copying them: `brand-asset-producer` owns approved visual-asset generation, `brand-typography-researcher` owns font licensing/selection when needed, and `brand-quality-reviewer` performs a fresh final brand/visual audit. The builder owns Next.js code, browser inspection, release packaging, and experiment wiring.

#### G2. Inputs and preference resolution

Inputs:

- Approved brand manifest/assets when available; otherwise a compact standalone brand brief.
- Confirmed customer segment, primary promise, CTA, objections, proof, and required pages when known.
- A versioned `website-preferences.json` containing visual likes, dislikes, spectra, density, imagery, typography, motion, accessibility, and anti-preferences.
- Primary locale, secondary locales, text direction, and translation ownership.
- Legal/privacy requirements supplied by the user; the agent does not invent legal text.
- User-selected GitHub repository and Vercel project only when release is requested.

Ask preference questions only for choices that materially affect the design. If brand outputs answer them, summarize those constraints and ask the user to confirm or override. When the user delegates taste to the agent, label selections `agent_inferred`, explain the rationale, and keep them reversible until the concept gate.

#### G3. Resolve and pin the Next.js stack

- For a new website, resolve the current `next@latest` stable version from the official npm dist-tag and cross-check the official Next.js documentation. Record version, source, and check time; reject canary, RC, beta, or mismatched results.
- As of this plan revision, use Next.js `16.3.3`, App Router, TypeScript, ESLint, Tailwind CSS, and the stable defaults produced by `create-next-app`; implementation must refresh this before scaffolding.
- Pin exact framework/tool versions in the manifest and lockfile. Record the selected Node requirement; the current Next.js docs require Node `20.9+`.
- Follow an existing Next.js target repository's package manager and conventions. If it is not on the resolved stable major, produce a separate migration decision and compatibility test instead of silently upgrading it.
- Default to React Server Components. Add client components only for real interaction. Use framework-native metadata, image, font, script, sitemap, robots, and internationalization primitives where applicable.

#### G4. Use an art-direction funnel, not one-shot generation

1. **Constraint extraction:** freeze brand-locked tokens, customer/CTA hierarchy, accessibility, content, locale, and performance constraints.
2. **Taste model:** capture liked qualities and disliked patterns, not only URLs or vague adjectives.
3. **Territories:** create two or three lightweight concept territories. Each defines one cohesive aesthetic premise, typography role, palette behavior, spatial composition, imagery system, motion moment, and one memorable signature device. Do not build three production sites.
4. **Concept evidence:** render small code-based first-fold or key-section proofs at mobile and desktop. Use FAL for supporting art/texture/imagery when justified, never for final UI text or layout.
5. **Selection:** compare brand fit, preference fit, customer clarity, distinctiveness, accessibility risk, performance feasibility, and implementation cost. Require explicit user selection unless the user delegated selection.
6. **Vertical slice:** build the selected hero/navigation/primary CTA with final tokens and representative assets; capture and critique real browser screenshots before expanding.
7. **Full build:** implement the page system, states, localization, metadata, content, and only the motion that reinforces hierarchy or brand character.
8. **Polish loop:** inspect screenshots and the live page, identify concrete defects, make bounded edits, and preserve diff/revert history. Stop after the acceptance threshold or the agreed iteration budget.

The anti-template review rejects unjustified defaults such as interchangeable gradient-blob heroes, universal bento grids, indiscriminate glass cards, one-radius-everywhere components, generic typography, arbitrary animation, or stock imagery unrelated to the customer context. These patterns remain valid only when the selected direction gives them a specific brand purpose. Originality must never hide the offer, CTA, proof, navigation, or focus state.

#### G5. FAL-assisted visual asset workflow

- Call the shared FAL adapter only after the selected concept identifies an asset role: hero art, illustration family, texture, background plate, iconographic motif, or social card.
- Generate a low-cost contact sheet first, with a fixed brief and recorded seeds/model IDs. Promote only explicitly approved candidates; regenerate a narrow attribute rather than repeatedly rewriting the whole prompt.
- Prefer a consistent image system over unrelated one-off images. Validate crop behavior at real responsive containers and create deliberate mobile/desktop crops when needed.
- Download and optimize approved assets into `public/`; do not hotlink temporary FAL CDN outputs.
- FAL is a build-time creative dependency, not a production-site runtime dependency. `FAL_AI_API_KEY` must never be needed by the deployed website.

#### G6. Initial website and file scope

Support a landing page or small corporate site with responsive navigation/footer, customer-aware content hierarchy, proof, process/features, objections/FAQ, CTA, SEO/social metadata, accessible interaction states, reduced motion, and locale-aware bidirectional layout.

Keep editable source and generated output separate:

```text
website/
  source/                     # Next.js application source
  public/                     # approved, optimized web assets
  tests/                      # behavior/accessibility/experiment checks
  screenshots/                # visual-review evidence
  qa/                         # machine and human QA reports
  .next/                      # generated and gitignored
```

Auth, payments, databases, ecommerce, and CRM submission require separate design/security work. A static contact method or validated no-send form state is the initial default.

#### G7. Optional simple A/B testing

Simple A/B testing is feasible with Vercel Flags, the Flags SDK, and Vercel Web Analytics. Implement it only after the control website passes QA.

- Define one falsifiable hypothesis, one material changed variable, one primary conversion event, guardrails, target audience, allocation, start/end rule, and cleanup owner.
- Use a typed string flag with `control` and `treatment`; evaluate on the server to avoid client flicker and layout shift.
- Emit the evaluated flag value through `FlagValues` and associate it with one approved Web Analytics event. Do not put personal data in event names or properties.
- Verify control and treatment in Preview using flag overrides before any production split.
- Production activation, allocation changes, analytics enablement, and winner rollout require explicit approval. The skill reports results and uncertainty; it does not declare a winner from low traffic or repeated peeking.
- After a decision, remove the losing branch and experiment code, archive the flag, and record the cleanup commit. Default to no more than one active experiment per page.
- Treat the current flag-to-Web-Analytics integration as a beta dependency: preflight current availability/plan limits and retain a no-experiment deployment path.

#### G8. GitHub-to-Vercel release workflow

- Build in a user-selected GitHub repository. CI runs install-from-lockfile, lint, type-check, unit tests, Playwright/accessibility tests, and `next build` before merge.
- Connect the repository to Vercel only after explicit authorization. Pull requests produce Preview deployments; human visual review and acceptance use the immutable Preview URL.
- Protect the production branch. Merge only the accepted commit; let the Vercel Git integration create Production. Do not use direct `vercel --prod` as the default path.
- Store environment values in Vercel project settings, never Git. The initial site should need no FAL key at runtime.
- Record Git commit, Preview URL, QA result, production approval, deployment URL, and rollback target in `website-manifest.json`.
- Roll back through Vercel/Git to the last approved deployment when a post-deploy smoke check fails.

#### G9. Website quality gate

Required before “done”:

- The locked install and production build succeed with no framework security advisory left unresolved.
- Lint and TypeScript pass; no missing local assets, broken internal links, leaked secrets, or unapproved remote image hosts exist.
- Automated accessibility has zero serious/critical findings; keyboard navigation, visible focus, contrast, landmarks, names, and reduced-motion behavior receive manual checks.
- Screenshots are reviewed at 375x812, 390x844, 768x1024, 1440x900, and optionally 1920x1080.
- No horizontal overflow, clipping, cumulative layout shift from media/font sizing, illegible long strings, or accidental visual collisions appear.
- Initial, loading, empty, success, validation-error, provider-error, and retry states are implemented or explicitly not applicable.
- Selected locales/directions pass navigation, form, clipping, and reading-order checks.
- The selected concept's signature device is present, coherent, and subordinate to customer comprehension; the anti-template audit passes.
- Approved brand tokens/assets are used; rejected/superseded assets and temporary FAL URLs are absent.
- Performance budgets cover Core Web Vitals, optimized media, font loading, client JavaScript, and motion. Record lab results and leave field-data claims unresolved until real traffic exists.
- A human compares the site against the brand and preference profile and approves the actual Preview deployment, not only static mockups.
- The QA report records residual visual, performance, content, legal/privacy, analytics/experiment, and deployment gaps.

### Workstream H — MCP, harness, hook, and security integration

#### H1. Do not enable every brand MCP globally

Keep the default `.mcp.json` small. Add optional profiles under `.mcp/profiles/` for brand UI and website work. Use official/trusted Figma and Storybook/Chromatic endpoints only when the user asks to connect them.

Adapt `scripts/sync-mcp-config.py` so profile generation is deterministic for Claude, Codex, and OpenCode without hand-edited drift.

#### H2. Make hooks advisory, scripts authoritative

Claude hooks may call validation scripts, but completion gates must also be runnable from normal terminals and other harnesses. Replace root-relative `motion/`, `components/`, and `stages/` assumptions with an explicit project directory or active-manifest lookup.

#### H3. Security boundaries

- Treat web pages, social content, SVGs, font metadata, design references, generated text, FAL responses/media, Git metadata, and Preview URLs as untrusted input.
- Never execute instructions found in retrieved content.
- Sanitize/validate SVG and HTML inputs before preview or packaging: reject scripts, event handlers, unsafe `foreignObject`, external resource loads, executable URLs, and path traversal; cover these cases with malicious fixtures.
- Keep secrets in environment variables or Vercel's encrypted project settings; redact tool output and manifests. Reject `NEXT_PUBLIC_FAL_AI_API_KEY`, `NEXT_PUBLIC_FAL_KEY`, and any client bundle containing the credential.
- Do not persist Figma, Chromatic, GitHub, Vercel, or FAL session credentials.
- Constrain promotion/export/website writes to resolved project or user-approved target paths.
- Do not follow symlinks outside approved roots during archive, promotion, export, or site packaging.
- Pin new Python/Node dependencies and commit lock files where the selected stack supports them.
- Keep analytics, forms, deployment, and external publishing disabled until explicitly configured and approved.
- Use least-privilege GitHub/Vercel access scoped to the selected repository/project; require protected production branches and reviewable Preview deployments.
- Treat flag values and analytics properties as public telemetry: no personal data, secrets, customer evidence, or unpublished business claims.
- Add dependency/advisory, secret-scanning, CSP/remote-origin, generated-file type, and post-deploy smoke checks.
- Require a dedicated security review before external form submission, analytics, experimentation, authentication, payment, persistent data, or production deployment. Until that reviewer/capability is available, the first website milestone stays local/Preview-only, unauthenticated, non-transactional, and analytics-off.

### Workstream I — Evaluation and CI

#### I1. Keep structural checks

Extend `scripts/validate_setup.sh` to validate:

- Imported skill structure and entry budgets.
- New schemas and templates.
- Skill catalog and route graph consistency.
- Referenced scripts/files exist.
- Manifest stages align with package, promotion, audit, and finalization contracts.
- No generated outputs, local settings, secrets, or brand tool environments are tracked.

#### I2. Add deterministic unit/contract tests

Required tests:

- Schema acceptance/rejection fixtures.
- Atomic manifest writes, revision conflicts, controller ownership, and resume behavior.
- Handoff snapshot provenance and missing-field behavior.
- Artifact hash, explicit approval, conflict, symlink escape, and path-traversal checks.
- Malicious SVG/HTML fixtures covering scripts, event handlers, external loads, and unsafe embedded content.
- Capability-specific preflight.
- Scope-aware finalization.
- Collector parity and claim-ledger validation.
- Website preference provenance, brand-constraint inheritance, and concept-approval behavior.
- Next stable-version resolver: accepts the official stable dist-tag, rejects pre-releases/mismatches, records the exact resolution, and preserves existing-repository compatibility.
- Website build fixture, asset/link/secret validation, form states, i18n/RTL, responsive screenshots, and performance budgets.
- FAL dry-run approval, spend cap, credential redaction, MIME/dimension validation, immediate local download, retention headers, and temporary-URL rejection. Mock provider responses in default CI; live calls are opt-in and spend-approved.
- A/B fixture: typed control/treatment flag, server evaluation, preview override, flag-tagged conversion event, no-PII payload, disabled-by-default production state, and cleanup validation.
- GitHub/Vercel release manifest and rollback fixture without making external deployments in default CI.
- Harness/MCP profile generation.

#### I3. Add behavioral skill evaluation

Create `scripts/run_behavioral_evals.py` or an equivalent adapter around the `skill-creator` workspace format. For changed skills:

1. Snapshot the original skill before editing.
2. Run old and new versions on the same prompt in the same evaluation round.
3. Repeat routing/critical behavior prompts three times.
4. Capture total tokens, duration, and tool calls for every run.
5. Grade objective assertions programmatically.
6. Produce the standard benchmark JSON/Markdown.
7. Generate a static `eval-viewer/generate_review.py` report for human review before accepting the iteration.

Minimum integrated scenarios:

- Standalone brand with no business workspace.
- Validated business handoff into segment-informed branding.
- Incomplete handoff that remains explicit about uncertainty.
- Direct logo-only request that does not require motion/components/website.
- Brand research request that does not trigger business validation.
- Existing approved brand and segment into a distinct landing page.
- Standalone website request captures preferences without forcing business research.
- Two contradictory preference profiles produce intentionally different concepts from the same content while both remain usable.
- An agent-inferred taste direction stays reversible until the user delegates or approves selection.
- App dashboard request routes to frontend-app designer.
- Competitor website analysis does not route to the website skill.
- Paid image/provider request pauses before spend.
- FAL asset generation uses the approved concept and never leaks a key or temporary URL into the site.
- A/B request changes one declared variable and stays off in production until approved.
- GitHub/Vercel request produces Preview first and cannot bypass the production gate.
- Existing project conflict does not overwrite canonical assets.

#### I4. Add screenshot-based visual evaluation

Treat “stunning” and “unique” as reviewable outcomes, not self-declared adjectives:

1. Run the skill and its baseline in the same evaluation round against a balanced set of brand/segment/preference prompts.
2. Capture anonymized full-page mobile and desktop screenshots plus interaction recordings for motion-heavy concepts.
3. Grade objective build, accessibility, performance, content, and provenance assertions programmatically.
4. Run blind pairwise visual review on brand/preference adherence, aesthetic fit, hierarchy, polish, usability, and creative distinction; randomize A/B order.
5. Use human review as the acceptance authority for aesthetic quality. A vision-model score may prioritize issues but cannot approve the design alone.
6. Include a diversity matrix: the same page content under materially different brand/preference profiles should not converge on the same typography, composition, palette behavior, imagery, and signature device.
7. Start with at least 12 representative prompts and three repeated runs for critical routing/constraint behavior; expand the visual set before final rollout if results have high variance.

Record tokens, duration, asset-generation calls/cost, build time, and iteration count. The efficiency target is achieved by narrowing concepts before production coding, not by skipping visual review.

#### I5. CI tiers

- **Every commit:** schemas, unit tests, structural eval validation, route-graph validation, setup checks, no-network website fixture build.
- **Pull request:** locked Next.js install, lint, type-check, tests, `next build`, Playwright/axe, secret scan, asset/link checks, and Vercel Preview when the repository is connected.
- **Manual or scheduled:** LLM behavioral benchmarks, token/latency variance, blind visual reviewer, Lighthouse/field-data follow-up, optional live FAL/tool checks.
- **User acceptance:** human review of representative brand alternatives and the immutable Vercel Preview through the generated eval viewer before production approval.

## 8. Ordered Milestones and Green Commit Strategy

### Milestone 0 — Preserve and baseline

Deliverables:

- User-approved snapshot/commit handling.
- Import manifest with source SHA and dirty hashes.
- Baseline structural, behavioral, token, duration, and tool-call results.

Exit gate: both original repositories reproduce their current offline results.

### Milestone 1 — Shared schemas and project control plane

Deliverables:

- Project, handoff, brand-manifest, website-preference, website-manifest, and claim schemas.
- Templates and schema fixtures.
- Shared atomic project helper.

Exit gate: schema and workspace tests pass; no existing research path changes.

### Milestone 2 — Import all brand skills and tests

Deliverables:

- All 15 source skill folders imported.
- Entry files refactored to destination budgets.
- Brand tests/evals adapted.
- Optional dependencies declared.

Exit gate: `validate_setup.sh`, business tests, and imported brand unit tests pass in the destination.

### Milestone 3 — Routing and independent/integrated entry

Deliverables:

- `business-strategist` orchestrator.
- Skill catalog, route graph, route script, and collision evals.
- Standalone and business-linked brand entry behavior.

Exit gate: routing fixtures pass; no brand request requires business research; validation completion does not auto-start branding.

### Milestone 4 — Brand state, approval, promotion, and contract repair

Deliverables:

- Brand manifest-driven workspace.
- Scope-aware preflight and finalization.
- Approval-aware promotion and archive behavior.
- Package/audit/export/guidelines alignment.
- Rights/provenance records.
- Shared, approval-gated FAL adapter with build-time asset provenance and retention controls.

Exit gate: logo-only and full-brand fixtures both finalize correctly; rejected artifacts cannot be promoted.

### Milestone 5 — Research quality

Deliverables:

- Collector characterization tests and modular core.
- Evidence schema v2 and domain packs.
- Claim ledger and synthesis validator.
- Stronger discovery gate and decision-first stop rules.

Exit gate: no material report claim can pass without traceable evidence/counter-evidence state; legacy CLI fixtures remain compatible.

### Milestone 6 — Distinctive website design and build

Deliverables:

- `brand-website-designer-builder` skill, preference/website manifests, scripts, references, and evals.
- Current-stable Next.js resolver and a pinned App Router fixture.
- Preference interview, creative-territory funnel, anti-template review, FAL asset path, and selected-concept vertical slice.
- Build, type/lint, accessibility, performance, link/asset, locale/RTL, interaction-state, and responsive screenshot QA.

Exit gate: materially different brand/preference fixtures produce coherent, runnable, responsive sites that pass objective QA and blind/human visual review without external deployment or real data submission.

### Milestone 7 — GitHub/Vercel release and optional experiment

Deliverables:

- GitHub CI and Vercel Git-integration runbook with immutable Preview acceptance and protected-production approval.
- Website release/rollback records in the manifest.
- Optional Vercel Flags control/treatment fixture, Preview overrides, Web Analytics event association, and cleanup path.
- Security/privacy review of repository permissions, secrets, deployment, analytics, and experimentation.

Exit gate: the accepted commit can travel GitHub -> Vercel Preview -> approved Production with rollback evidence, and the optional experiment is testable in Preview but off by default in Production.

### Milestone 8 — Behavioral optimization and rollout

Deliverables:

- Old/new evaluation workspaces.
- Trigger-description optimization after workflow quality stabilizes.
- Static human-review viewer and benchmark report.
- Final migration/rollback runbook.

Exit gate: all acceptance metrics below pass and the user approves the representative outputs.

## 9. Acceptance Metrics

### Correctness and routing

- 100% existing deterministic/unit tests pass.
- At least 95% correct routing on a balanced held-out trigger set, repeated three times.
- Zero automatic business research for explicit standalone brand requests.
- Zero automatic branding after business validation without user selection.
- Zero scope-unrequested finalization failures.

### Research quality

- 100% of material report claims have valid claim IDs and evidence references.
- Counter-evidence or an explicit “none found within checked scope” state exists for each decision-critical claim.
- Every “none found within checked scope” state records sources, queries, geography, dates, and retrieval failures.
- Duplicate/cross-posted evidence counts once for independence.
- Provider failures remain coverage gaps, not negative demand evidence.
- Item signal quality is never presented as repeated market validation.

### Brand and webpage quality

- Approved assets have hashes and provenance.
- Rejected/superseded assets cannot appear in canonical delivery or webpage output.
- Required requested deliverables pass manifest-aware QA.
- Website resolves and pins the current stable Next.js release with no implicit pre-release upgrade.
- Website build/type/lint checks pass; no broken local assets/links, temporary FAL URLs, secret leakage, or serious/critical accessibility findings.
- Each accepted site has one coherent creative direction and memorable signature device that pass brand/preference adherence, usability, polish, and creative-distinction review.
- Contrasting brand/preference fixtures do not converge on materially the same composition, typography, palette behavior, imagery, and signature device.
- Responsive screenshots and the immutable Vercel Preview receive human review before production acceptance.
- FAL outputs are cost-approved, locally stored, optimized, hashed, and reproducible to the extent supported by the chosen model.
- When A/B is requested, control/treatment change one declared variable, share one primary metric, work in Preview, and remain disabled in Production until approved.

### Efficiency

- Capture baseline before setting the final target.
- Initial goal: reduce median orchestration tokens/tool calls by at least 25% for comparable workflows without lowering quality scores.
- No skill reads unrelated long references in at least 90% of representative runs.
- Optional MCP/tool checks occur only for requested capabilities.

### Safety

- Zero paid calls, purchases, installs, authenticated connections, deployments, or external writes without required approval.
- Zero secrets in tracked files, raw artifacts, manifests, or eval output.
- Zero writes outside the resolved workspace or explicitly approved target repository.

## 10. Rollback Strategy

- Keep the source repository intact and runnable through Milestone 8.
- Import on a dedicated branch with one green commit per milestone.
- Record imported-source checksums so any file can be compared or restored.
- New manifests use versioned schemas; parsers reject unsupported future major versions and preserve originals.
- Keep existing research workspace functions as compatibility wrappers until new project helpers have parity coverage.
- Website generation defaults to a new directory and refuses non-empty target overwrites without a dry-run and confirmation.
- FAL failure leaves approved local assets untouched; temporary provider URLs are never a release dependency.
- The website can deploy with the control path and analytics/experimentation disabled if Vercel Flags or its analytics integration is unavailable.
- Retain the last approved Git commit and Vercel deployment as the rollback target; a failed smoke test does not advance the website manifest's accepted release.
- If behavioral routing regresses, disable the new top-level orchestrator and retain direct specialist skill invocation while fixes are developed.
- Retire/archive `brand_designer` only after user acceptance; do not delete it as part of the implementation branch.

## 11. Estimated Effort and Critical Path

Indicative single-engineer/agent effort, excluding user review latency and live-provider setup:

| Milestone | Estimate |
|---|---:|
| 0. Preserve and baseline | 1-2 days |
| 1. Schemas/control plane | 2-3 days |
| 2. Import skills/tests | 2-4 days |
| 3. Routing and entry modes | 2-3 days |
| 4. Brand state/contract repair | 3-5 days |
| 5. Research quality/refactor | 5-8 days |
| 6. Distinctive website design/build | 6-10 days |
| 7. GitHub/Vercel release and A/B | 2-4 days |
| 8. Behavioral optimization/rollout | 4-6 days |

Expected total: approximately 27-45 focused implementation days. The critical path is 0 -> 1 -> 2 -> 3 -> 4 -> 6 -> 7 -> 8. Workstream D can begin after Milestone 1 and proceed separately, but it should not be combined with provider-feature work in the same commits.

## 12. Implementation Start Checklist

- [ ] User chooses how to preserve both dirty worktrees.
- [ ] Integration branch created after preservation.
- [ ] Source SHA and dirty file hashes recorded.
- [ ] Existing structural and behavioral baselines captured.
- [ ] New schemas reviewed before workspace scripts are written.
- [ ] Brand import manifest approved.
- [ ] Default versus optional MCP/tool profiles agreed.
- [ ] Website initial scope confirmed as an unauthenticated Next.js landing/corporate site.
- [ ] Website preference profile and concept-selection authority confirmed.
- [ ] FAL model/batch budget and generation approval protocol confirmed; key remains environment-only.
- [ ] User selects the GitHub repository and authorizes Vercel connection before external setup.
- [ ] Analytics/experiment remains off unless hypothesis, metric, privacy review, and production approval are recorded.
- [ ] Each milestone implemented as a green, reviewable commit.
- [ ] Behavioral eval viewer generated before final skill-description optimization.

## 13. Web Research Basis

Research checked on 2026-08-30. Prefer these primary sources during implementation and refresh version/entitlement claims before scaffolding or external setup:

- [Next.js installation](https://nextjs.org/docs/app/getting-started/installation) — reports latest version `16.3.3`, Node `20.9+`, and current `create-next-app` defaults; page last updated 2026-07-21.
- [Next.js 16 release](https://nextjs.org/blog/next-16) — confirms the stable major, App Router-era architecture changes, Turbopack defaults, and agent-facing DevTools MCP; published 2025-10-21.
- [Vercel deployments](https://vercel.com/docs/deployments) — documents GitHub pull-request/commit deployments, unique Preview URLs, and Local/Preview/Production environments; accessed 2026-08-30.
- [Vercel Flags](https://vercel.com/docs/flags) and [running an A/B test](https://vercel.com/docs/flags/vercel-flags/cli/run-ab-test) — document typed variants, production traffic splits, Preview testing, Web Analytics correlation, and cleanup; updated 2026-08-11 and 2026-03-18 respectively.
- [Flags with Vercel Web Analytics](https://vercel.com/docs/flags/observability/web-analytics) and [Vercel Web Analytics](https://vercel.com/docs/analytics) — document flag-tagged events, anonymized/cookie-free visitor measurement, and the current beta status of the flag integration; updated 2026-08-11.
- [FAL authentication](https://fal.ai/docs/documentation/setting-up/authentication), [inference methods](https://fal.ai/docs/documentation/model-apis/inference), and [data retention](https://fal.ai/docs/documentation/model-apis/media-expiration) — support server-side credentials, queue-backed production inference, local copying of generated media, configurable media lifetime, and disabling stored request payloads; accessed 2026-08-30.
- [v0 Design Mode](https://v0.dev/docs/design-mode) and [v0 text prompting](https://v0.dev/docs/text-prompting) — support iterative live-preview editing, before/after comparison, versioned/revertible changes, preference-rich prompts, and incremental implementation; accessed 2026-08-30.
- [Web Vitals](https://web.dev/articles/vitals) and [Cumulative Layout Shift](https://web.dev/articles/cls) — ground the requirement that visually ambitious media, typography, and motion still meet measurable performance and visual-stability budgets; accessed 2026-08-30.
- [Anthropic skills PR #210](https://github.com/anthropics/skills/pull/210) — an unmerged contributor proposal, not official accepted guidance. Its screenshot-based blind A/B evaluation and actionable art-direction framing inform the proposed visual eval methodology, but its instructions are not copied or treated as authoritative.
