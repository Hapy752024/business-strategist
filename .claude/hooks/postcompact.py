#!/usr/bin/env python3
"""Persist Claude's compact summary; SessionStart restores it as context."""
import json
import sys

from compaction_state import load_state, project_root, resume_path, write_state


def main() -> int:
    try:
        data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, TypeError):
        data = {}
    session_id = data.get("session_id")
    if not isinstance(session_id, str) or not session_id:
        print("{}")
        return 0
    path = resume_path(project_root(), session_id)
    state = load_state(path, session_id)
    if state is not None:
        state["compact_summary"] = str(data.get("compact_summary", ""))[:12000]
        write_state(path, state)
    print("{}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
