#!/usr/bin/env python3
"""Summarise reviewed case artifacts as a decision memo with multiplicative scoring.

Read-only summary layer. It consumes existing reviewed artifacts and writes
`decision_memo.md` + `scores.json`; it never edits them, never publishes case
insights and never authorizes outreach, spend or execution.

Inputs (all optional; a missing input leaves its factors `unknown`):
- claim-ledger.json (reviewed). A `claim-ledger.falsified.json` sibling written by
  apply_falsification.py is applied automatically: quarantined (falsified) claims
  cannot contribute to any factor; weakened claims count at their downgraded confidence.
- problem-validation-assessment.json (pain gate receipt).
- voc-table.json from build_voc_table.py.
- economics.json from scripts/case_economics.py (results are read, never recomputed).
- factor-claims.json: analyst-declared claim -> factor assignments for claims whose
  type does not imply a factor, e.g. {"reachability": [{"claim_id": "c3",
  "direction": "supports"}], "competition": [{"claim_id": "c5", "direction": "against"}]}.
  The assignment is listed in the basis; the score still comes only from the rubric.

Rubric (score 0-100 per factor; higher = more favourable to this entrant; `unknown`
when no eligible evidence exists). Every score is traceable to an artifact field.

Claim score (pain, buyer, reachability, competition), from `confidence` after
falsification and `independence_count` (n):
- 81-100: confidence high      -> 81 + 4*min(n, 4)
- 51-80:  confidence medium    -> 51 + 6*min(n, 4)
- 21-50:  confidence low       -> 21 + 6*min(n, 4)
- 0-20:   evidence against the factor: a claim declared `against`, or a supporting
          claim whose verification.support_assessment is `contradicted`. Against
          claims cap the factor: high -> 10, medium -> 20, low -> 50; contradicted -> 20.
- not scored: confidence `unresolved`, or verification `unsupported`/`unresolved`.
Factor score = min(best supporting claim score, lowest against cap); against-only
evidence scores the cap. Claims count toward a factor when:
- pain: claim_type/claim_scope_type in occurrence|pattern|unmetness|prevalence, or listed
  in the assessment's claim_ids, or declared for pain. VOC-table `need` rows also score:
  row confidence high/medium/low -> the same bands with n = largest frame `sources`;
  rows with 0 supporting sources or tied (finding_ids) to a quarantined claim are skipped.
  Assessment status caps pain: insufficient_evidence -> 50, scoped -> 80, supported -> none.
- buyer: claim_type/claim_scope_type willingness_to_pay, or declared for buyer. A buyer
  claim without `price_bearing_behavior_evidence` (stated intent only) is capped at 50.
- reachability, competition: declared in factor-claims only.
Economics score, from case_economics results:
- unknown: no file, or results.status `unresolved`.
- 0-20:   contribution_per_unit <= 0 -> 10; viability.status `fail` or
          capacity_meets_target false -> 20.
- 21-50:  positive contribution, viability `unresolved` -> 35.
- 51-80:  viability `pass` with any assumption_inputs -> 65.
- 81-100: viability `pass` with no assumption_inputs (all evidence-backed) -> 85.

Total = 100 x product(score/100) over known factors, rounded to 0.1. Caps: any factor
<= 20 caps the total at 20 (one fatal weakness is never averaged away); any unknown
factor caps it at 40 and becomes the first next test.

Verdict uses the existing strategy-plan vocabulary (schemas/strategy-plan.schema.json
verdict enum); the idea-validation pattern maps pursue->commit, test->test,
pivot->pivot, drop->stop:
- stop: pain <= 20, or two or more factors <= 20.
- pivot: exactly one non-pain factor <= 20.
- insufficient_evidence: three or more factors unknown.
- commit: all factors known, none <= 50, total >= 40. A memo `commit` only means the case
  may prepare a commit decision_review; it is not a commitment.
- test: everything else.
Base rate: published idea-validation tools report roughly 17% "go" outcomes, so verdicts
above `test` should be rare. A warning is emitted when every factor is >= 80.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "schemas/decision-memo-scores.schema.json"
FACTORS = ("pain", "buyer", "reachability", "economics", "competition")
PAIN_TYPES = {"occurrence", "pattern", "unmetness", "prevalence"}
BUYER_TYPES = {"willingness_to_pay"}
BANDS = {"high": (81, 4), "medium": (51, 6), "low": (21, 6)}
AGAINST_CAP = {"high": 10, "medium": 20, "low": 50}
CONTRADICTED_CAP = 20
VERDICT_VOCABULARY = "strategy-plan.schema.json#/properties/verdict"
FALSIFIED_NAME = "claim-ledger.falsified.json"
BASE_RATE_WARNING = ("every factor scored >= 80: check for grade inflation; the published base rate "
                     "for a 'go' outcome is roughly 17%, so verdicts above 'test' should be rare")

ASSUMPTIONS = {
    "pain": "The target segment hits this problem recently and painfully enough to act on it.",
    "buyer": "An identifiable buyer already spends money or effort on a workaround and would pay this entrant.",
    "reachability": "The founder can reach qualified target customers through unpaid, repeatable routes.",
    "economics": "Each sale contributes positive margin at a price buyers accept, within founder cash limits.",
    "competition": "Target customers are not well served by an existing option they would refuse to switch from.",
}
TESTS = {
    "pain": ("Run 10 unpaid problem interviews with screened target customers about their last occurrence "
             "(no pitch, past behaviour only).",
             "Fewer than 3 of 10 screened target customers describe an occurrence in the last 90 days "
             "with a concrete consequence."),
    "buyer": ("Ask 10 screened target customers what they paid or spent on the current workaround in the "
              "last 12 months and who approved it.",
              "Fewer than 2 of 10 report past spend or budget on a workaround, or no buyer with authority is named."),
    "reachability": ("Recruit through at most 2 unpaid channels found in the research (communities, "
                     "referrals, direct outreach) for 14 days.",
                     "Fewer than 10 qualified target-segment responses within 14 days."),
    "economics": ("Collect actual price points and delivery time from 5 comparable offers or interviews "
                  "and rerun case_economics with them.",
                  "Contribution per unit <= 0 at the median observed price, or the viability check fails."),
    "competition": ("Ask 10 screened target customers which option they use now, what it fails at and what "
                    "would make them switch.",
                    "7 or more of 10 name a current option they are satisfied with and would not switch from."),
}


def band(score: float | None) -> str:
    if score is None:
        return "unknown"
    if score <= 20:
        return "0-20"
    if score <= 50:
        return "21-50"
    if score <= 80:
        return "51-80"
    return "81-100"


def claim_score(row: dict) -> int | None:
    """Supporting-claim score from confidence and independence_count (rubric above)."""
    conf = row.get("confidence")
    if conf not in BANDS:
        return None
    base, step = BANDS[conf]
    n = row.get("independence_count") if isinstance(row.get("independence_count"), int) else 0
    return base + step * min(max(n, 0), 4)


def _support_state(row: dict) -> str | None:
    verification = row.get("verification")
    return verification.get("support_assessment") if isinstance(verification, dict) else None


def load_claims(ledger_path: Path, falsified_path: Path | None = None) -> dict:
    """Read a reviewed ledger and apply its falsification sibling when present."""
    ledger_path = Path(ledger_path)
    rows = json.loads(ledger_path.read_text(encoding="utf-8"))
    if not isinstance(rows, list) or not all(isinstance(r, dict) and r.get("claim_id") for r in rows):
        raise ValueError(f"{ledger_path}: claim ledger must be a JSON array of records with claim_id")
    falsified_path = Path(falsified_path) if falsified_path else ledger_path.parent / FALSIFIED_NAME
    out = {"claims": rows, "quarantined": [], "warnings": [], "falsification": None}
    if not falsified_path.is_file():
        return out
    data = json.loads(falsified_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("quarantined"), list) or not isinstance(data.get("claims"), list):
        raise ValueError(f"{falsified_path}: malformed; re-run apply_falsification.py")
    quarantined = [q.get("claim", {}) for q in data["quarantined"] if isinstance(q, dict)]
    downgraded = {str(r.get("claim_id")): r for r in data["claims"] if isinstance(r, dict)}
    order = list(BANDS)[::-1]  # low, medium, high
    rank = lambda c: order.index(c) if c in order else -1
    merged = []
    for row in rows:
        other = downgraded.get(str(row["claim_id"]))
        if other is not None and rank(other.get("confidence")) < rank(row.get("confidence")):
            row = dict(row, confidence=other.get("confidence"))
        merged.append(row)
    digest = hashlib.sha256(ledger_path.read_bytes()).hexdigest()
    if data.get("source_ledger_sha256") not in (None, digest):
        out["warnings"].append("falsification was run on an earlier ledger revision; quarantine and downgrades "
                               "still applied, rerun apply_falsification.py")
    out.update(claims=merged, quarantined=quarantined,
               falsification={"path": str(falsified_path), "quarantined": len(quarantined)})
    return out


def _types(row: dict) -> set:
    return {row.get("claim_type"), row.get("claim_scope_type")}


def _claim_factor(name: str, rows: list[tuple[dict, str, str]], quarantined: set, artifact: str) -> dict:
    """Score one claim-based factor from (row, direction, why_assigned) tuples."""
    basis, ignored, excluded, supports, caps = [], [], [], [], []
    seen = set()
    for row, direction, why in rows:
        cid = str(row.get("claim_id"))
        if (cid, direction) in seen:
            continue
        seen.add((cid, direction))
        if cid in quarantined:
            excluded.append(cid)
            continue
        state = _support_state(row)
        conf = row.get("confidence")
        entry = {"artifact": artifact, "field": f"claim_id={cid}.confidence", "claim_id": cid,
                 "confidence": conf, "direction": direction, "assigned_by": why}
        if direction == "against":
            if conf not in AGAINST_CAP:
                ignored.append(cid)
                continue
            caps.append(AGAINST_CAP[conf]); entry["cap"] = AGAINST_CAP[conf]
        elif state == "contradicted":
            caps.append(CONTRADICTED_CAP); entry.update(cap=CONTRADICTED_CAP, field=f"claim_id={cid}.verification.support_assessment")
        elif state in {"unsupported", "unresolved"} or claim_score(row) is None:
            ignored.append(cid)
            continue
        else:
            score = claim_score(row)
            if name == "buyer" and score > 50 and not row.get("price_bearing_behavior_evidence"):
                score = 50
                entry["note"] = "stated intent only (no price_bearing_behavior_evidence): capped at 50"
            supports.append(score); entry["score"] = score
        basis.append(entry)
    return {"supports": supports, "caps": caps, "basis": basis, "ignored": ignored, "excluded": excluded}


def _voc_pain(voc_table: dict, quarantined_findings: set) -> dict:
    supports, basis, skipped = [], [], []
    for row in voc_table.get("rows", []) or []:
        if row.get("kind") != "need":
            continue
        rid = str(row.get("id"))
        n = max((f.get("sources", 0) for f in (row.get("frames") or {}).values()), default=0)
        if rid in quarantined_findings or n == 0:
            skipped.append(rid)
            continue
        score = claim_score({"confidence": row.get("confidence"), "independence_count": n})
        if score is None:
            skipped.append(rid)
            continue
        supports.append(score)
        basis.append({"artifact": "voc-table.json", "field": f"rows[id={rid}].confidence", "row_id": rid,
                      "confidence": row.get("confidence"), "sources": n, "score": score})
    return {"supports": supports, "basis": basis, "skipped": skipped}


def _economics(economics: dict | None) -> dict:
    if not economics:
        return {"score": None, "basis": [], "reason": "no case_economics output supplied"}
    res = economics.get("results") or {}
    field = lambda f: {"artifact": "economics.json", "field": f"results.{f}"}
    if res.get("status") != "conditional":
        return {"score": None, "basis": [field("status")], "reason": "economics inputs unresolved"}
    contribution = res.get("contribution_per_unit")
    viability = (res.get("viability") or {}).get("status")
    if isinstance(contribution, (int, float)) and contribution <= 0:
        return {"score": 10, "basis": [field("contribution_per_unit")], "reason": "non-positive contribution per unit"}
    if viability == "fail" or res.get("capacity_meets_target") is False:
        return {"score": 20, "basis": [field("viability.status"), field("capacity_meets_target")],
                "reason": "viability check failed or capacity below target"}
    if viability == "pass":
        if res.get("assumption_inputs"):
            return {"score": 65, "basis": [field("viability.status"), field("assumption_inputs")],
                    "reason": "passes the founder's viability targets on assumed inputs"}
        return {"score": 85, "basis": [field("viability.status"), field("assumption_inputs")],
                "reason": "passes viability targets with evidence-backed inputs"}
    return {"score": 35, "basis": [field("contribution_per_unit"), field("viability.status")],
            "reason": "positive contribution; viability targets untested"}


def build(*, ledger: list[dict] | None = None, quarantined: list[dict] | None = None,
          assessment: dict | None = None, voc_table: dict | None = None, economics: dict | None = None,
          factor_claims: dict | None = None, cost_cap: float = 100, currency: str = "EUR",
          warnings: list[str] | None = None) -> dict:
    ledger, factor_claims = ledger or [], factor_claims or {}
    unknown_factors = set(factor_claims) - set(FACTORS)
    if unknown_factors:
        raise ValueError("factor-claims has unknown factors: " + ", ".join(sorted(unknown_factors)))
    q_ids = {str(r.get("claim_id")) for r in (quarantined or [])}
    q_findings = {str(f) for r in (quarantined or []) for f in r.get("finding_ids", []) or []}
    by_id = {str(r["claim_id"]): r for r in ledger}
    for r in quarantined or []:
        by_id.setdefault(str(r.get("claim_id")), r)
    warnings = list(warnings or [])
    assigned: dict[str, list] = {f: [] for f in FACTORS if f != "economics"}
    for row in ledger + list(quarantined or []):
        if _types(row) & PAIN_TYPES:
            assigned["pain"].append((row, "supports", "claim_type"))
        if _types(row) & BUYER_TYPES:
            assigned["buyer"].append((row, "supports", "claim_type"))
    for cid in (assessment or {}).get("claim_ids", []) or []:
        if str(cid) in by_id:
            assigned["pain"].append((by_id[str(cid)], "supports", "problem-validation-assessment.claim_ids"))
    for factor, entries in factor_claims.items():
        if factor == "economics":
            raise ValueError("economics is scored from case_economics results, not claims")
        for item in entries:
            cid, direction = str(item.get("claim_id")), item.get("direction", "supports")
            if direction not in {"supports", "against"}:
                raise ValueError(f"{factor}/{cid}: direction must be supports or against")
            if cid not in by_id:
                raise ValueError(f"{factor}: claim {cid} is not in the ledger")
            assigned[factor].append((by_id[cid], direction, "factor-claims.json"))

    factors = {}
    for name in FACTORS:
        if name == "economics":
            e = _economics(economics)
            factors[name] = {"score": e["score"], "band": band(e["score"]), "basis": e["basis"],
                             "reason": e["reason"], "excluded_quarantined": [], "ignored": []}
            continue
        part = _claim_factor(name, assigned[name], q_ids, "claim-ledger.json")
        reasons = []
        if name == "pain" and voc_table:
            voc = _voc_pain(voc_table, q_findings)
            part["supports"] += voc["supports"]; part["basis"] += voc["basis"]
        score = max(part["supports"]) if part["supports"] else None
        if part["caps"]:
            cap = min(part["caps"])
            score = cap if score is None else min(score, cap)
            reasons.append(f"evidence against caps the factor at {cap}")
        if name == "pain" and assessment and score is not None:
            status = assessment.get("status")
            limit = {"insufficient_evidence": 50, "scoped": 80}.get(status)
            part["basis"].append({"artifact": "problem-validation-assessment.json", "field": "status", "value": status})
            if limit is not None and score > limit:
                score = limit
                reasons.append(f"assessment status {status} caps pain at {limit}")
        if score is None:
            reasons.append("no eligible reviewed evidence")
        factors[name] = {"score": score, "band": band(score), "basis": part["basis"], "reason": "; ".join(reasons),
                         "excluded_quarantined": sorted(set(part["excluded"])), "ignored": sorted(set(part["ignored"]))}

    known = [f["score"] for f in factors.values() if f["score"] is not None]
    unknown = [n for n in FACTORS if factors[n]["score"] is None]
    fatal = [n for n in FACTORS if factors[n]["score"] is not None and factors[n]["score"] <= 20]
    product = 100.0
    for s in known:
        product *= s / 100
    total, caps = round(product, 1) if known else 0.0, []
    if fatal:
        caps.append("factor <= 20 (" + ", ".join(fatal) + "): total capped at 20")
        total = min(total, 20.0)
    if unknown:
        caps.append("unknown factor (" + ", ".join(unknown) + "): total capped at 40")
        total = min(total, 40.0)

    if "pain" in fatal or len(fatal) >= 2:
        verdict = "stop"
    elif fatal:
        verdict = "pivot"
    elif len(unknown) >= 3:
        verdict = "insufficient_evidence"
    elif not unknown and min(known) > 50 and total >= 40:
        verdict = "commit"
    else:
        verdict = "test"
    if len(known) == len(FACTORS) and min(known) >= 80:
        warnings.append(BASE_RATE_WARNING)

    ordered = unknown + sorted((n for n in FACTORS if n not in unknown), key=lambda n: (factors[n]["score"], FACTORS.index(n)))
    def test_for(name):
        action, kill = TESTS[name]
        return {"factor": name, "assumption": ASSUMPTIONS[name], "action": action, "max_days": 14,
                "cost_cap": cost_cap, "currency": currency, "kill_threshold": kill,
                "constraints": "unpaid participants; proposal only, does not authorize outreach or spend"}
    riskiest = ordered[0]
    weak = [n for n in ordered if factors[n]["score"] is None or factors[n]["score"] <= 50]
    next_tests = [test_for(n) for n in (weak or [riskiest])]
    kill = [{"factor": n, "threshold": TESTS[n][1], "action": "stop or pivot this case if observed"}
            for n in dict.fromkeys([riskiest] + weak)]
    return {
        "schema_version": 1, "generated_view": True,
        "factors": factors,
        "total": {"score": total, "method": "100 x product(score/100) over known factors", "caps_applied": caps},
        "verdict": verdict, "verdict_vocabulary": VERDICT_VOCABULARY,
        "riskiest_assumption": {"factor": riskiest, "statement": ASSUMPTIONS[riskiest], "score": factors[riskiest]["score"],
                                "test": test_for(riskiest)},
        "next_tests": next_tests, "kill_criteria": kill,
        "segment": (assessment or {}).get("target_segment"),
        "warnings": warnings,
        "limits": "Summary of reviewed artifacts; scores are rubric bands, not probabilities, and not demand evidence.",
    }


def render(result: dict) -> str:
    lines = ["# Decision memo", "",
             f"**Verdict:** {result['verdict']} (strategy-plan verdict vocabulary). "
             f"**Total:** {result['total']['score']} / 100 (multiplicative).", ""]
    if result.get("segment"):
        lines += [f"Segment: {result['segment']}", ""]
    for cap in result["total"]["caps_applied"]:
        lines.append(f"- Cap applied: {cap}")
    for w in result["warnings"]:
        lines.append(f"- Warning: {w}")
    lines += ["", "## Factor scores", "", "| Factor | Score | Band | Basis | Note |", "|---|---|---|---|---|"]
    for name, f in result["factors"].items():
        basis = "; ".join(f"{b['artifact']}:{b['field']}" for b in f["basis"]) or "none"
        note = f.get("reason") or ""
        if f["excluded_quarantined"]:
            note += ("; " if note else "") + "falsified claims excluded: " + ", ".join(f["excluded_quarantined"])
        score = "unknown" if f["score"] is None else f["score"]
        lines.append(f"| {name} | {score} | {f['band']} | {basis} | {note} |")
    r = result["riskiest_assumption"]; t = r["test"]
    lines += ["", "## Riskiest assumption", "", f"{r['statement']} (factor: {r['factor']}, score: "
              f"{'unknown' if r['score'] is None else r['score']})", "",
              f"Test (at most {t['max_days']} days, cost cap {t['cost_cap']} {t['currency']}): {t['action']}",
              f"Constraint: {t['constraints']}.", "", "## Next tests", ""]
    lines += [f"{i}. {x['factor']}: {x['action']}" for i, x in enumerate(result["next_tests"], 1)]
    lines += ["", "## Kill criteria", ""]
    lines += [f"- {k['factor']}: {k['threshold']} -> {k['action']}." for k in result["kill_criteria"]]
    lines += ["", result["limits"], ""]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Build decision_memo.md and scores.json from reviewed case artifacts.")
    p.add_argument("--ledger", type=Path, help="reviewed claim-ledger.json (falsified sibling applied automatically)")
    p.add_argument("--falsified", type=Path, help="explicit claim-ledger.falsified.json path")
    p.add_argument("--assessment", type=Path, help="problem-validation-assessment.json")
    p.add_argument("--voc-table", type=Path, help="voc-table.json from build_voc_table.py")
    p.add_argument("--economics", type=Path, help="case_economics.py output JSON")
    p.add_argument("--factor-claims", type=Path, help="analyst-declared claim->factor assignments")
    p.add_argument("--cost-cap", type=float, default=100.0)
    p.add_argument("--currency", default="EUR")
    p.add_argument("--out", type=Path, required=True, help="output directory")
    a = p.parse_args(argv)
    load = lambda path: json.loads(path.read_text(encoding="utf-8")) if path else None
    try:
        claims = load_claims(a.ledger, a.falsified) if a.ledger else {"claims": [], "quarantined": [], "warnings": []}
        result = build(ledger=claims["claims"], quarantined=claims["quarantined"], warnings=claims["warnings"],
                       assessment=load(a.assessment), voc_table=load(a.voc_table), economics=load(a.economics),
                       factor_claims=load(a.factor_claims), cost_cap=a.cost_cap, currency=a.currency)
        from jsonschema import Draft202012Validator
        errors = list(Draft202012Validator(json.loads(SCHEMA.read_text(encoding="utf-8"))).iter_errors(result))
        if errors:
            raise ValueError("scores do not match decision-memo-scores schema: " + errors[0].message)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / "scores.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (a.out / "decision_memo.md").write_text(render(result), encoding="utf-8")
    for w in result["warnings"]:
        print("warning: " + w, file=sys.stderr)
    print(json.dumps({"verdict": result["verdict"], "total": result["total"]["score"],
                      "outputs": [str(a.out / "decision_memo.md"), str(a.out / "scores.json")]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
