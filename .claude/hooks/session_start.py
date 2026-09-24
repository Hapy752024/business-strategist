#!/usr/bin/env python3
"""Restore a session checkpoint after compaction using SessionStart context."""
import json
import sys

from compaction_state import load_state, project_root, resume_path


def main() -> int:
    try:
        data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, TypeError):
        data = {}
    session_id = data.get("session_id")
    state = load_state(resume_path(project_root(), session_id), session_id) if isinstance(session_id, str) and session_id else None
    if not state:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "No saved checkpoint for this session. Resolve the active request and workspace from current context."}}))
        return 0
    ws = state.get("workspace")
    lines = ["Restored this session's checkpoint after compaction."]
    if ws:
        lines.append(f"Workspace: {ws.get('project_path')} (module={ws.get('module') or 'unspecified'}, case={ws.get('case_id') or 'none'}, run={ws.get('run_id') or 'none'}).")
        lines.append(f"Manifest: {ws.get('manifest_path') or 'not found'}; stage={ws.get('current_stage')}; next action={ws.get('next_action') or 're-resolve from current files'}.")
        manifest_rel = ws.get("manifest_path")
        if manifest_rel:
            import hashlib
            from pathlib import Path
            manifest = project_root() / manifest_rel
            try:
                digest = hashlib.sha256(manifest.read_bytes()).hexdigest()
            except OSError:
                digest = None
            if digest != ws.get("manifest_sha256"):
                lines.append("STALE CHECKPOINT: the selected manifest is missing or changed. Re-read the current manifest and resolve the next action before writing.")
        else:
            lines.append("No manifest was captured; inspect the current workspace before writing.")
        for blocker in ws.get("open_blockers", []):
            lines.append(f"Open blocker: {blocker}")
    if state.get("compact_summary"):
        lines.extend(["", "Compact summary:", state["compact_summary"]])
    if state.get("open_question"):
        lines.extend(["", "Open question:", state["open_question"]])
    if state.get("accepted_decisions"):
        lines.extend(["", "Accepted decisions:"])
        lines.extend(f"- {item}" for item in state["accepted_decisions"])
    if state.get("custom_instructions"):
        lines.extend(["", "Pre-compaction instructions:", state["custom_instructions"]])
    result = {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "\n".join(lines)}}
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
