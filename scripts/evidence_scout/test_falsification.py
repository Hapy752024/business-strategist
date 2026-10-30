#!/usr/bin/env python3
"""Adversarial claim falsification: export, untrusted verdict validation and apply."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

import jsonschema
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.evidence_scout import apply_falsification as af  # noqa: E402
from scripts.evidence_scout import export_claims_for_falsification as ex  # noqa: E402

CHECKED_AT = "2026-10-30T12:00:00Z"
SURVIVED = "No disconfirming evidence found within 3 searches."


def claim(claim_id, confidence="medium", **extra):
    row = {
        "claim_id": claim_id,
        "claim_type": "willingness_to_pay",
        "claim": f"Claim {claim_id}: owners pay for monthly bookkeeping help.",
        "supporting_evidence": [f"ev-secret-{claim_id}"],
        "counter_evidence": ["ev-counter-1"],
        "independence_count": 2,
        "confidence": confidence,
        "confidence_rationale": f"SECRET-RATIONALE {claim_id}",
        "geography": "UK",
        "segment": "sole-trader cafes",
        "scope": "UK cafes with 1-5 staff, 2025-2026",
        "decision_affected": "pricing",
        "verification": {"supporting_passages": ["SECRET-PASSAGE"]},
    }
    row.update(extra)
    return row


def evidence(url="https://example.org/survey-2026", quote="Only 12% of cafe owners pay for bookkeeping."):
    return [{"url": url, "date": "2026-05-01", "quote": quote}]


def verdict(claim_id, kind, **extra):
    row = {
        "claim_id": claim_id,
        "verdict": kind,
        "evidence": evidence() if kind in {"falsified", "weakened"} else [],
        "searches_run": ["cafe owners do not pay for bookkeeping", "bookkeeping adoption small hospitality UK"],
        "rationale": SURVIVED if kind == "survived" else "Contrary survey data found.",
    }
    row.update(extra)
    return row


def write(tmp_path, ledger_rows, verdict_rows, budget=3):
    run = tmp_path / "customer-feedback"
    run.mkdir(parents=True, exist_ok=True)
    ledger = run / "claim-ledger.json"
    ledger.write_text(json.dumps(ledger_rows, indent=2) + "\n", encoding="utf-8")
    verdicts = run / "falsification-verdicts.json"
    verdicts.write_text(json.dumps({"schema_version": 1, "search_budget_per_claim": budget, "verdicts": verdict_rows}), encoding="utf-8")
    return ledger, verdicts


def outputs(ledger: Path):
    falsified = json.loads((ledger.parent / "claim-ledger.falsified.json").read_text())
    report = json.loads((ledger.parent / "falsification-report.json").read_text())
    return falsified, report


def test_survived_does_not_upgrade_strength(tmp_path):
    ledger, verdicts = write(tmp_path, [claim("C1", "medium"), claim("C2", "low")],
                             [verdict("C1", "survived"), verdict("C2", "survived")])
    result = af.apply(ledger, verdicts, checked_at=CHECKED_AT)
    falsified, report = outputs(ledger)
    by_id = {row["claim_id"]: row for row in falsified["claims"]}
    assert by_id["C1"]["confidence"] == "medium" and by_id["C2"]["confidence"] == "low"
    assert by_id["C1"]["confidence_rationale"] == "SECRET-RATIONALE C1"
    entries = {row["claim_id"]: row for row in report["claims"]}
    assert entries["C1"]["falsification_checked_at"] == CHECKED_AT
    assert entries["C1"]["confidence_before"] == entries["C1"]["confidence_after"] == "medium"
    assert "no upgrade" in entries["C1"]["action"]
    assert result["counts"]["survived"] == 2


def test_survived_cannot_claim_confirmation(tmp_path):
    ledger, verdicts = write(tmp_path, [claim("C1")], [verdict("C1", "survived", rationale="Confirmed by three sources.")])
    with pytest.raises(af.FalsificationInputError, match="no disconfirming evidence found within"):
        af.apply(ledger, verdicts, checked_at=CHECKED_AT)


def test_falsified_quarantines(tmp_path):
    ledger, verdicts = write(tmp_path, [claim("C1", "high"), claim("C2")], [verdict("C1", "falsified")])
    af.apply(ledger, verdicts, checked_at=CHECKED_AT)
    falsified, report = outputs(ledger)
    assert [row["claim_id"] for row in falsified["claims"]] == ["C2"]
    quarantined = falsified["quarantined"]
    assert len(quarantined) == 1 and quarantined[0]["claim"]["claim_id"] == "C1"
    assert "falsified" in quarantined[0]["reason"] and quarantined[0]["evidence"][0]["url"].startswith("https://")
    entry = {row["claim_id"]: row for row in report["claims"]}["C1"]
    assert entry["action"] == "quarantined" and entry["verdict"] == "falsified"
    assert entry["evidence"][0]["date"] == "2026-05-01"
    assert report["not_checked"] == ["C2"]
    assert (ledger.parent / "falsification-report.md").read_text().count("C1") >= 1


@pytest.mark.parametrize("before,after", [("high", "medium"), ("medium", "low"), ("low", "unresolved"), ("unresolved", "unresolved")])
def test_weakened_downgrades_one_level(tmp_path, before, after):
    ledger, verdicts = write(tmp_path, [claim("C1", before)], [verdict("C1", "weakened")])
    af.apply(ledger, verdicts, checked_at=CHECKED_AT)
    falsified, report = outputs(ledger)
    row = falsified["claims"][0]
    assert row["confidence"] == after
    assert "falsification" in row["confidence_rationale"].lower()
    schema = json.loads((ROOT / "schemas/claim-record.schema.json").read_text())
    checked = {k: v for k, v in row.items() if k != "verification"}  # fixture uses a partial verification stub
    jsonschema.validate(checked, schema)  # publishable rows stay valid claim records
    assert report["claims"][0]["confidence_after"] == after


def test_unknown_claim_id_rejected(tmp_path):
    ledger, verdicts = write(tmp_path, [claim("C1")], [verdict("C9", "survived")])
    with pytest.raises(af.FalsificationInputError, match="unknown claim id.*C9"):
        af.apply(ledger, verdicts, checked_at=CHECKED_AT)
    assert not (ledger.parent / "claim-ledger.falsified.json").exists()


def test_duplicate_verdict_rejected(tmp_path):
    ledger, verdicts = write(tmp_path, [claim("C1")], [verdict("C1", "survived"), verdict("C1", "falsified")])
    with pytest.raises(af.FalsificationInputError, match="duplicate"):
        af.apply(ledger, verdicts, checked_at=CHECKED_AT)


@pytest.mark.parametrize("kind", ["falsified", "weakened"])
def test_falsified_without_evidence_rejected(tmp_path, kind):
    ledger, verdicts = write(tmp_path, [claim("C1")], [verdict("C1", kind, evidence=[])])
    with pytest.raises(af.FalsificationInputError, match="evidence"):
        af.apply(ledger, verdicts, checked_at=CHECKED_AT)


def test_overlong_quote_and_bad_url_rejected(tmp_path):
    ledger, verdicts = write(tmp_path, [claim("C1")], [verdict("C1", "weakened", evidence=evidence(quote="x" * 301))])
    with pytest.raises(af.FalsificationInputError):
        af.apply(ledger, verdicts, checked_at=CHECKED_AT)
    ledger, verdicts = write(tmp_path, [claim("C1")], [verdict("C1", "weakened", evidence=evidence(url="file:///etc/passwd"))])
    with pytest.raises(af.FalsificationInputError):
        af.apply(ledger, verdicts, checked_at=CHECKED_AT)


def test_upgrade_attempt_rejected(tmp_path):
    ledger, verdicts = write(tmp_path, [claim("C1", "medium")], [verdict("C1", "survived", proposed_confidence="high")])
    with pytest.raises(af.FalsificationInputError, match="upgrade"):
        af.apply(ledger, verdicts, checked_at=CHECKED_AT)
    ledger, verdicts = write(tmp_path, [claim("C1", "medium")], [verdict("C1", "survived", confidence="high")])
    with pytest.raises(af.FalsificationInputError):
        af.apply(ledger, verdicts, checked_at=CHECKED_AT)


def test_reviewed_ledger_not_mutated(tmp_path):
    ledger, verdicts = write(tmp_path, [claim("C1", "high"), claim("C2", "high"), claim("C3")],
                             [verdict("C1", "falsified"), verdict("C2", "weakened"), verdict("C3", "survived")])
    before = hashlib.sha256(ledger.read_bytes()).hexdigest()
    result = af.apply(ledger, verdicts, checked_at=CHECKED_AT)
    assert hashlib.sha256(ledger.read_bytes()).hexdigest() == before
    assert result["source_ledger_sha256"] == before
    assert Path(result["outputs"]["ledger"]).name == "claim-ledger.falsified.json"


def test_export_strips_supporting_evidence(tmp_path):
    rows = [claim("C1"), claim("C2", decision_affected="", claim_type="observation"),
            claim("C3", decision_affected="", claim_type="observation", claim_scope_type="prevalence")]
    for row in rows[1:]:
        row.pop("decision_affected")
    ledger = tmp_path / "claim-ledger.json"
    ledger.write_text(json.dumps(rows), encoding="utf-8")
    out = tmp_path / "falsification-claims.json"
    ex.export(ledger, out, search_budget=3)
    text = out.read_text()
    data = json.loads(text)
    assert [row["claim_id"] for row in data["claims"]] == ["C1", "C3"]  # material claims only
    for forbidden in ("supporting_evidence", "counter_evidence", "confidence_rationale", "verification",
                      "SECRET", "ev-secret", "ev-counter", "independence"):
        assert forbidden not in text
    assert data["claims"][0]["geography"] == "UK" and data["search_budget_per_claim"] == 3
    assert set(data["claims"][0]) <= ex.ALLOWED_FIELDS
    everything = ex.export(ledger, out, search_budget=3, material_only=False)
    assert everything["claims"] == 3


def test_verdict_schema_is_valid_and_agent_cannot_read_findings():
    schema = json.loads((ROOT / "schemas/falsification-verdicts.schema.json").read_text())
    jsonschema.Draft202012Validator.check_schema(schema)
    agent = (ROOT / ".claude/agents/claim-falsifier.md").read_text()
    front = agent.split("---")[1]
    tools = re.search(r"^tools:\s*(.+)$", front, re.M).group(1)
    assert "WebSearch" in tools and not re.search(r"\b(Read|Bash|Write|Edit|Grep|Glob)\b", tools)
    assert "no disconfirming evidence found within" in agent.lower()
