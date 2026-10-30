"""IndexNow ping: refuses without deploy confirmation and a verified key file; HTTP is mocked."""
import json

import pytest

from scripts.brand import indexnow_ping

KEY = 'a1b2c3d4e5f60718293a4b5c6d7e8f90'


@pytest.fixture
def http(monkeypatch):
    calls = []
    responses = {}

    def fake(method, url, body=None, timeout=20):
        calls.append((method, url, body))
        return responses.get((method, url), (404, ''))

    monkeypatch.setattr(indexnow_ping, '_http', fake)
    return calls, responses


def test_refuses_without_confirm_deployed(http):
    calls, responses = http
    responses[('GET', f'https://www.example.com/{KEY}.txt')] = (200, KEY)
    with pytest.raises(PermissionError, match='confirm'):
        indexnow_ping.ping('www.example.com', ['https://www.example.com/'], KEY)
    assert calls == []
    assert indexnow_ping.main(['www.example.com', '--key', KEY, '--url', 'https://www.example.com/']) == 2
    assert calls == []


def test_refuses_when_key_file_missing_or_wrong(http):
    calls, responses = http
    with pytest.raises(PermissionError, match='key file'):
        indexnow_ping.ping('www.example.com', ['https://www.example.com/'], KEY, confirm_deployed=True)
    responses[('GET', f'https://www.example.com/{KEY}.txt')] = (200, 'someone-else')
    with pytest.raises(PermissionError, match='key file'):
        indexnow_ping.ping('www.example.com', ['https://www.example.com/'], KEY, confirm_deployed=True)
    assert all(method == 'GET' for method, _, _ in calls)


def test_rejects_foreign_urls_and_bad_keys(http):
    with pytest.raises(ValueError):
        indexnow_ping.ping('www.example.com', ['https://other.example/'], KEY, confirm_deployed=True)
    with pytest.raises(ValueError):
        indexnow_ping.ping('www.example.com', ['https://www.example.com/'], 'bad key!', confirm_deployed=True)
    with pytest.raises(ValueError):
        indexnow_ping.ping('www.example.com', [], KEY, confirm_deployed=True)


def test_pings_after_confirmation_and_verified_key(http):
    calls, responses = http
    responses[('GET', f'https://www.example.com/{KEY}.txt')] = (200, KEY + '\n')
    responses[('POST', indexnow_ping.ENDPOINT)] = (202, '')
    status = indexnow_ping.ping('www.example.com', ['https://www.example.com/', 'https://www.example.com/a'], KEY,
                                confirm_deployed=True)
    assert status == 202
    method, url, body = calls[-1]
    assert (method, url) == ('POST', indexnow_ping.ENDPOINT)
    assert json.loads(body) == {'host': 'www.example.com', 'key': KEY,
                                'keyLocation': f'https://www.example.com/{KEY}.txt',
                                'urlList': ['https://www.example.com/', 'https://www.example.com/a']}


def test_site_gate_never_imports_indexnow():
    from pathlib import Path
    gate = (Path(__file__).resolve().parents[1] / 'scripts/brand/site_gate.py').read_text()
    assert 'import indexnow' not in gate and 'indexnow_ping' not in gate.replace('indexnow_ping.py', '')
