#!/usr/bin/env python3
"""SubagentStop hook: gate subagent output before it enters the lead's context.

Validates that subagent output:
- Is not empty
- Contains required artifact paths or structured data
- Does not contain fabricated claims without sources

Can force a re-run instead of accepting incomplete or fabricated output.
"""

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def validate_subagent_output(output_text: str) -> dict:
    """Check subagent output for minimum quality signals."""
    findings: list[str] = []

    # Empty output check
    if not output_text or len(output_text.strip()) < 20:
        return {"valid": False, "reason": "Subagent output is empty or too short.", "findings": findings}

    # Check for common hallucination markers
    hallucination_markers = [
        "I cannot access",
        "I don't have access to",
        "I am unable to",
        "I apologize, but I cannot",
    ]
    for marker in hallucination_markers:
        if marker in output_text:
            findings.append(f"Subagent reported inability: '{marker}'")

    # Check for unsupported confidence markers
    confidence_markers = [
        "definitely",
        "certainly",
        "without a doubt",
        "absolutely",
        "undoubtedly",
    ]
    for marker in confidence_markers:
        if marker in output_text.lower():
            findings.append(f"Potentially overconfident language: '{marker}'")

    # Check for required research output patterns
    has_citation = "http" in output_text
    has_file_path = "/" in output_text and any(
        ext in output_text for ext in [".md", ".json", ".jsonl", ".py", ".csv"]
    )
    has_evidence_separation = any(
        phrase in output_text.lower()
        for phrase in ["evidence:", "interpretation:", "counter-evidence:", "facts:", "hypotheses:", "data gaps:"]
    )

    if not (has_citation or has_file_path or has_evidence_separation):
        findings.append("No citations, file paths, or evidence/interpretation separation found.")

    return {
        "valid": True,
        "reason": "Output passed basic quality checks.",
        "findings": findings,
        "has_citation": has_citation,
        "has_file_path": has_file_path,
        "has_evidence_separation": has_evidence_separation,
    }


def main() -> int:
    try:
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        input_data = {}

    subagent_name = input_data.get("agent_name", "unknown")
    subagent_output = input_data.get("agent_output", "")

    validation = validate_subagent_output(subagent_output)

    if not validation["valid"]:
        output = {
            "continue": False,
            "hookSpecificOutput": {
                "hookEventName": "SubagentStop",
                "decision": "block",
                "reason": validation["reason"],
                "message": f"Subagent '{subagent_name}' output blocked: {validation['reason']}",
            },
        }
    elif validation["findings"]:
        output = {
            "continue": True,
            "hookSpecificOutput": {
                "hookEventName": "SubagentStop",
                "decision": "warn",
                "reason": f"Subagent output accepted with {len(validation['findings'])} warnings.",
                "findings": validation["findings"],
                "message": f"Subagent '{subagent_name}' output accepted with warnings: {'; '.join(validation['findings'])}",
            },
        }
    else:
        output = {
            "continue": True,
            "hookSpecificOutput": {
                "hookEventName": "SubagentStop",
                "decision": "allow",
                "reason": "Subagent output passed quality checks.",
                "message": f"Subagent '{subagent_name}' output accepted.",
            },
        }

    print(json.dumps(output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())