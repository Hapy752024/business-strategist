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


EVIDENCE = [{"evidence_id": "er", "evidence_type": "community", "sampling_frame": "topic_led_voc"},
            {"evidence_id": "ec", "evidence_type": "pain", "sampling_frame": "entity_led_feedback"},
            {"evidence_id": "e1", "evidence_type": "pain", "sampling_frame": "topic_led_voc"}]
GATE = {"passed": True, "basis": "fixture manifest receipt"}


def strong_inputs():
    ledger = [claim("p1", "unmetness", "high", 4),
              claim("b1", "willingness_to_pay", "high", 4, price_bearing_behavior_evidence=["e9"]),
              claim("r1", "observation", "high", 4, supporting_evidence=["er"], factor_mapping_reviewed=True),
              claim("c1", "observation", "high", 4, supporting_evidence=["ec"], factor_mapping_reviewed=True,
                    verification={"support_assessment": "supported"})]
    factor_claims = {"reachability": [{"claim_id": "r1", "direction": "supports"}],
                     "competition": [{"claim_id": "c1", "direction": "supports"}]}
    economics = {"input_digest": "x", "results": {"status": "conditional", "contribution_per_unit": 40.0,
                 "assumption_inputs": [], "capacity_meets_target": True,
                 "viability": {"status": "pass"}}}
    return ledger, factor_claims, economics


def test_fatal_factor_caps_score():
    ledger, factor_claims, economics = strong_inputs()
    factor_claims["competition"] = [{"claim_id": "c1", "direction": "against"}]  # strong incumbents, high confidence
    result = memo.build(ledger=ledger, factor_claims=factor_claims, economics=economics, evidence=EVIDENCE)
    assert result["factors"]["competition"]["score"] <= 20
    assert result["total"]["score"] <= 20
    assert any("20" in cap for cap in result["total"]["caps_applied"])
    assert result["verdict"] in {"pivot", "stop"}
    assert result["riskiest_assumption"]["factor"] == "competition"


def test_unknown_factor_caps_at_40_and_is_first_next_test():
    ledger, factor_claims, economics = strong_inputs()
    del factor_claims["reachability"]
    result = memo.build(ledger=ledger, factor_claims=factor_claims, economics=economics, evidence=EVIDENCE)
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
                        factor_claims=factor_claims, economics=economics, evidence=EVIDENCE)
    pain = result["factors"]["pain"]
    assert pain["score"] is None  # the only pain claim was falsified
    assert "p1" in pain["excluded_quarantined"]
    assert all(b.get("claim_id") != "p1" for f in result["factors"].values() for b in f["basis"])
    assert 51 <= result["factors"]["buyer"]["score"] <= 80  # high -> medium after weakening


def test_quarantine_also_blocks_factor_map_and_assessment_claims():
    ledger, factor_claims, economics = strong_inputs()
    result = memo.build(ledger=ledger, quarantined=[ledger[2]], factor_claims=factor_claims, economics=economics, evidence=EVIDENCE,
                        assessment={"status": "supported", "claim_ids": ["p1"], "target_segment": "s"})
    assert result["factors"]["reachability"]["score"] is None
    assert "r1" in result["factors"]["reachability"]["excluded_quarantined"]


def test_all_high_warns_about_base_rate(capsys):
    ledger, factor_claims, economics = strong_inputs()
    result = memo.build(ledger=ledger, factor_claims=factor_claims, economics=economics, evidence=EVIDENCE, gate=GATE)
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
    result = memo.build(ledger=ledger, factor_claims=factor_claims, economics=economics, evidence=EVIDENCE)
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
    (tmp_path / "evidence.jsonl").write_text("\n".join(json.dumps(r) for r in EVIDENCE))
    proc = subprocess.run([sys.executable, str(SCRIPT), "--ledger", str(paths["claim-ledger.json"]),
                           "--evidence", str(tmp_path / "evidence.jsonl"),
                           "--override-gate", "--override-by", "founder", "--override-reason", "accepts pain risk",
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
    assert scores["verdict"] == "commit" and scores["gate"]["override"]["by"] == "founder"
    assert "Pain-first gate: overridden by founder" in text and "geometric mean" in text
    assert "all factors at 80 give 32.8" in text


def test_commit_requires_pain_first_gate():
    ledger, factor_claims, economics = strong_inputs()
    kw = dict(ledger=ledger, factor_claims=factor_claims, economics=economics, evidence=EVIDENCE)
    blocked = memo.build(**kw)
    assert blocked["verdict"] == "test"
    assert any("pain-first gate not passed" in c for c in blocked["total"]["caps_applied"])
    assert memo.build(**kw, gate=GATE)["verdict"] == "commit"
    assessed = memo.build(**kw, assessment={"status": "supported", "claim_ids": ["p1"]})
    assert assessed["verdict"] == "commit" and "assessment" in assessed["gate"]["basis"]
    assert memo.build(**kw, assessment={"status": "scoped", "claim_ids": ["p1"]})["verdict"] == "test"
    overridden = memo.build(**kw, gate={"passed": False, "override": {"by": "founder", "reason": "accepts risk"}})
    assert overridden["verdict"] == "commit" and overridden["gate"]["override"]["by"] == "founder"
    assert "overridden by founder" in memo.render(overridden)


def test_gate_state_reads_router_helper(monkeypatch):
    calls = []
    monkeypatch.setattr(memo, "_pain_gate_state", lambda project, case: calls.append((project, case)) or (True, Path("m.json")))
    gate = memo.gate_from_project("demo", "case-a")
    assert calls == [("demo", "case-a")] and gate["passed"] is True and "m.json" in gate["basis"]


def test_pain_or_buyer_claim_cannot_be_reused_for_other_factor():
    ledger, factor_claims, economics = strong_inputs()
    import pytest
    with pytest.raises(ValueError, match="already scores pain"):
        memo.build(ledger=ledger, evidence=EVIDENCE, factor_claims={"reachability": [{"claim_id": "p1"}]})
    with pytest.raises(ValueError, match="already scores buyer"):
        memo.build(ledger=ledger, evidence=EVIDENCE, factor_claims={"competition": [{"claim_id": "b1"}]})


def test_assigned_claim_must_be_type_compatible():
    import pytest
    ledger = [claim("r1", "recommendation", "high", 4, supporting_evidence=["er"])]
    with pytest.raises(ValueError, match="not compatible"):
        memo.build(ledger=ledger, evidence=EVIDENCE, factor_claims={"reachability": [{"claim_id": "r1"}]})
    # Reachability needs community/channel evidence; competition needs entity-led or competitor evidence.
    ledger = [claim("r1", "observation", "high", 4, supporting_evidence=["e1"], factor_mapping_reviewed=True),
              claim("c1", "observation", "high", 4, supporting_evidence=["e1"], factor_mapping_reviewed=True)]
    result = memo.build(ledger=ledger, evidence=EVIDENCE, factor_claims={"reachability": [{"claim_id": "r1"}],
                                                                         "competition": [{"claim_id": "c1"}]})
    assert result["factors"]["reachability"]["score"] is None and "r1" in result["factors"]["reachability"]["ignored"]
    assert result["factors"]["competition"]["score"] is None
    # Without evidence records the frame cannot be checked: not scored.
    ledger, factor_claims, _ = strong_inputs()
    assert memo.build(ledger=ledger, factor_claims=factor_claims)["factors"]["reachability"]["score"] is None


def test_analyst_only_assignment_capped_at_50_and_marked():
    ledger, factor_claims, economics = strong_inputs()
    for row in ledger:
        row.pop("factor_mapping_reviewed", None)
    result = memo.build(ledger=ledger, factor_claims=factor_claims, economics=economics, evidence=EVIDENCE)
    assert result["factors"]["reachability"]["score"] == 50
    assert result["factors"]["competition"]["score"] == 50
    assert "analyst-assigned" in memo.render(result)


def test_against_claim_counts_only_when_verified_supported():
    ledger, factor_claims, economics = strong_inputs()
    ledger[3].pop("verification")
    factor_claims["competition"] = [{"claim_id": "c1", "direction": "against"}]
    result = memo.build(ledger=ledger, factor_claims=factor_claims, economics=economics, evidence=EVIDENCE)
    assert result["factors"]["competition"]["score"] is None
    assert "c1" in result["factors"]["competition"]["ignored"]


def test_cli_rejects_whitespace_only_override_fields(tmp_path):
    for by, reason in (("founder", "   "), ("  ", "accepts pain risk")):
        proc = subprocess.run([sys.executable, str(SCRIPT), "--override-gate", "--override-by", by,
                               "--override-reason", reason, "--out", str(tmp_path / "memo")],
                              capture_output=True, text=True)
        assert proc.returncode != 0 and "--override-reason" in proc.stderr, (by, reason, proc.stderr)
        assert not (tmp_path / "memo" / "scores.json").exists()


# ---- draft basis and the final-memo claim-challenge rule ----

def _draft(tmp_path, falsified=True):
    d = tmp_path / "draft"
    d.mkdir(parents=True, exist_ok=True)
    rows = [{"claim_id": "D1", "text": "Owners pay for hybrid advice.", "section": "Executive assessment", "sources": []},
            {"claim_id": "D2", "text": "No incumbent offers it.", "section": "Competition", "sources": []}]
    (d / "draft-claims.json").write_text(json.dumps(rows))
    if falsified:
        (d / "draft-claims.falsified.json").write_text(json.dumps({
            "schema_version": 1, "basis": "draft", "claims": [rows[1]],
            "source_ledger_sha256": hashlib.sha256((d / "draft-claims.json").read_bytes()).hexdigest(),
            "quarantined": [{"claim": rows[0], "reason": "falsified", "evidence": []}]}))
    return d / "draft-claims.json"


def _run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True)


def test_draft_basis_memo_is_labelled_and_never_scores_draft_claims(tmp_path):
    out = tmp_path / "memo"
    proc = _run("--draft-claims", _draft(tmp_path), "--out", out)
    assert proc.returncode == 0, proc.stderr
    scores = json.loads((out / "scores.json").read_text())
    assert scores["basis"] == "draft" and scores["claim_challenge"]["basis"] == "draft"
    assert scores["factors"]["pain"]["score"] is None  # draft claims never score
    assert {c["claim_id"]: c["status"] for c in scores["draft_claims"]} == {"D1": "quarantined", "D2": "kept"}
    text = (out / "decision_memo.md").read_text()
    assert text.splitlines()[2].startswith("Basis: draft claims, not ledger-bound")


def test_final_memo_requires_a_claim_challenge_of_either_basis(tmp_path):
    refused = _run("--draft-claims", _draft(tmp_path, falsified=False), "--final", "--out", tmp_path / "m1")
    assert refused.returncode == 2 and "claim challenge" in refused.stderr
    assert not (tmp_path / "m1" / "decision_memo.md").exists()
    refused = _run("--final", "--out", tmp_path / "m0")
    assert refused.returncode == 2 and "claim challenge" in refused.stderr
    ok = _run("--draft-claims", _draft(tmp_path), "--final", "--out", tmp_path / "m2")
    assert ok.returncode == 0, ok.stderr
    assert json.loads((tmp_path / "m2" / "scores.json").read_text())["status"] == "final"


def test_provisional_memo_without_challenge_says_so(tmp_path):
    proc = _run("--out", tmp_path / "m")
    assert proc.returncode == 0, proc.stderr
    scores = json.loads((tmp_path / "m" / "scores.json").read_text())
    assert scores["status"] == "provisional" and scores["claim_challenge"] is None
    assert "Claim challenge: not run" in (tmp_path / "m" / "decision_memo.md").read_text()


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def test_final_refuses_stale_challenge_and_passes_current(tmp_path):
    d = _draft(tmp_path)
    fals = d.parent / "draft-claims.falsified.json"
    data = json.loads(fals.read_text()); data["source_ledger_sha256"] = "0" * 64; fals.write_text(json.dumps(data))
    stale = _run("--draft-claims", d, "--final", "--out", tmp_path / "s")
    assert stale.returncode == 2 and "stale or unrelated to current claims" in stale.stderr
    assert _run("--draft-claims", d, "--out", tmp_path / "p").returncode == 0  # non-final: warning only
    data["source_ledger_sha256"] = _sha(d); fals.write_text(json.dumps(data))
    assert _run("--draft-claims", d, "--final", "--out", tmp_path / "f").returncode == 0
    ledger = tmp_path / "rv" / "claim-ledger.json"
    ledger.parent.mkdir()
    ledger.write_text(json.dumps([claim("p1", "unmetness", "high")]))
    sib = {"schema_version": 1, "basis": "reviewed_ledger", "claims": [], "quarantined": [], "source_ledger_sha256": "1" * 64}
    (ledger.parent / "claim-ledger.falsified.json").write_text(json.dumps(sib))
    stale = _run("--ledger", ledger, "--final", "--out", tmp_path / "r1")
    assert stale.returncode == 2 and "stale" in stale.stderr
    sib["source_ledger_sha256"] = _sha(ledger)
    (ledger.parent / "claim-ledger.falsified.json").write_text(json.dumps(sib))
    assert _run("--ledger", ledger, "--final", "--out", tmp_path / "r2").returncode == 0


def test_falsified_basis_must_match_claims_basis(tmp_path):
    d = _draft(tmp_path)
    reviewed = tmp_path / "reviewed.falsified.json"
    reviewed.write_text(json.dumps({"basis": "reviewed_ledger", "claims": [], "quarantined": []}))
    bad = _run("--draft-claims", d, "--falsified", reviewed, "--out", tmp_path / "x")
    assert bad.returncode == 2 and "does not match draft claims" in bad.stderr
    ledger = tmp_path / "claim-ledger.json"
    ledger.write_text(json.dumps([claim("p1", "unmetness", "high")]))
    bad = _run("--ledger", ledger, "--falsified", d.parent / "draft-claims.falsified.json", "--out", tmp_path / "y")
    assert bad.returncode == 2 and "does not match the reviewed ledger" in bad.stderr


def test_memo_warns_on_claim_challenge_order(tmp_path):
    import os
    # Built before any challenge while draft claims exist.
    d = _draft(tmp_path, falsified=False)
    early = _run("--draft-claims", d, "--out", tmp_path / "early")
    assert early.returncode == 0 and "no claim challenge while draft claims exist" in early.stderr
    # A hand-written challenge beside the memo with nothing applied.
    (tmp_path / "early" / "claim-challenge-draft-basis.md").write_text("# Progress challenge\n")
    again = _run("--draft-claims", d, "--out", tmp_path / "early")
    assert "none was applied to this memo (claim-challenge-draft-basis.md)" in again.stderr
    # Applied challenge, then newer verdicts that were never applied.
    d = _draft(tmp_path)
    current = _run("--draft-claims", d, "--out", tmp_path / "cur")
    assert current.returncode == 0 and "claim challenge" not in current.stderr.lower()
    verdicts = d.parent / "falsification-verdicts.draft.json"
    verdicts.write_text("[]")
    applied = d.parent / "draft-claims.falsified.json"
    os.utime(verdicts, (applied.stat().st_mtime + 60,) * 2)
    stale = _run("--draft-claims", d, "--out", tmp_path / "cur")
    assert stale.returncode == 0 and "newer than the applied challenge (falsification-verdicts.draft.json)" in stale.stderr


def test_memo_order_warning_branches_on_ledger_basis(tmp_path):
    run = tmp_path / "customer-feedback"
    run.mkdir()
    ledger = run / "claim-ledger.json"
    ledger.write_text(json.dumps([claim("p1", "unmetness", "high")]))
    (run / "falsification-claims.json").write_text("{}")  # export output only: precedes the challenge, no warning
    clean = _run("--ledger", ledger, "--out", tmp_path / "m")
    assert clean.returncode == 0 and "claim-challenge file" not in clean.stderr
    assert "no claim challenge while draft claims exist" not in clean.stderr  # no draft claims given
    (run / "falsification-verdicts.json").write_text("[]")  # verdicts saved, apply never run
    unapplied = _run("--ledger", ledger, "--out", tmp_path / "m")
    assert unapplied.returncode == 0
    assert "none was applied to this memo (falsification-verdicts.json)" in unapplied.stderr
