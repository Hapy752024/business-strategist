#!/usr/bin/env python3
"""PreCompact hook: save manifest state and current plan before context is rewritten.

Reads session context from stdin, writes current plan state to .claude/plans/resume.json
so PostCompact can restore it. This is the single highest-risk moment for losing the thread.
"""

import json
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RESUME_FILE = ROOT / ".claude" / "plans" / "resume.json"


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def main() -> int:
    try:
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        input_data = {}

    # Collect active workspace state
    active_workspaces: list[dict[str, str]] = []
    topics_dir = ROOT / "research" / "topics"
    if topics_dir.exists():
        for manifest_path in sorted(topics_dir.glob("*/manifest.json")):
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                active_workspaces.append({
                    "slug": manifest_path.parent.name,
                    "current_stage": manifest.get("current_stage", "unknown"),
                    "updated_at": manifest.get("updated_at", ""),
                    "next_action": manifest.get("next_action", ""),
                    "open_blockers": manifest.get("open_blockers", []),
                })
            except (json.JSONDecodeError, OSError):
                continue

    # Collect recent run manifests
    recent_runs: list[dict[str, str]] = []
    for run_manifest_path in sorted(topics_dir.glob("*/**/run-manifest.json")):
        try:
            run = json.loads(run_manifest_path.read_text(encoding="utf-8"))
            recent_runs.append({
                "run_id": run.get("run_id", ""),
                "current_stage": run.get("current_stage", ""),
                "gate_result": run.get("gate_result", "not_run"),
                "next_action": run.get("next_action", ""),
            })
        except (json.JSONDecodeError, OSError):
            continue

    resume_state = {
        "compacted_at": now_iso(),
        "active_workspaces": active_workspaces,
        "recent_runs": recent_runs[-5:],  # Keep last 5
        "session_hint": input_data.get("session_hint", ""),
    }

    RESUME_FILE.parent.mkdir(parents=True, exist_ok=True)
    RESUME_FILE.write_text(json.dumps(resume_state, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    # Return allow — we never block compaction, just save state
    output = {
        "continue": True,
        "hookSpecificOutput": {
            "hookEventName": "PreCompact",
            "message": f"Saved {len(active_workspaces)} workspace(s) and {len(recent_runs)} run(s) to resume file.",
        },
    }
    print(json.dumps(output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())