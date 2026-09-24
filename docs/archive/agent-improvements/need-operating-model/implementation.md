# Need, positioning and operating-model implementation

Delivered 17 September 2026 against the existing working tree. Existing research, unrelated edits, skill IDs, stage gates and standalone Branding/Website scope were preserved.

## Changes

- Existing discovery and VOC guidance distinguishes inferred latent need, observed shortfall, adequate service and missing evidence. It requires a competing explanation and disconfirming test without converting complaint counts into demand.
- The shared positioning method connects reviewed needs to a specific promise, customer choice, delivery configuration and a separate benefit/barrier/value-capture assessment.
- Operations selects delivery-design or management-cadence procedure inside the existing `company-operations` route. No new router mode, alias or lifecycle gate was needed. Delivery considers available assets, clean-sheet target, affordable transition, activity interactions and entry-scale economics.
- Startup/risk guidance now consumes the shared method. Removed mandatory moat identification, customer-top-three tests for barriers and categorical B2C/B2B moat assumptions. A viable small business can have no durable moat.
- Optional strategy fields preserve reviewed need locators, per-claim proposition provenance, activity IDs/relationships and scoped defensibility hypotheses. Old plans remain valid. Reinforcement cycles are allowed; unknown activity, test and KPI references fail. Unsupported evidence labels and unsupported `supported` assessments fail declared-support checks.
- Strategy and snapshot validators share positioning validation. Existing publication, source hashes and frozen-baseline logic preserve the extensions and detect subsequent strategy changes. The builder already copied the whole positioning object, so it required no rewrite.

No third-party code was adopted. Existing evidence, publication, strategy and validation components supplied the required mechanics; researched JTBD and operating-model methods informed the guidance. Wardley tooling remains deferred.

## Verification

`bash scripts/validate_setup.sh` passed outside the restricted sandbox: **626 tests passed**, plus offline routing, catalog parity, evaluation structure, schemas and website fixture checks. One pre-existing warning remains: town-db-curator lacks a `Quality Checklist` heading. The first sandbox run's nine browser/socket/child-process failures disappeared on the unrestricted rerun; no unrelated browser code was changed.

Three changed skill entrypoints pass `quick_validate.py`. Python syntax compilation, JSON Schema meta-validation and scoped `git diff --check` passed. Regression tests exercise mixed provenance, legacy plans, reinforcing cycles, bad references, unsupported maturity labels, immutable baselines, strategy publication, snapshot preservation and source freshness.

Twelve synthetic behavioral cases were added to existing discovery, GTM, operations and risk skill eval files. [Inline review](inline-review.md) records the same-session applications and limitations. The six [before/after routing comparisons](route-comparison.json) show unchanged route IDs, owners, modes and required references for selected focused/execution requests. This is deterministic evidence, not a model-quality benchmark.

## Bloat and quality limits

[Surface measurements](surface-check.json): skill count remains **39**; runtime Markdown increased by **582 bytes net** across scoped changes. Entrypoint plus workflow size fell from 10,254 to 6,665 bytes for operations, 17,023 to 16,800 for marketing, and 12,877 to 12,863 for GTM. These are file-size measurements, not measured tokens. Strategic requests conditionally load a larger shared positioning method; cadence-only and narrow-copy requests do not acquire that load by default.

No new skills, runtime references, providers, dependencies, databases, default reports or business stages. The additive schema fields use two reusable definitions in the existing schema. Evaluation artifacts are authoring evidence and are not loaded by runtime skills.

Structure and declared support can be checked automatically; customer fit, economic causality and a real moat cannot. Live cross-harness behavior, independent before/after strategic quality and model token savings remain unverified. No independent agent or headless model run was launched. Full check metadata is in [verification.json](verification.json); pre-task snapshots and the scoped patch are retained under `/tmp/need-operating-model-*` for this session.
