#!/usr/bin/env python3
"""Save a compact, session-scoped workspace checkpoint before compaction."""
import json
import sys
import time
from pathlib import Path

from compaction_state import active_workspace, load_state, project_root, resume_path, write_state


def main() -> int:
    try:
        data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, TypeError):
        data = {}
    session_id = data.get("session_id")
    root = project_root()
    if not isinstance(session_id, str) or not session_id:
        print(json.dumps({"continue": True}))
        return 0
    prior = load_state(resume_path(root, session_id), session_id) or {}
    selection = prior.get('active_selection', {})
    state = {
        "schema_version": 1,
        "session_id": session_id,
        "compacted_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "active_selection": selection,
        "workspace": active_workspace(root, data.get("cwd"),
            selected_project=data.get("selected_project") or selection.get('project'),
            selected_module=data.get("selected_module") or selection.get('module'),
            selected_case=data.get("selected_case") or selection.get('case'),
            selected_run=data.get("selected_run") or selection.get('run')),
        "session_hint": str(data.get("session_hint", ""))[:2000],
        "open_question": str(data.get("open_question") or selection.get('request') or prior.get('open_question', ''))[:1000],
        "accepted_decisions": data.get("accepted_decisions", prior.get("accepted_decisions", [])) if isinstance(data.get("accepted_decisions", prior.get("accepted_decisions", [])), list) else [],
        "custom_instructions": str(data.get("custom_instructions", ""))[:4000],
        "compact_summary": "",
    }
    write_state(resume_path(root, session_id), state)
    print(json.dumps({"continue": True}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
