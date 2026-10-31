import json
from pathlib import Path

import pytest

from scripts.marketing import connections

ROOT = Path(__file__).resolve().parents[1]
PROVIDERS = ('gsc', 'ga4', 'google_ads')


@pytest.fixture
def no_adc(monkeypatch, tmp_path):
    monkeypatch.delenv('GOOGLE_APPLICATION_CREDENTIALS', raising=False)
    monkeypatch.setenv('HOME', str(tmp_path / 'home'))
    monkeypatch.setenv('XDG_CONFIG_HOME', str(tmp_path / 'home/.config'))
    monkeypatch.setenv('CLOUDSDK_CONFIG', str(tmp_path / 'home/gcloud'))


@pytest.mark.parametrize('provider', PROVIDERS)
def test_probe_missing_adc_reports_unconnected(provider, no_adc, tmp_path):
    def forbidden(*a, **k):
        raise AssertionError('no network call may happen without credentials')
    store = tmp_path / 'marketing-connections.json'
    result = connections.probe(provider, request=forbidden, store=store)
    assert result['provider'] == provider and result['status'] == 'unconnected'
    assert result['checked_at'] and result['owner_steps']
    assert any('application-default' in s or 'Application Default' in s for s in result['owner_steps'])
    assert json.loads(store.read_text())['probes'][provider]['status'] == 'unconnected'


def test_probe_unknown_provider_rejected(tmp_path):
    with pytest.raises(ValueError):
        connections.probe('meta_ads', store=tmp_path / 's.json')


@pytest.mark.parametrize('provider,status,expected', [('gsc', 200, 'connected'), ('ga4', 200, 'connected'),
                                                      ('google_ads', 200, 'connected'), ('ga4', 403, 'error')])
def test_probe_with_adc_uses_read_request_only(provider, status, expected, no_adc, tmp_path, monkeypatch):
    cred = tmp_path / 'adc.json'
    cred.write_text('{"type": "authorized_user", "refresh_token": "SECRET-REFRESH"}')
    monkeypatch.setenv('GOOGLE_APPLICATION_CREDENTIALS', str(cred))
    seen = []

    def request(method, url, scopes):
        seen.append((method, url, tuple(scopes)))
        return status
    result = connections.probe(provider, request=request, store=tmp_path / 's.json')
    assert result['status'] == expected
    assert len(seen) == 1 and seen[0][0] == 'GET'
    assert all(s.endswith('.readonly') or s.endswith('/adwords') for s in seen[0][2])
    assert 'SECRET-REFRESH' not in json.dumps(result) + (tmp_path / 's.json').read_text()
    if expected == 'error':
        assert result['owner_steps']


def test_probe_request_exception_is_error_without_leaking(no_adc, tmp_path, monkeypatch):
    cred = tmp_path / 'adc.json'
    cred.write_text('{}')
    monkeypatch.setenv('GOOGLE_APPLICATION_CREDENTIALS', str(cred))

    def boom(method, url, scopes):
        raise RuntimeError('token ya29.LEAK failed')
    result = connections.probe('gsc', request=boom, store=tmp_path / 's.json')
    assert result['status'] == 'error' and 'ya29' not in json.dumps(result)


def test_providers_and_mcp_entries_are_read_only_and_pinned():
    providers = json.loads((ROOT / 'config/marketing/providers.json').read_text())['providers']
    for name in PROVIDERS:
        assert providers[name]['status'] == 'read_connector_available'
        assert 'probe' in providers[name]['connection_check']
    assert providers['tiktok_ads']['status'] == providers['postiz']['status'] == 'documented_not_connected'
    servers = json.loads((ROOT / '.mcp.json').read_text())['mcpServers']
    for name in ('analytics-mcp', 'google-ads-mcp', 'search-console-mcp'):
        text = json.dumps({k: v for k, v in servers[name].items() if not k.startswith('_')})
        assert '--allow-write' not in text and 'BING_API_KEY' not in text and 'DEVELOPER_TOKEN' not in text.upper()
        assert '==' in text or '@2.' in text or '@0.' in text, 'version must be pinned'


def test_search_console_write_tools_denied_and_not_allowed():
    perms = json.loads((ROOT / '.claude/settings.json').read_text())['permissions']
    assert 'search-console-mcp' in json.loads((ROOT / '.mcp.json').read_text())['mcpServers']
    for tool in ('sites_manage', 'sitemaps_submit', 'sitemaps_delete', 'indexing_submit', 'accounts_manage',
                 'adsense_accounts', 'adsense_report', 'adsense_payments_alerts'):
        assert 'mcp__search-console-mcp__' + tool in perms['deny']
    assert 'Bash(rm -rf *)' in perms['deny']
    assert not [a for a in perms['allow'] if a.startswith('mcp__')]
