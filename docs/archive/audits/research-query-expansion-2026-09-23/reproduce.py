"""Offline reproductions. Does not modify project files or make provider calls."""
import sys
import tempfile
import types
import json
from pathlib import Path
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests'))
import test_research_query_expansion as fixtures
c = fixtures.c
ok = lambda body: {'ok': True, 'status_code': 200, 'body': body}
def youtube_get(url, **kwargs):
    if 'commentThreads' in url:
        return ok({'items': [{'id': f'comment{i}', 'snippet': {'topLevelComment': {'snippet': {'textDisplay': f'comment text {i}'}}}} for i in range(5)]})
    return ok({'items': [{'id': {'videoId': 'v1'}, 'snippet': {'title': 'local founder story'}}]})
def youtube_run(module, baseline=False):
    with tempfile.TemporaryDirectory() as directory, patch.object(module, 'get_secret', return_value=('fixture', 'key')), patch.object(module, 'assess_relevance', return_value=('relevant', 'fixture', 2)), patch.object(module, 'http_get', side_effect=youtube_get), patch.object(module, 'fetch_youtube_transcript', return_value=('ok', 'unique full transcript content')):
        args = fixtures.args('youtube', query_plan_data=fixtures.plan('youtube', ['founder account']), limit=5, results_per_query=5, youtube_transcripts=True)
        records, summary = module.collect_youtube(args, ['q'] * 9 if baseline else [], Path(directory))
        result = {'sources': [r['source'] for r in records], 'summary': summary['status'], 'transcripts': summary['transcripts']}
        if not baseline:
            capture = json.loads(Path(summary['query_ledger'][0]['capture_path']).read_text())
            result['raw_transcript'] = capture['transcripts']
            result['raw_contains_transcript_text'] = 'unique full transcript content' in json.dumps(capture)
        return result
print('Current YouTube:', json.dumps(youtube_run(c)))
baseline_path = Path('/tmp/research-expansion-baseline/scripts/evidence_scout/collect.py')
if baseline_path.exists():
    old = types.ModuleType('baseline_collect')
    old.__file__ = str(ROOT / 'scripts/evidence_scout/collect.py')
    sys.modules[old.__name__] = old
    # Resolve unchanged repository dependencies from the actual repository root.
    exec(compile(baseline_path.read_text(), old.__file__, 'exec'), old.__dict__)
    print('Baseline YouTube:', json.dumps(youtube_run(old, baseline=True)))
def social_get(url, **kwargs):
    if 'credit-balance' in url:
        return ok({'creditCount': 100})
    source = 'tiktok' if 'tiktok' in url else 'instagram' if 'instagram' in url else 'threads'
    return ok({'items': [{'id': f'{source}{i}', 'text': f'{source} customer account {i}', 'url': f'https://{source}.test/post/{i}'} for i in range(3)]})
with tempfile.TemporaryDirectory() as directory, patch.object(c, 'get_secret', return_value=('fixture', 'key')), patch.object(c, 'assess_relevance', return_value=('relevant', 'fixture', 2)), patch.object(c, 'http_get', side_effect=social_get):
    args = fixtures.args('scrapecreators', query_plan_data=fixtures.plan('scrapecreators', ['local experience']), limit=3, results_per_query=3, social_per_endpoint=3, social_comments=True)
    records, summary = c.collect_scrapecreators(args, [], Path(directory))
    print('Current social:', json.dumps({'sources': [r['source'] for r in records], 'summary': summary['status'], 'endpoints': summary['endpoint_statuses'], 'comments': summary['comment_request_ledger']}))
