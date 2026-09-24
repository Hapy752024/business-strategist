"""Review reproductions. All writes/deletions are confined to fresh /tmp fixtures."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile

REPO = Path(__file__).resolve().parents[3]
SCRIPT = REPO / 'scripts/monitoring/ai_answer_probe.py'
ROOT = Path(tempfile.mkdtemp(prefix='visibility-review-'))
PANEL = {'panel_version': 'v1', 'engines': ['example'], 'repetitions': 1,
         'prompts': [{'id': 'p1', 'version': 1, 'type': 'unbranded_discovery',
                      'text': 'Which provider should I consider?'}]}
BASE = {'engine': 'example', 'model': 'model-1', 'search_config': 'on',
        'surface': 'api', 'locale': 'en-US', 'prompt_type': 'unbranded_discovery',
        'prompt_id': 'p1', 'prompt_version': 1, 'repetition': 1,
        'timestamp': '2026-09-21T10:00:00Z', 'status': 'success',
        'brand_mentioned': False, 'url_cited': False, 'recommended': False,
        'answer_text': 'An independently supplied recorded answer.'}

def run(name, rows, prior=None, panel=None, prior_panel=None, sentinel=False, dot=False):
    root = ROOT / name
    root.mkdir()
    (root / 'panel.json').write_text(json.dumps(panel or PANEL))
    (root / 'recorded.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
    out = root / 'out'
    if sentinel or dot:
        out.mkdir()
        (out / 'valuable-user-notes.txt').write_text('must survive')
    cmd = [sys.executable, str(SCRIPT), '--panel', str(root / 'panel.json'),
           '--recorded', str(root / 'recorded.jsonl'), '--out', '.' if dot else str(out)]
    if prior is not None:
        (root / 'prior.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in prior))
        cmd += ['--prior', str(root / 'prior.jsonl')]
    if prior_panel is not None:
        (root / 'prior-panel.json').write_text(json.dumps(prior_panel))
        cmd += ['--prior-panel', str(root / 'prior-panel.json')]
    result = subprocess.run(cmd, cwd=out if dot else root, text=True, capture_output=True)
    (root / 'stdout.json').write_text(result.stdout)
    (root / 'stderr.txt').write_text(result.stderr)
    summary = json.loads(result.stdout)
    return {'exit': result.returncode, 'status': summary.get('status'),
            'sentinel_exists': (out / 'valuable-user-notes.txt').exists(),
            'summary': summary, 'report': (out / 'report.md').read_text()}

old = {**BASE, 'timestamp': '2026-09-20T10:00:00Z'}
results = {}
for name, dot in [('existing_output_data_loss', False), ('out_dot_data_loss', True)]:
    results[name] = run(name, [BASE], sentinel=True, dot=dot)
results['off_panel_trend'] = run('off_panel_trend',
    [BASE, {**BASE, 'prompt_id': 'not-selected', 'brand_mentioned': True}],
    [old, {**old, 'prompt_id': 'not-selected'}], prior_panel=PANEL)
results['unverified_version_trend'] = run('unverified_version_trend',
    [{**BASE, 'brand_mentioned': True}], [old])
results['reverse_chronology'] = run('reverse_chronology',
    [{**old, 'brand_mentioned': True}], [BASE], prior_panel=PANEL)
changed = copy.deepcopy(PANEL)
changed['prompts'][0]['text'] = 'Completely different question about a different brand'
results['changed_question_same_version'] = run('changed_question_same_version',
    [{**BASE, 'brand_mentioned': True}], [old], panel=changed, prior_panel=PANEL)
two = {**PANEL, 'repetitions': 2}
results['pooled_surfaces_coverage'] = run('pooled_surfaces_coverage',
    [BASE, {**BASE, 'surface': 'consumer', 'repetition': 2}], panel=two)
results['lost_provenance'] = run('lost_provenance',
    [{**BASE, 'target_brand': 'Acme', 'target_url': 'https://example.test',
      'citation_urls': ['https://example.test/source'], 'error_detail': None}])

# Inject failure after the old output is moved aside, without touching real data.
spec = importlib.util.spec_from_file_location('review_probe', SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
case = ROOT / 'failed_publish_prior_loss'
case.mkdir()
out = case / 'out'
out.mkdir()
(out / 'previous-evidence.jsonl').write_text('irreplaceable previous evidence')
(case / 'panel.json').write_text(json.dumps(PANEL))
(case / 'recorded.jsonl').write_text(json.dumps(BASE)+'\n')
original = module._rename
calls = 0
def fail_second(src, dst):
    global calls
    calls += 1
    if calls == 2:
        raise OSError('injected second rename failure')
    original(src, dst)
module._rename = fail_second
sys.argv = ['probe', '--panel', str(case / 'panel.json'), '--recorded',
            str(case / 'recorded.jsonl'), '--out', str(out)]
rc = module.main()
results['failed_publish_prior_loss'] = {'exit': int(rc),
    'prior_evidence_anywhere': bool(list(case.rglob('previous-evidence.jsonl'))),
    'out_exists': out.exists()}
(ROOT / 'results.json').write_text(json.dumps(results, indent=2))
print(json.dumps({'artifacts': str(ROOT), 'cases': {
    name: {k: v for k, v in result.items() if k not in ('report', 'summary')}
    for name, result in results.items()}}, indent=2))
