#!/usr/bin/env python3
"""PostCompact hook: restore run manifest and current checklist after context compaction.

Reads the resume state saved by PreCompact and re-states invariants so the agent
knows where it was before context was rewritten. This is the highest dumb-zone-risk moment.
"""

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RESUME_FILE = ROOT / ".claude" / "plans" / "resume.json"


def main() -> int:
    try:
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        input_data = {}

    resume_state = {}
    if RESUME_FILE.exists():
        try:
            resume_state = json.loads(RESUME_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass

    workspaces = resume_state.get("active_workspaces", [])
    runs = resume_state.get("recent_runs", [])

    # Build restoration message
    lines = ["## Post-Compact Restoration", ""]
    if workspaces:
        lines.append("### Active Workspaces")
        for ws in workspaces:
            lines.append(f"- **{ws['slug']}**: stage `{ws['current_stage']}`, next: {ws['next_action']}")
            if ws.get("open_blockers"):
                for blocker in ws["open_blockers"]:
                    lines.append(f"  - ⚠️ Blocker: {blocker}")
    if runs:
        lines.append("")
        lines.append("### Recent Runs")
        for run in runs[:3]:
            lines.append(f"- `{run['run_id']}`: stage `{run['current_stage']}`, gate: `{run['gate_result']}`")
    if not workspaces and not runs:
        lines.append("No active workspaces or runs to restore.")

    lines.append("")
    lines.append("### Restored Invariants")
    lines.append("- Check `research/topics/<slug>/manifest.json` before resuming any workflow.")
    lines.append("- Do not re-run completed stages unless source data has materially changed.")
    lines.append("- Separate facts, hypotheses, and judgments in all outputs.")
    lines.append("- Ask one question at a time when user input is needed.")

    output = {
        "continue": True,
        "hookSpecificOutput": {
            "hookEventName": "PostCompact",
            "message": "\n".join(lines),
        },
    }
    print(json.dumps(output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())