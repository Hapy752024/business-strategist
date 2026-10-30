"""Acceptance harness tests: no model calls, no provider calls, no real worktrees."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import jsonschema
import pytest

from scripts import run_acceptance as acc

ROOT = Path(__file__).resolve().parents[1]
SCENARIO = ROOT / 'evals/acceptance/hybrid-insurance-advisor'
CHECKPOINTS = SCENARIO / 'checkpoints.json'
SCHEMA = ROOT / 'evals/acceptance/scorecard.schema.json'
SLUG = 'hybrid-insurance-advisor-20261030-120000'


def _line(obj: dict) -> str:
    return json.dumps(obj) + '\n'


def _assistant(text: str = '', tools: list[dict] | None = None, parent=None) -> str:
    content = [{'type': 'text', 'text': text}] if text else []
    content += tools or []
    return _line({'type': 'assistant', 'parent_tool_use_id': parent, 'message': {'role': 'assistant', 'content': content}})


def _tool(tid: str, name: str, inp: dict) -> dict:
    return {'type': 'tool_use', 'id': tid, 'name': name, 'input': inp}


def _result(tid: str, content: str, is_error: bool = False) -> str:
    return _line({'type': 'user', 'parent_tool_use_id': None, 'message': {'role': 'user', 'content': [
        {'type': 'tool_result', 'tool_use_id': tid, 'content': content, 'is_error': is_error}]}})


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def make_out_dir(tmp_path: Path, with_memo: bool = True) -> Path:
    """A synthetic finished run: two rounds, some tool calls and eval-project artifacts."""
    out = tmp_path / 'out'
    lines = [
        _line({'type': 'system', 'subtype': 'init', 'session_id': 'sess-1'}),
        _assistant('I found existing research workspaces:\n\n1. projects/german-insurance-opportunity/ — stage: evidence_collection\n\n'
                   'Which path: continue [1], or start new research?'),
        _line({'type': 'result', 'subtype': 'success', 'session_id': 'sess-1', 'total_cost_usd': 1.5, 'duration_ms': 1000,
               'num_turns': 1, 'result': 'Which path: continue [1], or start new research?',
               'usage': {'input_tokens': 100, 'output_tokens': 50, 'cache_creation_input_tokens': 10, 'cache_read_input_tokens': 5}}),
    ]
    round0_end = len(lines)
    lines += [
        _assistant('', [_tool('t1', 'Skill', {'skill': 'idea-grill', 'args': '{"route": {}}'})]),
        _result('t1', 'Launching skill: idea-grill'),
        _assistant('', [_tool('t2', 'Bash', {'command': 'python3 scripts/route_workflow.py "GTM" --project eval-x --check-skill archetype-gtm-strategist'})]),
        _result('t2', '{\n  "first_skill": "idea-grill",\n  "gate": "pain_first",\n  "gate_blocked": true\n}'),
        _assistant('', [_tool('t3', 'Bash', {'command': 'python3 scripts/route_workflow.py "GTM" --project eval-x --override-gate'})]),
        _result('t3', '{"gate_blocked": false, "override": true}'),
        _assistant('', [_tool('t4', 'Skill', {'skill': 'archetype-gtm-strategist', 'args': '{}'})]),
        _result('t4', 'Launching skill: archetype-gtm-strategist'),
        _assistant('', [_tool('t5', 'Bash', {'command': 'python3 scripts/evidence_scout/validate_research_completion.py --workspace w --run-dir r --check delivery'})]),
        _result('t5', 'delivery: ok'),
        _assistant('Regulation: §34d GewO brokers earn commission while §34e GewO advisers are fee-based '
                   '(https://www.gesetze-im-internet.de/gewo/__34d.html). Destatis reports coverage figures '
                   '(https://www.destatis.de/). Coverage gap: one provider could not be checked. journey complete'),
        _line({'type': 'result', 'subtype': 'success', 'session_id': 'sess-1', 'total_cost_usd': 2.0, 'duration_ms': 2000,
               'num_turns': 5, 'result': 'journey complete',
               'usage': {'input_tokens': 200, 'output_tokens': 80, 'cache_creation_input_tokens': 0, 'cache_read_input_tokens': 0}}),
    ]
    _write(out / 'transcript.jsonl', ''.join(lines))
    rounds = [
        {'round': 0, 'kind': 'initial', 'line_start': 0, 'line_end': round0_end, 'session_id': 'sess-1', 'matched_ids': []},
        {'round': 1, 'kind': 'answer', 'line_start': round0_end, 'line_end': len(lines), 'session_id': 'sess-1',
         'matched_ids': ['workspace_choice', 'scale_ambition']},
    ]
    _write(out / 'rounds.jsonl', ''.join(_line(r) for r in rounds))
    _write(out / 'run-manifest.json', json.dumps({
        'scenario': 'hybrid-insurance-advisor', 'ref': 'HEAD', 'ref_sha': 'a' * 40, 'eval_slug': SLUG,
        'started_at': '2026-10-30T12:00:00Z', 'finished_at': '2026-10-30T12:10:00Z', 'wall_time_s': 600.0,
        'budget_usd': 25.0, 'model_budget_usd': 40.0, 'blocked_tools': ['Artifact'], 'writes_outside_eval': [],
        'dry_run': False}))
    _write(out / 'provider-spend.json', json.dumps({'before': {}, 'after': {}, 'delta': {
        'apify_usd': 1.25, 'dataforseo_usd': None, 'serpapi_searches': 12, 'serpapi_usd': None}}))
    art = out / 'artifacts/projects/_eval' / SLUG / 'business'
    _write(art / 'strategy/intake/founder-context.md', 'A small, profitable practice; no external financing.\n')
    _write(art / 'market_research/pain_points/runs/r1/summary.json', json.dumps({'providers': {
        'brave_search': {'attempts': [{'status': 'ok'}]}, 'reddit': {'attempts': [{'status': 'missing_credentials'}]}}}))
    if with_memo:
        _write(art / 'cases/c1/decision_memo.md', '# Decision memo\n')
        _write(art / 'cases/c1/scores.json', '{"total": 18}')
    return out


def test_checkpoints_cover_brief_and_are_well_formed():
    data = json.loads(CHECKPOINTS.read_text())
    cps = data['checkpoints']
    assert [c['id'] for c in cps][:11] == [f'cp{n:02d}' for n in range(1, 12)]
    for cp in cps:
        assert {'id', 'stage', 'title', 'check', 'pass_rule', 'proxy'} <= set(cp)
        acc.validate_check(cp['check'])  # raises on unknown check types


def test_scorecard_validates_schema(tmp_path):
    out = make_out_dir(tmp_path)
    card = acc.score(out, CHECKPOINTS)
    jsonschema.validate(card, json.loads(SCHEMA.read_text()))
    assert len(card['checkpoints']) == 11
    assert card['cost']['model_usd'] == pytest.approx(2.0)  # cumulative max, not 1.5 + 2.0
    assert card['tokens']['input'] == 300
    assert card['providers']['failed'] == ['reddit']
    assert card['cost']['provider_spend']['complete'] is False  # SerpApi searches are unpriced
    by_id = {c['id']: c for c in card['checkpoints']}
    assert by_id['cp09']['passed'], by_id['cp09']['detail']
    assert by_id['cp03']['proxy'] is True
    path = acc.write_scorecard(out, card)
    assert path == out / 'scorecard.json' and json.loads(path.read_text())['summary']['total'] == 11


def test_score_marks_missing_artifact_as_fail(tmp_path):
    out = make_out_dir(tmp_path, with_memo=False)
    by_id = {c['id']: c for c in acc.score(out, CHECKPOINTS)['checkpoints']}
    assert by_id['cp08']['passed'] is False
    assert 'decision_memo' in by_id['cp08']['detail']


def test_gate_fails_when_downstream_runs_before_override(tmp_path):
    out = make_out_dir(tmp_path)
    lines = (out / 'transcript.jsonl').read_text().splitlines(keepends=True)
    early = _assistant('', [_tool('t0', 'Skill', {'skill': 'marketing-strategy-builder', 'args': '{}'})])
    (out / 'transcript.jsonl').write_text(''.join(lines[:3] + [early, _result('t0', 'ok')] + lines[3:]))
    by_id = {c['id']: c for c in acc.score(out, CHECKPOINTS)['checkpoints']}
    assert by_id['cp09']['passed'] is False


def test_runner_refuses_budget_over_cap(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(acc.subprocess, 'run', lambda *a, **k: calls.append(a) or subprocess.CompletedProcess(a, 0, '', ''))
    monkeypatch.setattr(acc.subprocess, 'Popen', lambda *a, **k: calls.append(a))
    with pytest.raises(ValueError, match='ceiling'):
        acc.run_acceptance(SCENARIO, tmp_path / 'out', budget_usd=acc.HARD_BUDGET_CEILING_USD + 0.01)
    with pytest.raises(ValueError, match='ceiling'):
        acc.run_acceptance(SCENARIO, tmp_path / 'out', model_budget_usd=acc.HARD_BUDGET_CEILING_USD * 10)
    with pytest.raises(ValueError, match='combined ceiling'):
        acc.run_acceptance(SCENARIO, tmp_path / 'out', budget_usd=30.0, model_budget_usd=40.0)
    acc.check_budgets(25.0, 40.0)  # the defaults stay allowed
    assert calls == [] and not (tmp_path / 'out').exists()
    assert acc.main(['--budget-usd', '75', '--dry-run']) == 2


class FakeGit:
    """Stands in for `git`: creates/removes the worktree directory, records every call."""

    def __init__(self):
        self.calls: list[list[str]] = []

    def __call__(self, cmd, *args, **kwargs):
        self.calls.append(list(cmd))
        if cmd[:3] == ['git', 'worktree', 'add']:
            wt = Path(cmd[4])
            (wt / 'projects').mkdir(parents=True)
            (wt / 'AGENTS.md').write_text('x')
        if cmd[:3] == ['git', 'worktree', 'remove']:
            import shutil
            shutil.rmtree(cmd[-1], ignore_errors=True)
        out = 'f' * 40 + '\n' if 'rev-parse' in cmd else ''
        return subprocess.CompletedProcess(cmd, 0, out, '')


def _reference(tmp_path: Path) -> Path:
    ref = tmp_path / 'reference/german-insurance-opportunity'
    for rel in acc.REFERENCE_SEED_FILES:
        _write(ref / rel, '{}')
    return ref


def test_runner_never_writes_outside_eval_slug(tmp_path, monkeypatch, capsys):
    git = FakeGit()
    monkeypatch.setattr(acc.subprocess, 'run', git)
    monkeypatch.setattr(acc.subprocess, 'Popen', lambda *a, **k: pytest.fail('dry run must not start claude'))
    monkeypatch.setattr(acc, 'measure_provider_spend', lambda: pytest.fail('dry run must not call providers'))
    monkeypatch.setattr(acc.tempfile, 'mkdtemp', lambda prefix='': str(tmp_path / 'tmp'))
    (tmp_path / 'tmp').mkdir()
    ref = _reference(tmp_path)
    ref_before = {p: p.read_bytes() for p in ref.rglob('*') if p.is_file()}
    out = tmp_path / 'out'
    plan = acc.run_acceptance(SCENARIO, out, dry_run=True, reference_project=ref, now='20261030-120000')
    wt = tmp_path / 'tmp/wt'
    eval_dir = wt / 'projects/_eval' / SLUG
    assert plan['writes'], 'dry run lists planned writes'
    for w in plan['writes']:
        p = Path(w['path'])
        if w['kind'] == 'scenario_copy':
            assert eval_dir / 'scenario' in [p, *p.parents]
        elif w['kind'] == 'reference_seed':
            assert wt / 'projects/german-insurance-opportunity' in p.parents
        else:
            assert w['kind'] == 'out_dir' and out in [p, *p.parents]
    assert not out.exists(), 'dry run writes nothing to out_dir'
    assert {p: p.read_bytes() for p in ref.rglob('*') if p.is_file()} == ref_before
    assert all(c[:2] == ['git', 'worktree'] or 'rev-parse' in c for c in git.calls)
    assert not wt.exists()
    printed = capsys.readouterr().out
    assert 'planned writes' in printed.lower() and str(eval_dir) in printed


def test_worktree_removed_after_run(tmp_path, monkeypatch):
    git = FakeGit()
    monkeypatch.setattr(acc.subprocess, 'run', git)
    monkeypatch.setattr(acc.tempfile, 'mkdtemp', lambda prefix='': str(tmp_path / 'tmp'))
    (tmp_path / 'tmp').mkdir()
    monkeypatch.setattr(acc, 'measure_provider_spend', lambda: {})

    def boom(*a, **k):
        raise RuntimeError('claude crashed')
    monkeypatch.setattr(acc, 'run_round', boom)
    with pytest.raises(RuntimeError, match='claude crashed'):
        acc.run_acceptance(SCENARIO, tmp_path / 'out', reference_project=_reference(tmp_path), now='20261030-120000')
    wt = str(tmp_path / 'tmp/wt')
    assert ['git', 'worktree', 'remove', '--force', wt] in git.calls
    assert ['git', 'worktree', 'prune'] in git.calls
    assert not Path(wt).exists()


def test_feeder_answers_from_fixture():
    feeder = acc.Feeder.load(SCENARIO / 'founder-answers.json', eval_dir='projects/_eval/' + SLUG,
                             alt_slug='eval-' + SLUG, budget_usd=25.0)
    kind, text, ids = feeder.reply('I found existing research workspaces:\n1. projects/german-insurance-opportunity/\n'
                                   'Which path: continue [1], or start new research?')
    assert kind == 'answer' and 'workspace_choice' in ids and 'projects/_eval/' + SLUG in text and 'eval-' + SLUG in text
    kind, text, ids = feeder.reply('The pain-first gate blocks GTM. Do you want me to record an explicit gate override?')
    assert 'gate_override' in ids and 'override' in text.lower()
    kind, text, ids = feeder.reply('Roughly how many hours per week can you put into this?')
    assert ids == ['time_commitment'] and 'proceed under a stated assumption' in text.lower()
    kind, text, ids = feeder.reply('What colour is your favourite umbrella?')
    assert kind == 'generic' and ids == [] and 'proceed under a stated assumption' in text.lower()
    assert feeder.reply('Here is the finished summary. journey complete') is None
    kind, text, ids = feeder.reply('I wrote the segment analysis and will continue with competitors next.')
    assert kind == 'nudge'
    answers = json.loads((SCENARIO / 'founder-answers.json').read_text())
    for entry in answers['answers']:
        if entry['answer'] is None:
            assert entry['instruction'] == 'proceed under a stated assumption'


def test_question_proxy_counts_question_sentences():
    assert acc.count_questions('Which segment first? And who pays? I will wait.') == 2
    assert acc.count_questions('Done. See https://example.com/?q=1 for details.') == 0


def test_private_answers_not_tracked():
    tracked = (SCENARIO / 'founder-answers.json').read_text(encoding='utf-8')
    assert not re.search(r'(€|\bEUR\b|\bUSD\b)\s*\d|\d[\d,.]*\s*(€|\bEUR\b|k\b)', tracked)
    data = json.loads(tracked)
    for entry in data['answers']:
        if entry.get('private_ref'):
            assert entry['answer'] is None and entry['instruction'] == 'proceed under a stated assumption'
            assert 'persist_markers' not in entry
    private = SCENARIO / acc.PRIVATE_ANSWERS
    ignored = subprocess.run(['git', 'check-ignore', '-q', str(private)], cwd=ROOT)
    assert ignored.returncode == 0, 'private answers file must be gitignored'
    listed = subprocess.run(['git', 'ls-files', '--error-unmatch', str(private)], cwd=ROOT, capture_output=True)
    assert listed.returncode != 0, 'private answers file must not be tracked'


def test_feeder_merges_private_answers(tmp_path):
    tracked = tmp_path / 'founder-answers.json'
    tracked.write_text((SCENARIO / 'founder-answers.json').read_text(encoding='utf-8'), encoding='utf-8')
    kwargs = dict(eval_dir='projects/_eval/x', alt_slug='eval-x', budget_usd=25.0)
    question = 'How much capital can you put into this?'
    kind, text, ids = acc.Feeder.load(tracked, **kwargs).reply(question)
    assert ids[0] == 'capital_budget' and 'proceed under a stated assumption' in text.lower()
    (tmp_path / acc.PRIVATE_ANSWERS).write_text(json.dumps({'answers': {'capital_budget': {
        'answer': 'Synthetic capital answer 42.', 'persist_markers': ['synthetic-42']}}}), encoding='utf-8')
    feeder = acc.Feeder.load(tracked, **kwargs)
    kind, text, ids = feeder.reply(question)
    assert kind == 'answer' and 'Synthetic capital answer 42.' in text
    assert feeder.entry('capital_budget')['persist_markers'] == ['synthetic-42']


def test_scenario_copy_excludes_private_answers(tmp_path):
    scen = tmp_path / 'scen'
    for name in ('scenario.md', 'founder-answers.json', 'checkpoints.json', acc.PRIVATE_ANSWERS, '.gitignore'):
        _write(scen / name, '{}')
    wt = tmp_path / 'wt'
    writes = acc.stage_inputs(scen, wt, wt / 'projects/_eval/s', None)
    assert {Path(w['path']).name for w in writes} == {'scenario.md'}


def test_agent_cannot_see_scoring_files(tmp_path, monkeypatch):
    class GitWithTrackedEvals(FakeGit):
        def __call__(self, cmd, *args, **kwargs):
            res = super().__call__(cmd, *args, **kwargs)
            if cmd[:3] == ['git', 'worktree', 'add']:
                for name in ('founder-answers.json', 'checkpoints.json', 'scenario.md'):
                    _write(Path(cmd[4]) / 'evals/acceptance/hybrid-insurance-advisor' / name, '{}')
            return res
    monkeypatch.setattr(acc.subprocess, 'run', GitWithTrackedEvals())
    monkeypatch.setattr(acc.tempfile, 'mkdtemp', lambda prefix='': str(tmp_path / 'tmp'))
    (tmp_path / 'tmp').mkdir()
    monkeypatch.setattr(acc, 'measure_provider_spend', lambda: {})
    seen = {}

    def fake_round(cmd, *, cwd, transcript, stderr_log, timeout_s):
        wt = Path(cwd)
        seen['evals'] = (wt / 'evals/acceptance').exists()
        seen['files'] = sorted(p.name for p in wt.rglob('*') if p.is_file())
        return {'line_start': 0, 'line_end': 0, 'session_id': None, 'final_text': '', 'session_cost_usd': 0.0,
                'exit_code': 0, 'timed_out': False, 'duration_s': 0.0}
    monkeypatch.setattr(acc, 'run_round', fake_round)
    acc.run_acceptance(SCENARIO, tmp_path / 'out', reference_project=_reference(tmp_path), now='20261030-120000')
    assert seen['evals'] is False
    assert 'founder-answers.json' not in seen['files'] and 'checkpoints.json' not in seen['files']
    assert acc.PRIVATE_ANSWERS not in seen['files'] and 'scenario.md' in seen['files']
    assert any(r.startswith('Read(') and r.endswith('/evals/acceptance/**)') for r in acc.blocked_tools([ROOT]))


def test_gate_requires_pain_first_gate(tmp_path):
    out = make_out_dir(tmp_path)
    path = out / 'transcript.jsonl'
    path.write_text(path.read_text().replace('pain_first', 'case_scope_required'))
    by_id = {c['id']: c for c in acc.score(out, CHECKPOINTS)['checkpoints']}
    assert by_id['cp09']['passed'] is False and 'no blocked' in by_id['cp09']['detail']


def test_empty_run_is_not_exercised_not_passed(tmp_path):
    out = tmp_path / 'empty'
    out.mkdir()
    card = acc.score(out, CHECKPOINTS)
    jsonschema.validate(card, json.loads(SCHEMA.read_text()))
    by_id = {c['id']: c for c in card['checkpoints']}
    assert by_id['cp11']['status'] == 'not_exercised' and by_id['cp11']['passed'] is False
    assert 'cp11' in card['summary']['not_exercised'] and card['summary']['passed'] == 0
    assert card['cost']['over_budget'] is None


def test_cp11_not_exercised_without_provider_failure(tmp_path):
    out = make_out_dir(tmp_path)
    summary = next((out / 'artifacts').rglob('summary.json'))
    summary.write_text(json.dumps({'providers': {'brave_search': {'attempts': [{'status': 'ok'}]}}}))
    by_id = {c['id']: c for c in acc.score(out, CHECKPOINTS)['checkpoints']}
    assert by_id['cp11']['status'] == 'not_exercised'


def test_over_budget_needs_complete_measurement(tmp_path):
    out = tmp_path / 'o'
    _write(out / 'provider-spend.json', json.dumps({'delta': {'apify_usd': 3.0, 'dataforseo_usd': None,
                                                               'serpapi_searches': 5, 'serpapi_usd': None}}))
    assert acc.spend_summary(out, 25.0)[1] is None
    _write(out / 'provider-spend.json', json.dumps({'delta': {'apify_usd': 30.0}}))
    assert acc.spend_summary(out, 25.0)[1] is True
    _write(out / 'provider-spend.json', json.dumps({'delta': {'apify_usd': 3.0, 'dataforseo_usd': 1.0,
                                                               'serpapi_searches': 5, 'serpapi_usd': 0.5}}))
    assert acc.spend_summary(out, 25.0)[1] is False


def test_feeder_whole_words_and_last_questions():
    feeder = acc.Feeder.load(SCENARIO / 'founder-answers.json', eval_dir='e', alt_slug='a', budget_usd=25.0)
    kind, text, ids = feeder.reply('Should I investigate the PKV journey first?')
    assert 'capital_budget' not in ids
    kind, text, ids = feeder.reply('How much capital do you have? Fine. Which product do you want to start with?')
    assert 'capital_budget' in ids  # within the last two question sentences
    kind, text, ids = feeder.reply('What capital do you have? Who pays? Which region? Do you speak English?')
    assert 'capital_budget' not in ids and 'languages' in ids


def test_feeder_intake_cap():
    feeder = acc.Feeder.load(SCENARIO / 'founder-answers.json', eval_dir='e', alt_slug='a', budget_usd=25.0)
    kinds = [feeder.reply('Roughly how many hours per week can you put into this?', rounds_left=10)[0] for _ in range(5)]
    assert kinds[:4] == ['answer'] * 4 and kinds[4] == 'intake_cap'
    fresh = acc.Feeder.load(SCENARIO / 'founder-answers.json', eval_dir='e', alt_slug='a', budget_usd=25.0)
    kind, text, _ = fresh.reply('Which segment first?', rounds_left=4)
    assert kind == 'intake_cap' and text.endswith(acc.INTAKE_CAP_TEXT)


def test_completion_marker_only_at_end():
    feeder = acc.Feeder.load(SCENARIO / 'founder-answers.json', eval_dir='e', alt_slug='a', budget_usd=25.0)
    assert feeder.reply('All steps done. **Journey complete.**') is None
    kind, _, _ = feeder.reply('Once the journey complete marker is reached I will stop; next I build the site.')
    assert kind == 'nudge'


def test_interrupt_kills_child_and_removes_worktree(tmp_path, monkeypatch):
    git = FakeGit()
    monkeypatch.setattr(acc.subprocess, 'run', git)
    monkeypatch.setattr(acc.tempfile, 'mkdtemp', lambda prefix='': str(tmp_path / 'tmp'))
    (tmp_path / 'tmp').mkdir()
    monkeypatch.setattr(acc, 'measure_provider_spend', lambda: {})
    kills = []

    class Proc:
        pid = 424242
        returncode = None

        def __init__(self, *a, **k):
            self.calls = 0

        def wait(self, timeout=None):
            self.calls += 1
            if self.calls == 1:
                raise KeyboardInterrupt
            return 0

    def killpg(pid, sig):
        kills.append((pid, sig))
        if sig == acc.signal.SIGKILL:
            raise ProcessLookupError
    monkeypatch.setattr(acc.subprocess, 'Popen', Proc)
    monkeypatch.setattr(acc.os, 'killpg', killpg)
    with pytest.raises(KeyboardInterrupt):
        acc.run_acceptance(SCENARIO, tmp_path / 'out', reference_project=_reference(tmp_path), now='20261030-120000')
    assert kills[0] == (424242, acc.signal.SIGTERM)
    wt = str(tmp_path / 'tmp/wt')
    assert ['git', 'worktree', 'remove', '--force', wt] in git.calls and ['git', 'worktree', 'prune'] in git.calls
    assert acc.signal.getsignal(acc.signal.SIGTERM) is not acc._raise_interrupt  # handlers restored


def test_terminate_tolerates_vanished_group(monkeypatch):
    monkeypatch.setattr(acc.os, 'killpg', lambda pid, sig: (_ for _ in ()).throw(ProcessLookupError()))
    acc.terminate(type('P', (), {'pid': 1, 'wait': lambda self, timeout=None: 0})())


def test_host_projects_audit(tmp_path):
    host = tmp_path / 'host'
    _write(host / 'projects/real/file.md', 'a')
    wt = tmp_path / 'wt'
    (wt / 'projects').mkdir(parents=True)
    before_host = {host: acc.snapshot(host / 'projects')}
    _write(host / 'projects/real/new.md', 'agent wrote here')
    changed = acc.writes_outside_eval(wt, [wt / 'projects/_eval/s'], acc.snapshot(wt / 'projects'), before_host)
    assert any(c.startswith('host:') and c.endswith('real/new.md') for c in changed)
    assert 'Bash(git rev-parse*)' in acc.DISALLOWED_TOOLS and 'Bash(git rev-parse*)' not in acc.ALLOWED_TOOLS


def test_cp01_counts_script_created_workspaces(tmp_path):
    out = make_out_dir(tmp_path)
    lines = (out / 'transcript.jsonl').read_text().splitlines(keepends=True)
    write = _assistant('', [_tool('w0', 'Bash', {'command': 'python3 scripts/evidence_scout/workspace.py --workspace projects/_eval/x'})])
    (out / 'transcript.jsonl').write_text(''.join(lines[:1] + [write, _result('w0', 'ok')] + lines[1:]))
    by_id = {c['id']: c for c in acc.score(out, CHECKPOINTS)['checkpoints']}
    assert by_id['cp01']['passed'] is False


def _results(costs, session='s1'):
    return ''.join(_line({'type': 'result', 'session_id': session, 'total_cost_usd': c, 'result': 'x',
                          'usage': {'input_tokens': 1, 'output_tokens': 1}}) for c in costs)


def test_model_cost_is_cumulative_max_not_sum(tmp_path):
    out = tmp_path / 'o'
    # Round 0 emits one result; round 1 repeats the cumulative figure on several events (background notifications).
    _write(out / 'transcript.jsonl', _results([0.276]) + _results([2.033, 2.033, 2.033, 3.205, 3.205]))
    _write(out / 'rounds.jsonl', _line({'round': 0, 'kind': 'initial', 'line_start': 0, 'line_end': 1}) +
           _line({'round': 1, 'kind': 'nudge', 'line_start': 1, 'line_end': 6}))
    card = acc.score(out, CHECKPOINTS)
    assert card['cost']['model_usd'] == pytest.approx(3.205)
    assert any('maximum cumulative' in n for n in card['honesty_notes'])


def test_run_round_reports_session_cumulative_cost(tmp_path, monkeypatch):
    transcript, err = tmp_path / 't.jsonl', tmp_path / 'e.log'
    transcript.write_text(_results([1.0]))

    class Proc:
        pid, returncode = 1, 0

        def __init__(self, cmd, cwd, stdout, stderr, text, start_new_session):
            stdout.write(_results([1.4, 1.4, 1.9]))
            stdout.flush()

        def wait(self, timeout=None):
            return 0
    monkeypatch.setattr(acc.subprocess, 'Popen', Proc)
    info = acc.run_round(['claude'], cwd=tmp_path, transcript=transcript, stderr_log=err, timeout_s=5)
    assert info['session_cost_usd'] == pytest.approx(1.9) and info['line_start'] == 1 and info['line_end'] == 4


GATE_OPTIONS_MESSAGE = """Step 2 is drafted: nine files with customer voices, search behaviour and regulation.

Step 3 (business model, costs, regulation, risks) stays blocked until the customer problem is validated, and
this research does not validate it. To go on I need you to record the explicit gate override you mentioned.
It is not evidence, and everything built after it will be labelled untested. About 1 USD of the evidence budget is spent.

**Your call:**
1. Record the override and move on to step 3.
2. Let me keep closing the step 2 gaps first, mainly recent voices and competitor reviews.

I recommend option 2."""


def test_feeder_sends_gate_override_for_options_list():
    feeder = acc.Feeder.load(SCENARIO / 'founder-answers.json', eval_dir='e', alt_slug='a', budget_usd=25.0)
    kind, text, ids = feeder.reply(GATE_OPTIONS_MESSAGE)
    assert kind == 'answer' and ids == ['gate_override'] and 'record an explicit gate override' in text.lower()
    say_form = ('Gate: step 3 is still blocked. If you want to test the downstream steps, say: '
                '"record the gate override for the hybrid insurance advisor".')
    assert feeder.reply(say_form)[2] == ['gate_override']
    plain_list = 'Done:\n1. Wrote the journey map.\n2. Wrote the source list.\nNext I compare competitors.'
    assert feeder.reply(plain_list)[0] == 'nudge'  # a list without a choice cue is not a question


def test_host_writes_attribution(tmp_path):
    out = make_out_dir(tmp_path)
    host = '/home/u/repo/projects'
    manifest = json.loads((out / 'run-manifest.json').read_text())
    manifest['writes_outside_eval'] = [f'host:{host}/agent-touched/notes.md', f'host:{host}/other-site/web-site/app/page.tsx']
    (out / 'run-manifest.json').write_text(json.dumps(manifest))
    lines = (out / 'transcript.jsonl').read_text()
    touch = _assistant('', [_tool('h1', 'Bash', {'command': f'python3 scripts/x.py --out {host}/agent-touched'})])
    (out / 'transcript.jsonl').write_text(lines + touch + _result('h1', 'ok'))
    card = acc.score(out, CHECKPOINTS)
    jsonschema.validate(card, json.loads(SCHEMA.read_text()))
    assert card['host_writes']['attributed'] == [f'host:{host}/agent-touched/notes.md']
    assert card['host_writes']['unattributed_possibly_concurrent'] == [f'host:{host}/other-site/web-site/app/page.tsx']
    assert card['honesty_notes'][0].startswith('WARNING: 1 host file change')
    manifest['writes_outside_eval'] = manifest['writes_outside_eval'][1:]
    (out / 'run-manifest.json').write_text(json.dumps(manifest))
    assert not any(n.startswith('WARNING') for n in acc.score(out, CHECKPOINTS)['honesty_notes'])


def test_quota_errors_count_as_exercised_gap(tmp_path):
    out = make_out_dir(tmp_path)
    for p in (out / 'artifacts').rglob('summary.json'):
        p.unlink()
    lines = (out / 'transcript.jsonl').read_text()
    call = _assistant('', [_tool('q1', 'mcp__brave-search__brave_web_search', {'query': 'PKV GKV'})])
    err = _result('q1', '402 Payment Required\n{"status": 402, "detail": "Usage limit exceeded."}', is_error=True)
    (out / 'transcript.jsonl').write_text(lines + call + err)
    card = acc.score(out, CHECKPOINTS)
    by_id = {c['id']: c for c in card['checkpoints']}
    assert 'brave-search' in card['providers']['failed']
    assert by_id['cp11']['status'] == 'pass'  # the fixture states a coverage gap
    assert any('brave-search (1 call(s))' in n for n in card['honesty_notes'])


def test_hook_denial_counted_once(tmp_path):
    out = tmp_path / 'o'
    hook = _line({'type': 'system', 'subtype': 'hook_response', 'hook_name': 'PreToolUse:Skill',
                  'output': '{"hookSpecificOutput": {"permissionDecision": "deny"}}'})
    call = _assistant('', [_tool('d1', 'Skill', {'skill': 'idea-grill'})])
    res = _result('d1', 'PreToolUse:Skill hook error: Skill route rejected', is_error=True)
    _write(out / 'transcript.jsonl', call + hook + res)
    assert acc.hook_denials(acc.parse_transcript(out))['count'] == 1
