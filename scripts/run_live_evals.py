#!/usr/bin/env python3
"""Opt-in live skill evals: dry run by default; --live invokes `claude -p` and spends tokens."""
from __future__ import annotations
import argparse
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_cases(skill: str) -> list[dict]:
    path = ROOT / '.agents/skills' / skill / 'evals/evals.json'
    data = json.loads(path.read_text())
    return data.get('evals', [])


def score(case: dict, answer: str) -> dict:
    lower = answer.lower()
    missing = [term for term in case.get('must_mention', []) if term.lower() not in lower]
    hit = [term for term in case.get('must_not_mention', []) if term.lower() in lower]
    return {'case_id': case.get('id'), 'passed': not missing and not hit,
            'missing_terms': missing, 'forbidden_terms_hit': hit}


def run_case(skill: str, case: dict) -> str:
    prompt = f"Use the {skill} skill. {case['prompt']}"
    with tempfile.TemporaryDirectory() as cwd:
        out = subprocess.run(['claude', '-p', prompt, '--output-format', 'json', '--add-dir', str(ROOT)],
                             cwd=cwd, text=True, capture_output=True, timeout=600)
    if out.returncode != 0:
        raise RuntimeError(out.stderr[-2000:])
    payload = json.loads(out.stdout)
    return payload.get('result', '') if isinstance(payload, dict) else str(payload)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--skill', required=True)
    ap.add_argument('--case', default='')
    ap.add_argument('--live', action='store_true', help='actually call the model')
    ap.add_argument('--out', type=Path, default=ROOT / 'evals/live-results')
    args = ap.parse_args()
    cases = [c for c in load_cases(args.skill) if not args.case or str(c.get('id')) == args.case]
    if not cases:
        ap.error('no matching eval cases')
    if not args.live:
        for case in cases:
            print(f"[dry-run] {args.skill} #{case.get('id')}: {case['prompt'][:100]}")
        print(f"{len(cases)} case(s). Add --live to run them.")
        return 0
    args.out.mkdir(parents=True, exist_ok=True)
    failures = 0
    for case in cases:
        answer = run_case(args.skill, case)
        result = score(case, answer) | {'answer': answer}
        (args.out / f"{args.skill}-{case.get('id')}.json").write_text(json.dumps(result, indent=2) + '\n')
        failures += not result['passed']
        print(f"{'PASS' if result['passed'] else 'FAIL'} {args.skill} #{case.get('id')} missing={result['missing_terms']} forbidden={result['forbidden_terms_hit']}")
    return 1 if failures else 0


if __name__ == '__main__':
    raise SystemExit(main())
