# Workspace Lifecycle — Resume, Replay, and Run-Manifest

Canonical root is `projects/<project-slug>/` per venture. The research stage machine lives at `projects/<slug>/market_research/manifest.json`; the controller manifest is `projects/<slug>/project-manifest.json`. `_infra` and `_archive` are reserved directory names, not project slugs. Former roots (`research/`, `brand-projects/`, `projects/research/`, `projects/brand-projects/`) are rejected by relocation guards — do not recreate them. Legacy pre-restructure runs live read-only under `projects/_archive/`; preserve frozen evidence paths as historical provenance. Repair only operational links after checking their targets. A new unrelated request does not inherit another workspace's active track.

## Layout and stage → folder map

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
4. Resume from the current stage's `next_action` field.
5. Do not re-run completed stages unless the user explicitly asks or source data has materially changed.

## Current executive document

Keep `README.md` as the sole current reader-facing narrative at the project root. It contains the current date/status, founder context, the segment/journey/pain foundation, options and trade-offs, recommendation and evidence strength, acquisition/relationship feasibility, decisive unknowns and next action. A reader should understand the decision without opening an annex. Supporting narratives belong under `market_research/deep_dives/`; source/run outputs and machine state retain their established paths.

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
