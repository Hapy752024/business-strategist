from scripts import run_live_evals as live


def test_dry_run_lists_cases_for_a_skill():
    cases = live.load_cases('idea-grill')
    assert cases and all({'id', 'prompt'} <= set(case) for case in cases)


def test_scoring_checks_must_and_must_not_mention():
    case = {'id': 1, 'prompt': 'x', 'must_mention': ['segment', 'assumption'], 'must_not_mention': ['start coding']}
    good = live.score(case, 'Which segment? What assumption is riskiest?')
    bad = live.score(case, 'Great idea, start coding now.')
    assert good['passed'] and good['missing_terms'] == []
    assert not bad['passed'] and bad['missing_terms'] == ['segment', 'assumption'] and bad['forbidden_terms_hit'] == ['start coding']
