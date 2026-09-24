#!/usr/bin/env python3
"""Offline audit reproductions; temporary data only, no providers or project writes.

Run from any directory. Prints observations, not a quality-pass certificate.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts/evidence_scout"))
from validate_analysis_eval import summarize
from workspace import _problem_validation_receipt, _receipt_current


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    result = {"purpose": "Adversarial implementation audit; observations are not desired behavior"}
    manifest = json.loads((ROOT / "evals/voc/analysis-eval-manifest.json").read_text())
    result["empty_evaluation"] = summarize({"ratings": []}, manifest)
    rows = []
    for variant in ("A", "B"):
        ratings = {dimension: (4 if variant == "A" else 3) for dimension in manifest["dimensions"]}
        if variant == "A":
            ratings["source_fidelity"] = 1
            ratings["uncertainty"] = 1
        rows.append({"task_id": "not-in-the-manifest", "variant": variant,
                     "critical_failure": False, "ratings": ratings,
                     "rationale": "Synthetic audit input, not an actual evaluated model output."})
    result["unknown_task_and_compensated_fidelity_regression"] = summarize({"ratings": rows}, manifest)

    with tempfile.TemporaryDirectory(prefix="analysis-quality-audit-") as temp:
        root = Path(temp)
        paths = []
        for section in ("customer_segments", "customer_journey", "pain_points"):
            path = root / "market_research" / section / "empty-observation.md"
            path.parent.mkdir(parents=True)
            path.write_text("No customer observations exist. https://example.invalid/source 2026-09-23\n")
            paths.append(path)
        receipt = _problem_validation_receipt(root, paths, case_id="audit", revision=1)
        result["no_customer_observations_receipt"] = {
            "status": receipt["status"],
            "accepted_as_current": _receipt_current(root, {"validation_receipt": receipt}, case_id="audit", revision=1),
            "input_text": paths[0].read_text().strip(),
            "boundary": "Receipt producer and consumer directly; not a full route/stage replay",
        }

        evidence = root / "evidence.jsonl"
        evidence.write_text("")
        review = root / "source-review.json"
        review.write_text(json.dumps({"evidence_sha256": digest(evidence), "target_segment": "audit", "reviews": []}))
        claim_text = "No observed payment behavior is available."
        claim = {"claim_id": "C1", "claim": claim_text, "claim_type": "observation",
                 "confidence": "unresolved", "supporting_evidence": [], "counter_evidence": [],
                 "independence_count": 0, "finding_ids": ["U1"],
                 "none_found_scope": {"sources": ["synthetic empty packet"], "queries": ["audit"],
                                      "geography": "DE", "date_range": "2026-09-23", "failed_routes": []},
                 "verification": {"claim_sha256": hashlib.sha256(claim_text.encode()).hexdigest(),
                                  "evidence_sha256": digest(evidence), "source_review_sha256": digest(review),
                                  "verification_question": "Is payment observed?",
                                  "support_assessment": "unsupported", "rationale": "No observations."}}
        ledger = root / "claim-ledger.json"
        ledger.write_text(json.dumps([claim]))
        synthesis = root / "synthesis.json"
        synthesis.write_text(json.dumps({"status": "supported", "customer_needs": [
            {"id": "U1", "claim_ids": ["C1"], "statement": "Customers repeatedly pay for a replacement."}],
            "solution_requirements": []}))
        completed = subprocess.run([
            sys.executable, "-B", str(ROOT / "scripts/evidence_scout/validate_synthesis.py"),
            "--evidence", str(evidence), "--ledger", str(ledger), "--source-review", str(review),
            "--customer-segment", "audit", "--require-verification", "--synthesis", str(synthesis)
        ], capture_output=True, text=True, check=False)
        result["unsupported_claim_linked_to_positive_finding"] = {
            "exit_code": completed.returncode, "stdout": completed.stdout.strip(), "stderr": completed.stderr.strip(),
            "boundary": "Actual claim-validator CLI; deliberately minimal synthesis, not a schema-valid full VoC pack or discovery-finalizer replay",
        }

    result["source_sha256"] = {name: digest(ROOT / name) for name in (
        "scripts/evidence_scout/workspace.py", "scripts/evidence_scout/validate_synthesis.py",
        "scripts/evidence_scout/discover_market_problems.py", "scripts/validate_analysis_eval.py",
        "evals/voc/analysis-eval-manifest.json")}
    result["reproducer_sha256"] = digest(Path(__file__))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
