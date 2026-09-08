# Workspace Lifecycle — Resume, Replay, and Run-Manifest

Canonical roots are `projects/research/topics/` and `projects/brand-projects/`; controller manifests remain `projects/<slug>/project-manifest.json`. Reserve `research` and `brand-projects` as controller slugs. Do not recreate former root-level directories. For an old explicit path, report its relocated equivalent; preserve frozen evidence paths as historical provenance. Repair only operational links after checking their targets. A new unrelated request does not inherit another workspace's active track.

## Purpose

Every research workflow must check for existing topic workspaces before creating new ones. Reuse an explicit workspace choice or clear continuation instruction from the conversation; ask only when the target or new-versus-resume intent is unresolved.

Branding and website workflows are independent tracks. Do not run the research-workspace check, market discovery, or idea validation merely because a user asks for a brand or website. When those tracks are requested, inspect only the relevant project/brand manifests:

```bash
ls -d projects/*/project-manifest.json projects/brand-projects/*/brand-manifest.json 2>/dev/null
```

Present matching workspaces with their active track, revision, next action, and blockers. Ask whether to continue the selected workspace or start a new one. A website may consume an explicitly linked, immutable `business-to-brand.json` snapshot; it must not silently read live research files.

## Checking for Existing Workspaces

Before any research workflow (market-problem-discovery, evidence-scout, idea-grill), run:

```bash
ls -d projects/research/topics/*/manifest.json 2>/dev/null
```

If the command returns paths, read each manifest's key fields:

```bash
python3 -c "
import json, pathlib
for p in pathlib.Path('projects/research/topics').glob('*/manifest.json'):
    m = json.loads(p.read_text())
    print(f\"{p.parent.name} | stage: {m['current_stage']} | updated: {m['updated_at']} | next: {m['next_action']}\")
"
```

## Presenting Options

When existing workspaces are found and the conversation has not already resolved the choice, present them as numbered options:

```
I found existing research workspaces:

1. <topic-slug-1> — stage: <stage>, last updated: <date>
   Next action: <next_action>
2. <topic-slug-2> — stage: <stage>, last updated: <date>
   Next action: <next_action>

Which path: continue [1], continue [2], or start new research?
```

Include the `next_action` field so the user knows what they were doing. If `open_blockers` is non-empty, surface those too.

## Resuming a Workspace

When the user chooses to continue a workspace:

1. Read the full `manifest.json` to understand the current stage and all completed stages.
2. Read the latest artifacts from the completed stages (evidence, competitors, reports).
3. Read the `run-manifest.json` from the most recent run if it exists.
4. Resume from the current stage's `next_action` field.
5. Do not re-run completed stages unless the user explicitly asks or source data has materially changed.

## Current executive document

Keep `README.md` as the sole current reader-facing narrative at the topic root. It contains the current date/status, founder context, options and trade-offs, recommendation and evidence strength, acquisition/relationship feasibility, decisive unknowns and next action. A reader should understand the decision without opening an annex. Supporting narratives belong under `deep-dives/`; source/run outputs and machine state retain their established paths.

After substantive follow-ups, update the affected README sections and link directly to relevant evidence or deep dives. Use verified website links for named players; label unavailable addresses. For a material reversal, preserve the previous decision in `decisions/`, record why the affected assumption changed, and keep README consistent with the current manifest and strategy record. Preserve frozen experiment baselines.

For an explicitly scoped existing-workspace migration, inventory narratives and inbound links first. Save a reversible old-to-new path map, consolidate current conclusions in README, move only supporting narratives, and update relative links and manifest references. Verify every local link/manifest target and unchanged evidence/baseline bytes. Initialization must never overwrite an existing README or silently migrate a workspace. Do not reorganize unrelated topics.

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

## Topic Workspace Cleanup

If the user explicitly says to start fresh and discard existing work, ask for confirmation before deleting anything. Never delete a workspace silently.

## Mode Files

Agent modes (`agent-modes/`) define tool permissions and stop conditions per workflow type. Each mode file governs what tools and scripts are available during that phase of work.
