#!/usr/bin/env python3
"""Create minimal structural evals for imported brand skills."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROMPTS = {
    "brand-asset-producer": "Produce an approved logo asset package from the selected brand direction.",
    "brand-designer": "Create a complete brand identity from this brief and route its stages.",
    "brand-discovery-interviewer": "Interview me one question at a time to build a brand brief.",
    "brand-exporter": "Export the approved brand assets and preserve provenance.",
    "brand-frontend-app-designer": "Build a branded product dashboard screen from the approved tokens.",
    "brand-guideline-researcher": "Research brand guideline patterns for this identity.",
    "brand-guidelines-writer": "Write guidelines from the approved brand package.",
    "brand-motion-designer": "Define coherent motion tokens for the approved brand.",
    "brand-quality-reviewer": "Audit this brand package before final delivery.",
    "brand-strategy-director": "Create three evidence-aware brand territories from this brief.",
    "brand-typography-researcher": "Select licensable typography for this brand.",
    "brand-ui-component-producer": "Produce a tested branded button component from the token set.",
    "brand-ui-kit-producer": "Create a branded UI token kit from the approved direction.",
    "brand-workspace-manager": "Create or resume a brand workspace without deleting history.",
    "setup-multiharness-project": "Synchronize the project harness configuration without leaking secrets.",
}


def main() -> int:
    for skill, prompt in PROMPTS.items():
        path = ROOT / ".agents" / "skills" / skill / "evals" / "evals.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            continue
        data = {"skill_name": skill, "evals": [{"id": 1, "prompt": prompt, "expected_output": "Uses the skill workflow, preserves approvals/provenance, and reports artifacts and next action.", "files": []}]}
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"seeded {len(PROMPTS)} brand skill eval files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
