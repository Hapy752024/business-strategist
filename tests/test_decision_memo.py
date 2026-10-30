import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/evidence_scout/build_decision_memo.py"
spec = importlib.util.spec_from_file_location("build_decision_memo", SCRIPT)
memo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(memo)


def claim(cid, ctype, confidence, n=3, **extra):
    row = {"claim_id": cid, "claim_type": ctype, "claim": f"claim {cid}", "supporting_evidence": ["e1"],
           "counter_evidence": [], "independence_count": n, "confidence": confidence,
           "confidence_rationale": "fixture"}
    row.update(extra)
    return row


def strong_inputs():
    ledger = [claim("p1", "unmetness", "high", 4),
              claim("b1", "willingness_to_pay", "high", 4, price_bearing_behavior_evidence=["e9"]),
              claim("r1", "observation", "high", 4), claim("c1", "observation", "high", 4)]
    factor_claims = {"reachability": [{"claim_id": "r1", "direction": "supports"}],
                     "competition": [{"claim_id": "c1", "direction": "supports"}]}
    economics = {"input_digest": "x", "results": {"status": "conditional", "contribution_per_unit": 40.0,
                 "assumption_inputs": [], "capacity_meets_target": True,
                 "viability": {"status": "pass"}}}
    return ledger, factor_claims, economics


def test_fatal_factor_caps_score():
    ledger, factor_claims, economics = strong_inputs()
    factor_claims["competition"] = [{"claim_id": "c1", "direction": "against"}]  # strong incumbents, high confidence
    result = memo.build(ledger=ledger, factor_claims=factor_claims, economics=economics)
    assert result["factors"]["competition"]["score"] <= 20
    assert result["total"]["score"] <= 20
    assert any("20" in cap for cap in result["total"]["caps_applied"])
    assert result["verdict"] in {"pivot", "stop"}
    assert result["riskiest_assumption"]["factor"] == "competition"


def test_unknown_factor_caps_at_40_and_is_first_next_test():
    ledger, factor_claims, economics = strong_inputs()
    del factor_claims["reachability"]
    result = memo.build(ledger=ledger, factor_claims=factor_claims, economics=economics)
    assert result["factors"]["reachability"]["score"] is None
    assert result["factors"]["reachability"]["band"] == "unknown"
    assert result["total"]["score"] <= 40
    assert result["next_tests"][0]["factor"] == "reachability"
    assert result["riskiest_assumption"]["factor"] == "reachability"
    test = result["riskiest_assumption"]["test"]
    assert test["max_days"] <= 14 and test["cost_cap"] == 100 and test["currency"] == "EUR"
    assert result["kill_criteria"] and all(k["threshold"] for k in result["kill_criteria"])


def test_quarantined_claim_excluded_and_weakened_downgraded(tmp_path):
    ledger, factor_claims, economics = strong_inputs()
    ledger_path = tmp_path / "claim-ledger.json"
    ledger_path.write_text(json.dumps(ledger))
    weakened = dict(ledger[1], confidence="medium")
    sibling = {"schema_version": 1, "source_ledger": str(ledger_path),
               "source_ledger_sha256": hashlib.sha256(ledger_path.read_bytes()).hexdigest(),
               "claims": [weakened, ledger[2], ledger[3]],
               "quarantined": [{"claim": ledger[0], "reason": "falsified", "evidence": []}]}
    (tmp_path / "claim-ledger.falsified.json").write_text(json.dumps(sibling))
    loaded = memo.load_claims(ledger_path)
    result = memo.build(ledger=loaded["claims"], quarantined=loaded["quarantined"],
                        factor_claims=factor_claims, economics=economics)
    pain = result["factors"]["pain"]
    assert pain["score"] is None  # the only pain claim was falsified
    assert "p1" in pain["excluded_quarantined"]
    assert all(b.get("claim_id") != "p1" for f in result["factors"].values() for b in f["basis"])
    assert 51 <= result["factors"]["buyer"]["score"] <= 80  # high -> medium after weakening


def test_quarantine_also_blocks_factor_map_and_assessment_claims():
    ledger, factor_claims, economics = strong_inputs()
    result = memo.build(ledger=ledger, quarantined=[ledger[2]], factor_claims=factor_claims, economics=economics,
                        assessment={"status": "supported", "claim_ids": ["p1", "r1"], "target_segment": "s"})
    assert result["factors"]["reachability"]["score"] is None
    assert "r1" in result["factors"]["reachability"]["excluded_quarantined"]


def test_all_high_warns_about_base_rate(capsys):
    ledger, factor_claims, economics = strong_inputs()
    result = memo.build(ledger=ledger, factor_claims=factor_claims, economics=economics)
    assert all(f["score"] >= 80 for f in result["factors"].values())
    assert any("base rate" in w for w in result["warnings"])
    assert result["verdict"] == "commit"


def test_rubric_band_mapping():
    assert memo.band(None) == "unknown"
    assert memo.band(0) == "0-20" and memo.band(20) == "0-20"
    assert memo.band(21) == "21-50" and memo.band(50) == "21-50"
    assert memo.band(51) == "51-80" and memo.band(80) == "51-80"
    assert memo.band(81) == "81-100" and memo.band(100) == "81-100"
    assert 81 <= memo.claim_score({"confidence": "high", "independence_count": 1}) <= 100
    assert 51 <= memo.claim_score({"confidence": "medium", "independence_count": 9}) <= 80
    assert 21 <= memo.claim_score({"confidence": "low", "independence_count": 0}) <= 50
    assert memo.claim_score({"confidence": "unresolved", "independence_count": 5}) is None
    # Stated willingness without price-bearing behaviour cannot exceed the weak band.
    ledger = [claim("b1", "willingness_to_pay", "high", 4)]
    result = memo.build(ledger=ledger)
    assert result["factors"]["buyer"]["score"] <= 50
    # Economics from the calculator's results fields only.
    econ = lambda **r: memo.build(economics={"results": r})["factors"]["economics"]["score"]
    assert econ(status="unresolved") is None
    assert econ(status="conditional", contribution_per_unit=-1.0, viability={"status": "unresolved"}) <= 20
    assert 21 <= econ(status="conditional", contribution_per_unit=5.0, viability={"status": "unresolved"}) <= 50
    assert 51 <= econ(status="conditional", contribution_per_unit=5.0, assumption_inputs=["revenue_per_unit"],
                      viability={"status": "pass"}) <= 80


def test_multiplicative_total_and_traceable_basis():
    ledger, factor_claims, economics = strong_inputs()
    result = memo.build(ledger=ledger, factor_claims=factor_claims, economics=economics)
    product = 100.0
    for factor in result["factors"].values():
        product *= factor["score"] / 100
        assert factor["basis"] and all(b["artifact"] and b["field"] for b in factor["basis"])
    assert result["total"]["score"] == round(product, 1)
    assert result["verdict_vocabulary"] == "strategy-plan.schema.json#/properties/verdict"


def test_cli_writes_memo_and_scores(tmp_path):
    ledger, factor_claims, economics = strong_inputs()
    paths = {}
    for name, data in (("claim-ledger.json", ledger), ("factor-claims.json", factor_claims), ("economics.json", economics)):
        paths[name] = tmp_path / name
        paths[name].write_text(json.dumps(data))
    out = tmp_path / "memo"
    proc = subprocess.run([sys.executable, str(SCRIPT), "--ledger", str(paths["claim-ledger.json"]),
                           "--factor-claims", str(paths["factor-claims.json"]), "--economics", str(paths["economics.json"]),
                           "--out", str(out), "--cost-cap", "50", "--currency", "USD"], capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    bad = subprocess.run([sys.executable, str(SCRIPT), "--out", str(tmp_path / "x"), "--cost-cap", "50",
                          "--currency", "usd"], capture_output=True, text=True)
    assert bad.returncode == 2 and "schema" in bad.stderr
    scores = json.loads((out / "scores.json").read_text())
    from jsonschema import Draft202012Validator
    schema = json.loads((ROOT / "schemas/decision-memo-scores.schema.json").read_text())
    assert not list(Draft202012Validator(schema).iter_errors(scores))
    assert scores["riskiest_assumption"]["test"]["cost_cap"] == 50
    text = (out / "decision_memo.md").read_text()
    assert text.startswith("# Decision memo") and "Kill criteria" in text and "Verdict" in text
    assert "base rate" in proc.stderr.lower()
