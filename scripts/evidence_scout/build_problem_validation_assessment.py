#!/usr/bin/env python3
"""Bind a human-reviewed problem assessment to current VoC files and findings."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
FILES = ("evidence.jsonl", "source-review.json", "customer-feedback-coverage.json",
         "customer-voc-synthesis.json", "claim-ledger.json", "customer-feedback-source-plan.json")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe_child(root: Path, value: str) -> Path:
    path = (root / value).absolute()
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("assessment inputs must remain inside the workspace")
    cursor = path
    while cursor != root and cursor != cursor.parent:
        if cursor.is_symlink():
            raise ValueError("assessment inputs cannot use symlinked paths")
        cursor = cursor.parent
    return path


def build(args: argparse.Namespace) -> tuple[Path, dict]:
    workspace = Path(args.workspace).expanduser().absolute()
    if not workspace.is_dir():
        raise ValueError("workspace must be an existing directory")
    case_id, revision = args.case_id, args.assessment_revision
    if revision < 1:
        raise ValueError("assessment revision must be positive")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", args.study_id):
        raise ValueError("study ID must be a short path-independent identifier")
    if not re.fullmatch(r"[a-f0-9]{64}", args.research_design_digest):
        raise ValueError("research design digest must be a lowercase SHA-256 digest")

    sections = {
        "customer_segments": args.customer_segments,
        "customer_journey": args.customer_journey,
        "pain_points": args.pain_points,
    }
    section_inputs = {}
    for section, value in sections.items():
        path = safe_child(workspace, value)
        if not path.is_file() or path.stat().st_size == 0:
            raise ValueError(f"{section} artifact must be an existing nonempty file")
        section_inputs[section] = {"path": path.relative_to(workspace).as_posix(), "sha256": digest(path)}

    pack = safe_child(workspace, args.voc_pack)
    if not pack.is_dir():
        raise ValueError("VoC pack must be a workspace-local directory")
    pack_paths = {name: pack / name for name in FILES}
    if any(not path.is_file() or path.is_symlink() for path in pack_paths.values()):
        raise ValueError("VoC pack is missing a required regular file")
    source_plan = json.loads(pack_paths["customer-feedback-source-plan.json"].read_text(encoding="utf-8"))
    source_review = json.loads(pack_paths["source-review.json"].read_text(encoding="utf-8"))
    synthesis = json.loads(pack_paths["customer-voc-synthesis.json"].read_text(encoding="utf-8"))
    if (source_plan.get("study_id") != args.study_id or source_review.get("study_id") != args.study_id
            or synthesis.get("study_id") != args.study_id
            or source_plan.get("research_design_digest") != args.research_design_digest
            or synthesis.get("research_design_digest") != args.research_design_digest
            or source_plan.get("customer_segment") != args.target_segment
            or source_review.get("target_segment") != args.target_segment
            or synthesis.get("topic") != source_plan.get("topic")
            or synthesis.get("schema_version") != 3 or synthesis.get("status") != "supported"):
        raise ValueError("VoC pack must be a supported v3 synthesis for the requested study and customer segment")
    needs = {str(row.get("id")): row for row in synthesis.get("customer_needs", []) if isinstance(row, dict)}
    claims = json.loads(pack_paths["claim-ledger.json"].read_text(encoding="utf-8"))
    known_claims = {str(row.get("claim_id")) for row in claims if isinstance(row, dict)}
    finding_ids = list(dict.fromkeys(args.finding_id))
    claim_ids = list(dict.fromkeys(args.claim_id))
    if not finding_ids or any(ident not in needs for ident in finding_ids):
        raise ValueError("select at least one current customer-need finding ID from the v3 synthesis")
    associated = {str(ident) for finding_id in finding_ids for ident in needs[finding_id].get("claim_ids", [])}
    if not claim_ids or not set(claim_ids) <= associated or not set(claim_ids) <= known_claims:
        raise ValueError("assessment claim IDs must be current claims linked to the selected customer findings")

    common = ["--evidence", str(pack_paths["evidence.jsonl"]), "--source-review", str(pack_paths["source-review.json"]),
              "--coverage", str(pack_paths["customer-feedback-coverage.json"]),
              "--synthesis", str(pack_paths["customer-voc-synthesis.json"]),
              "--study-plan", str(pack_paths["customer-feedback-source-plan.json"]),
              "--customer-segment", args.target_segment]
    commands = [
        [sys.executable, str(ROOT / "scripts/evidence_scout/validate_customer_voc_synthesis.py"), *common],
        [sys.executable, str(ROOT / "scripts/evidence_scout/validate_synthesis.py"),
         "--evidence", str(pack_paths["evidence.jsonl"]), "--ledger", str(pack_paths["claim-ledger.json"]),
         "--source-review", str(pack_paths["source-review.json"]), "--customer-segment", args.target_segment,
         "--require-verification", "--synthesis", str(pack_paths["customer-voc-synthesis.json"])],
    ]
    for command in commands:
        checked = subprocess.run(command, capture_output=True, text=True, check=False)
        if checked.returncode:
            raise ValueError("VoC pack validation failed: " + checked.stdout + checked.stderr)

    assessment = {
        "schema_version": 1, "status": "supported", "intent": args.intent,
        "case_id": case_id, "assessment_revision": revision, "target_segment": args.target_segment,
        "scope": {"geography": args.geography, "limits": args.scope_limits},
        "study_id": args.study_id, "research_design_digest": args.research_design_digest,
        "section_inputs": section_inputs, "voc_pack_path": pack.relative_to(workspace).as_posix(),
        "voc_pack_hashes": {name: digest(path) for name, path in pack_paths.items()},
        "finding_ids": finding_ids, "claim_ids": claim_ids,
        "review": {"reviewer_id": args.reviewer_id, "reviewer_type": args.reviewer_type,
                   "review_mode": args.review_mode, "reviewed_at": args.reviewed_at,
                   "rationale": args.review_rationale},
    }
    schema = json.loads((ROOT / "schemas/problem-validation-assessment.schema.json").read_text())
    from jsonschema import Draft202012Validator
    errors = list(Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER).iter_errors(assessment))
    if errors:
        raise ValueError("problem assessment is invalid: " + errors[0].message)
    destination = workspace / "market_research/pain_points/problem-validation-assessment.json"
    if destination.exists() and not args.replace:
        raise ValueError("problem assessment already exists; use --replace after reviewing the current revision")
    return destination, assessment


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--case-id", default="")
    parser.add_argument("--assessment-revision", required=True, type=int)
    parser.add_argument("--intent", required=True, choices=("customer_problem", "idea_validation"))
    parser.add_argument("--target-segment", required=True)
    parser.add_argument("--geography", required=True)
    parser.add_argument("--scope-limits", required=True)
    parser.add_argument("--study-id", required=True)
    parser.add_argument("--research-design-digest", required=True)
    parser.add_argument("--customer-segments", required=True)
    parser.add_argument("--customer-journey", required=True)
    parser.add_argument("--pain-points", required=True)
    parser.add_argument("--voc-pack", required=True)
    parser.add_argument("--finding-id", action="append", required=True)
    parser.add_argument("--claim-id", action="append", required=True)
    parser.add_argument("--reviewer-id", required=True)
    parser.add_argument("--reviewer-type", required=True, choices=("independent_human", "model"))
    parser.add_argument("--review-mode", required=True, choices=("fresh_context", "independent_review"))
    parser.add_argument("--reviewed-at", required=True, help="ISO 8601 UTC timestamp")
    parser.add_argument("--review-rationale", required=True)
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()
    try:
        destination, assessment = build(args)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        parser.error(str(exc))
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=destination.name + ".", suffix=".tmp", dir=destination.parent)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(assessment, handle, indent=2, sort_keys=True)
        handle.write("\n")
    os.replace(temporary, destination)
    print(json.dumps({"status": "recorded", "assessment": str(destination),
                      "finding_ids": assessment["finding_ids"], "claim_ids": assessment["claim_ids"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
