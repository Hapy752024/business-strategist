#!/usr/bin/env python3
"""Stop hook: block an unvalidated "research delivered" claim.

Behavior: when the last assistant message claims a case or research is
delivered/complete/rerun AND the session checkpoint names a resolvable case
and run, runs the delivery validator. A non-complete result blocks the stop
once. Without a resolvable case/run, an unreadable transcript, or any error,
it allows the stop (the claim cannot be checked; never fail closed).
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from compaction_state import load_state, project_root, resume_path  # noqa: E402

CLAIM = re.compile(r"\b(?:(?:case|research) (?:is|was) (?:fully )?(?:delivered|complete|rerun)|final delivery"
                   r"|delivered the (?:case|research)|(?:(?:case|research) )?rerun (?:is|was) (?:fully )?complete)\b", re.I)
NEGATION = re.compile(r"\b(?:not|never|no longer)\b|n['\u2019]t\b", re.I)
SUFFIX = " Either complete the missing items or restate the result as a progress snapshot."


def claims_delivery(text: str) -> bool:
    """True when a non-negated delivery claim appears (negation within the same sentence, before the phrase)."""
    for match in CLAIM.finditer(text):
        before = re.split(r"[.!?\n]", text[max(0, match.start() - 60):match.start()])[-1]
        if not NEGATION.search(before):
            return True
    return False


def last_assistant_text(transcript_path) -> str:
    try:
        lines = Path(transcript_path).read_text(encoding="utf-8").splitlines()
    except (OSError, TypeError, ValueError):
        return ""
    for line in reversed(lines):
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        message = entry.get("message") if isinstance(entry, dict) else None
        if not isinstance(message, dict) or message.get("role") != "assistant":
            continue
        content = message.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            text = "\n".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text")
            if text.strip():
                return text
    return ""


def resolve_paths(state: dict, root: Path):
    ws = state.get("workspace") or {}
    selection = state.get("active_selection") or {}
    case_id = ws.get("case_id") or selection.get("case")
    run_id = ws.get("run_id") or selection.get("run")
    manifest = ws.get("manifest_path")
    if not (case_id and manifest):
        return None
    manifest_path = root / manifest
    case_root = manifest_path.parent.parent  # <business>/cases/<id>/market_research/manifest.json
    business_root = case_root.parent.parent
    if case_root.name != case_id:
        return None
    if run_id:
        run_dir = case_root / "market_research" / "pain_points" / "runs" / run_id
    else:
        # The route hook records no run; use the case's registered parent run.
        try:
            parent = json.loads(manifest_path.read_text(encoding="utf-8"))["research_assignment"]["parent_run"]
        except (OSError, ValueError, KeyError, TypeError):
            return None
        if not isinstance(parent, str) or not parent:
            return None
        run_dir = (business_root / parent).resolve()
        if not run_dir.is_relative_to(business_root.resolve()):
            return None
    if not run_dir.is_dir():
        return None
    return business_root, run_dir


def stop_delivery_check(event: dict, root: Path) -> dict:
    try:
        if event.get("stop_hook_active"):
            return {}
        if not claims_delivery(last_assistant_text(event.get("transcript_path"))):
            return {}
        session_id = event.get("session_id")
        if not isinstance(session_id, str) or not session_id:
            return {}
        state = load_state(resume_path(root, session_id), session_id)
        resolved = resolve_paths(state, root) if state else None
        if not resolved:
            return {}
        workspace, run_dir = resolved
        done = subprocess.run(
            [sys.executable, str(root / "scripts/evidence_scout/validate_research_completion.py"),
             "--workspace", str(workspace), "--run-dir", str(run_dir), "--check", "delivery", "--json"],
            capture_output=True, text=True, timeout=45, cwd=root)
        if done.returncode == 0:
            return {}
        try:
            result = json.loads(done.stdout)
        except json.JSONDecodeError:
            return {}  # validator crashed: cannot check, do not trap the turn
        missing = "; ".join(str(m) for m in result.get("missing_requirements", [])) or f"delivery status is {result.get('status')}"
        return {"decision": "block", "reason": missing[:600] + "." + SUFFIX}
    except Exception:
        return {}


def main() -> int:
    try:
        event = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, TypeError):
        event = {}
    print(json.dumps(stop_delivery_check(event if isinstance(event, dict) else {}, project_root())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
