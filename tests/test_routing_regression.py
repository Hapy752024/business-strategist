"""Frozen routing decisions: any change to how the differential corpus routes fails with the changed rows.

After an intended routing change, review the printed rows, then refresh with
`python3 scripts/routing_regression.py --update` and review the diff of tests/routing_expected.json for steals.
"""
import json

from scripts import routing_regression


def test_routing_decisions_match_the_frozen_corpus():
    expected = json.loads(routing_regression.EXPECTED_PATH.read_text(encoding='utf-8'))
    actual, _ = routing_regression.decisions()
    changes = routing_regression.changed_rows(expected, actual)
    assert not changes, f'{len(changes)} routing decision(s) changed:\n' + '\n'.join(changes)


def test_corpus_covers_evals_single_phrases_and_ordered_pairs():
    rows = routing_regression.corpus()
    phrased = [route for route in routing_regression.route_workflow.load_routes() if route.get('match')]
    pairs = [pair for _, pair in rows if pair]
    assert len(pairs) == len(phrased) * (len(phrased) - 1)
    requests = [request for request, _ in rows]
    assert len(requests) == len(set(requests))
    assert all(route['match'][0] in requests for route in phrased)
    evals = json.loads((routing_regression.ROOT / 'config/routing-evals.json').read_text(encoding='utf-8'))
    assert all(case['prompt'] in requests for pair in evals['pairs'] for case in pair['evals'])
    expected = json.loads(routing_regression.EXPECTED_PATH.read_text(encoding='utf-8'))
    assert set(expected) == set(routing_regression.CONTEXTS)
    assert all(list(decisions) == requests for decisions in expected.values())


def test_a_changed_decision_is_reported_with_its_row():
    expected = {'no-project': {'logo': 'standalone-brand', 'smoke test': 'smoke-test-design'}}
    actual = {'no-project': {'logo': 'website-build', 'smoke test': 'smoke-test-design'}}
    assert routing_regression.changed_rows(expected, actual) == [
        "[no-project] 'logo': standalone-brand -> website-build"]
