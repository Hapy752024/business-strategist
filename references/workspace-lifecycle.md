# Workspace Lifecycle — Resume, Replay, and Run-Manifest

New projects use the independent subproject layout in [subprojects.md](subprojects.md): `business-analysis/`, `branding/`, `digital-assets/website/`, and `digital-assets/others/`. The umbrella has layout version 3; Business reuses case layout version 2. In the case contract below, root means the Business root for new projects and the existing project root for older version-2 projects. Read [case-assessment.md](case-assessment.md) for its authoritative outputs, selection, publication and recovery contract. Root `project-manifest.json` is the explicit version switch. `README.md` is current comparison/navigation; investigated cases have their own current findings and research stage manifests. The root `strategy/` belongs to the single selected execution target. Case changes do not select an idea. Detect versioned projects even before a root research manifest exists.

Before writes, check `history/pending.json`. Recover through `python3 scripts/case_workspace.py recover --workspace <project>`; do not bypass unresolved or outside-edit conflicts. Case collectors use `--workspace <project> --case <id>` and unique immutable run destinations. The allocator saves the reviewed assessment revision in `.case-context.json`; stage writers require that run context or an explicit `expected_assessment_revision`. A stale run may remain historical evidence but cannot close the current case checkpoint. Direct builders require a fresh path under the case's `market_research/.../runs/`.

Explicit migration: inventory files and links, copy the project, then run `python3 scripts/project_workspace.py migrate-cases <copy> --mapping <mapping.json> --decision-id <id> --reason <scope>`. Mapping is an object keyed by stable case ID; each entry has a title and optional sources (project-relative path, locator, applicability). The helper snapshots previous root outputs, registers cases with no inherited passes and no selection, and switches the root version last. Test interruption/recovery and verify original evidence hashes before any separately authorized live migration.

The remaining layout and legacy stage instructions below apply to unversioned projects. Ordinary legacy research continues without creating cases; new business-linked execution requires migration; standalone branding and website work remain independent. Repository-root `research/` and `brand-projects/` roots are retired. A new unrelated request does not inherit another workspace's active track.

## Legacy layout and stage → folder map

```
projects/<project-slug>/
├── project-manifest.json        # controller: links workstream tracks
├── README.md                    # sole current executive narrative
├── market_research/
│   ├── manifest.json            # research stage machine + events (incl. gate overrides)
│   ├── customer_segments/       # segment_selection output
│   ├── customer_journey/        # customer_profile output
│   ├── pain_points/             # problem_validation output; runs/ = evidence collection
│   ├── pain_point_sizing/
│   ├── solution_alternatives/   # competitor/workaround runs, marketing, ads, landscape
│   ├── market_discovery/runs/   # market_discovery stage runs
│   ├── interviews/
│   └── deep_dives/<topic>/
├── strategy/                    # intake/, canvases/, decisions/, gtm/, playbooks/runs/, risks/, experiments/
├── branding/                    # brand track (brand-manifest.json)
├── marketing/                   # our campaigns
├── web-site/                    # website track (website-manifest.json)
└── digital-assets/
```

Pain-first chain: `intake` → `segment_selection` (writes `customer_segments/`) → `customer_profile` (writes `customer_journey/`) → `problem_validation` (writes `pain_points/` incl. web-searched evidence) → downstream. `problem_validation` may only pass with evidence artifacts under `market_research/pain_points/`; commitment stages (`business_model_draft`, `offer_validation`, `mvp_or_pilot`, `first_customers`, `channel_validation`, `synthesis`) require that gate. `update_stage(..., override="<reason>")` bypasses a gate and records `gate_override:<stage>:<reason>` in the manifest's `events`.

## Purpose

Every research workflow must check for existing project workspaces before creating new ones. Reuse an explicit workspace choice or clear continuation instruction from the conversation; ask only when the target or new-versus-resume intent is unresolved.

Branding and website workflows are independent tracks. Do not run the research-workspace check, market discovery, or idea validation merely because a user asks for a brand or website. When those tracks are requested, inspect only the relevant project/brand manifests:

```bash
ls -d projects/*/project-manifest.json projects/*/branding/brand-manifest.json 2>/dev/null
```

Present matching workspaces with their active track, revision, next action, and blockers. Ask whether to continue the selected workspace or start a new one. A website may consume an explicitly linked, immutable `business-to-brand.json` snapshot; it must not silently read live research files. Brand/website tracks linked to a venture's controller before its pain gate passed are marked `validated: false` in the link and carry an open blocker.

## Checking for Existing Workspaces

Before any research workflow (market-problem-discovery, evidence-scout, idea-grill), run:

```bash
ls -d projects/*/market_research/manifest.json 2>/dev/null
```

If the command returns paths, read each manifest's key fields:

```bash
python3 -c "
import json, pathlib
for p in pathlib.Path('projects').glob('*/market_research/manifest.json'):
    m = json.loads(p.read_text())
    print(f\"{p.parent.parent.name} | stage: {m['current_stage']} | updated: {m['updated_at']} | next: {m['next_action']}\")
"
```

## Presenting Options

When existing workspaces are found and the conversation has not already resolved the choice, present them as numbered options:

```
I found existing research workspaces:

1. <project-slug-1> — stage: <stage>, last updated: <date>
   Next action: <next_action>
2. <project-slug-2> — stage: <stage>, last updated: <date>
   Next action: <next_action>

Which path: continue [1], continue [2], or start new research?
```

Include the `next_action` field so the user knows what they were doing. If `open_blockers` is non-empty, surface those too.

## Resuming a Workspace

When the user chooses to continue a workspace:

1. Read the full `market_research/manifest.json` to understand the current stage and all completed stages.
2. Read the latest artifacts from the completed stages (evidence, competitors, reports).
3. Read the `run-manifest.json` from the most recent run if it exists.
4. Resume from the current stage's `next_action` field. For owner actions apply `references/owner-actions.md`: parse accepted rows from the active track manifest, load their linked details, and reconcile completed/deferred states before proposing work. Optional tasks do not become blockers.
5. Do not re-run completed stages unless the user explicitly asks or source data has materially changed.

## Current executive document

Keep `README.md` as the sole current reader-facing narrative at the project root. It contains the current date/status, founder context, the segment/journey/pain foundation, options and trade-offs, recommendation and evidence strength, acquisition/relationship feasibility, decisive unknowns and next action. A reader should understand the decision without opening an annex. Supporting narratives belong under `market_research/deep_dives/`; source/run outputs and machine state retain their established paths.

README must explicitly cover the current findings, corrections/contradictions, segment and journey hypotheses, solution alternatives, country/segment trade-offs, feasibility/licensing where relevant, researched first-interview recruitment, applied/reused/pending skill coverage, and one next owner decision. Link each substantive conclusion to the relevant dated deep dive or source; links alone do not replace the self-contained synthesis. Pending founder choices and weak evidence must agree with the manifest; generated artifacts are not passed stages.

After substantive follow-ups, update the affected README sections and link directly to relevant evidence or deep dives. Use verified website links for named players; label unavailable addresses. For a material reversal, preserve the previous decision in `strategy/decisions/`, record why the affected assumption changed, and keep README consistent with the current manifest and strategy record. Preserve frozen experiment baselines.

For an explicitly scoped existing-workspace migration, inventory narratives and inbound links first. Save a reversible old-to-new path map, consolidate current conclusions in README, move only supporting narratives, and update relative links and manifest references. Verify every local link/manifest target and unchanged evidence/baseline bytes. Initialization must never overwrite an existing README or silently migrate a workspace. Do not reorganize unrelated projects.

## Per-Run Manifest

Each research run (evidence collection, market discovery, competitor discovery) writes a `run-manifest.json` in its run directory:

```json
{
  "run_id": "<timestamp>-<topic-slug>",
  "subject": "<topic>",
  "run_date": "<ISO timestamp>",
  "run_type": "evidence_collection | market_discovery | competitor_discovery | competitor_marketing | playbook_research",
  "current_stage": "<stage name>",
  "stage_status": "in_progress | passed | failed | conditional_pass",
  "gate_result": "not_run | pass | fail | conditional_pass",
  "artifacts": ["path/to/evidence.jsonl", "path/to/report.md"],
  "sources": ["reddit", "google_trends", "youtube"],
  "open_gaps": ["missing X source", "weak Y signal"],
  "blocked_reason": "",
  "next_action": "Review evidence before synthesis",
  "events": [
    {"ts": "2026-07-18T12:00:00Z", "event": "collection_started"},
    {"ts": "2026-07-18T12:05:00Z", "event": "collection_completed", "record_count": 15}
  ]
}
```

## Replay from Last Passed Gate

A failed or interrupted run should resume from the last passed gate. Do not restart from Stage 0 unless entity identity, scope, or source availability materially changed.

To resume:

1. Read the `run-manifest.json` from the target run directory.
2. Check the `current_stage` and `gate_result`.
3. If `gate_result` is `pass` or `conditional_pass`, proceed to the next stage.
4. If `gate_result` is `fail`, re-attempt the current stage with adjusted parameters.
5. If `gate_result` is `not_run`, start from that stage.

## Project Workspace Cleanup

If the user explicitly says to start fresh and discard existing work, ask for confirmation before deleting anything. Never delete a workspace silently.

## Mode Files

Agent modes (`agent-modes/`) define tool permissions and stop conditions per workflow type. Each mode file governs what tools and scripts are available during that phase of work.
