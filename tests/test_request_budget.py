import importlib
import io
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts/validate_apis'))
common = importlib.import_module('common')


class Response(io.BytesIO):
    status = 200

    def __init__(self, control='max-age=30'):
        super().__init__(b'{"items": [1]}')
        self.headers = {'Cache-Control': control}


def test_budget_blocks_network_and_reuses_only_identical_fresh_gets():
    with patch.object(common.urllib.request, 'urlopen', side_effect=lambda *a, **k: Response()) as network:
        with common.request_budget(2) as budget:
            first = common.http_get('https://example.test/a', headers={'Authorization': 'one'})
            first['body']['items'].append(2)
            assert common.http_get('https://example.test/a', headers={'Authorization': 'one'})['body']['items'] == [1]
            common.http_get('https://example.test/a', headers={'Authorization': 'two'})
            blocked = common.http_get('https://example.test/b')
            assert common.status_from_response(blocked) == 'request_budget_exhausted'
            assert network.call_count == 2
            assert budget.summary()['cache_hits'] == 1
            assert 'one' not in json.dumps(budget.summary())
        assert budget.cache == {}
        common.http_get('https://example.test/b')
        assert network.call_count == 3


@pytest.mark.parametrize('control', ['', 'no-store,max-age=30', 'no-cache,max-age=30', 'max-age=0'])
def test_uncacheable_responses_are_not_reused(control):
    with patch.object(common.urllib.request, 'urlopen', side_effect=lambda *a, **k: Response(control)) as network:
        with common.request_budget(2):
            common.http_get('https://example.test/a')
            common.http_get('https://example.test/a')
        assert network.call_count == 2


def test_posts_and_failures_are_not_cached_and_fresh_mode_works():
    with patch.object(common.urllib.request, 'urlopen', side_effect=lambda *a, **k: Response()) as network:
        with common.request_budget(4, reuse_gets=False):
            for method in ['POST', 'POST', 'GET', 'GET']:
                common.http_request(method, 'https://example.test/a')
        assert network.call_count == 4
    with patch.object(common.urllib.request, 'urlopen', side_effect=OSError('offline')) as network:
        with common.request_budget(2):
            for _ in range(3):
                common.http_get('https://example.test/a')
        assert network.call_count == 2


def test_expired_cache_and_nested_budget_cannot_bypass_limit():
    with patch.object(common.urllib.request, 'urlopen', side_effect=lambda *a, **k: Response()) as network:
        with common.request_budget(1) as budget:
            common.http_get('https://example.test/a')
            key = next(iter(budget.cache))
            budget.cache[key] = (0, budget.cache[key][1])
            assert not common.http_get('https://example.test/a')['ok']
            with pytest.raises(ValueError, match='Nested'):
                with common.request_budget(100):
                    pass
        assert network.call_count == 1


@pytest.mark.parametrize('value', [0, -1, True, 1.5])
def test_invalid_budget(value):
    with pytest.raises(ValueError):
        common.RequestBudget(value)
