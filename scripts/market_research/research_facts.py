"""Review binding for typed research observations; no automatic truth certification."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator, ValidationError

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
SCHEMA = json.loads((ROOT / 'schemas/research-fact.schema.json').read_text())


def fact_digest(fact):
    authored = {k: v for k, v in fact.items() if k not in {'review', 'review_status'}}
    return hashlib.sha256(json.dumps(authored, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def check_fact(fact, base, *, accepted=False):
    try:
        Draft202012Validator(SCHEMA).validate(fact)
    except ValidationError as exc:
        raise ValueError('Invalid research fact: ' + exc.message) from exc
    base = Path(base).resolve()
    path = (base / fact['capture_path']).resolve()
    if not path.is_relative_to(base) or not path.is_file():
        raise ValueError('Fact capture is missing or outside its run')
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != fact['content_sha256']:
        raise ValueError('Fact capture changed')
    from scripts.verify_numeric_claims import pointer
    capture = json.loads(raw)
    if capture.get('original_path'):
        original = (base / capture['original_path']).resolve()
        if not original.is_relative_to(base) or not original.is_file() or hashlib.sha256(original.read_bytes()).hexdigest() != capture.get('original_sha256'):
            raise ValueError('Original research document changed or is missing')
    observation = pointer(capture, fact['locator'])
    expected = {**observation, 'currency': None, 'scope': capture['scope']['population']}
    if expected != fact['observation']:
        raise ValueError('Fact observation does not match its original capture')
    if accepted:
        if fact['review_status'] != 'accepted' or fact.get('review', {}).get('fact_digest') != fact_digest(fact):
            raise ValueError('Fact needs a current accepted review')
    return fact


def review(facts, decisions, base):
    by_id = {row['evidence_id']: row for row in facts}
    if len(by_id) != len(facts) or set(by_id) != {row['evidence_id'] for row in decisions} or len(decisions) != len(facts):
        raise ValueError('Review must cover each unique fact exactly once')
    result = []
    for decision in decisions:
        fact = dict(check_fact(by_id[decision['evidence_id']], base))
        if decision.get('fact_digest') != fact_digest(fact):
            raise ValueError('Review was prepared against a different fact')
        if decision.get('status') not in {'accepted', 'rejected'}:
            raise ValueError('Review status must be accepted or rejected')
        for key in ('reviewer', 'reviewed_at', 'rationale'):
            if not isinstance(decision.get(key), str) or not decision[key].strip():
                raise ValueError('Review requires ' + key)
        fact['review_status'] = decision['status']
        fact['review'] = {key: decision[key] for key in ('reviewer', 'reviewed_at', 'fact_digest', 'rationale')}
        result.append(fact)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--facts', type=Path, required=True)
    p.add_argument('--reviews', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    if args.out.exists() or args.out.parent.resolve() != args.facts.parent.resolve():
        p.error('Use a fresh sibling output so capture paths remain bound')
    try:
        facts = [json.loads(line) for line in args.facts.read_text().splitlines() if line.strip()]
        rows = review(facts, json.loads(args.reviews.read_text()), args.facts.parent)
    except (ValueError, KeyError) as exc:
        p.exit(2, str(exc) + '\n')
    args.out.write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows))
    print(json.dumps({'reviewed': len(rows), 'accepted': sum(row['review_status'] == 'accepted' for row in rows)}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
