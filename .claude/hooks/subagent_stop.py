#!/usr/bin/env python3
"""SubagentStop hook: reject empty subagent output.

Behavior: blocks a subagent result only when the output is empty or shorter
than 20 characters, forcing a re-run. It does not check artifact paths,
structure, sources or factual accuracy; judging content is the coordinator's job.
"""

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def validate_subagent_output(output_text: str) -> dict:
    """Block only empty output; everything else is the coordinator's job to judge."""
    if not output_text or len(output_text.strip()) < 20:
        return {"valid": False, "reason": "Subagent output is empty or too short.", "findings": []}
    return {"valid": True, "reason": "Output present.", "findings": []}


def main() -> int:
    try:
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        input_data = {}

    # Claude's documented hook input uses agent_type and last_assistant_message.
    # Keep the old keys as a harmless compatibility fallback for local harnesses.
    subagent_output = input_data.get("last_assistant_message") or input_data.get("agent_output", "")

    validation = validate_subagent_output(subagent_output)

    if input_data.get("stop_hook_active"):
        print("{}")
        return 0

    if not validation["valid"]:
        output = {"decision": "block", "reason": validation["reason"]}
    else:
        output = {}

    print(json.dumps(output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
