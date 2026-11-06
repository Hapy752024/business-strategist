import json

from scripts import provider_health as ph

BILLING = ph.load_config('provider-billing.json')['providers']


def row(result):
    return ph.advise(result, BILLING.get(result['provider'], {}), ['dataforseo_keywords'])


def test_status_maps_to_founder_action_with_where_to_go():
    funded = row({'provider': 'dataforseo', 'status': 'insufficient_credits'})
    assert funded['action'] == 'fund' and 'https://app.dataforseo.com/' in funded['todo']
    key = row({'provider': 'serper', 'status': 'missing_credentials', 'required_env': ['SERPER_API_KEY']})
    assert key['action'] == 'add_key' and 'SERPER_API_KEY' in key['todo'] and '~/.secrets' in key['todo']
    expired = row({'provider': 'meta', 'status': 'token_expired', 'credential_source': 'META_ACCESS_TOKEN'})
    assert expired['action'] == 'renew_key' and 'META_ACCESS_TOKEN' in expired['todo'] and '60 days' in expired['todo']
    assert row({'provider': 'hn', 'status': 'ok'})['action'] == 'ready'
    assert row({'provider': 'unknown', 'status': 'weird'})['action'] == 'check'


def test_sources_most_founders_cannot_get_are_optional_when_missing():
    for provider in ('tiktok', 'app_reviews'):
        assert row({'provider': provider, 'status': 'missing_credentials'})['action'] == 'optional'
    assert row({'provider': 'tiktok', 'status': 'invalid_credentials'})['action'] != 'optional'
    assert row({'provider': 'producthunt', 'status': 'missing_credentials'})['action'] == 'add_key'


def test_stale_rows_keep_their_observed_status():
    stale = row({'provider': 'serper', 'status': 'stale', 'observed_status': 'insufficient_credits',
                 'validated_at': '2026-09-27T11:26:05Z'})
    assert stale['action'] == 'fund' and stale['stale'] and stale['status'] == 'insufficient_credits'
    assert 'as of 2026-09-27' in ph.render([stale])


def test_report_sorts_actions_first_and_never_prints_secret_values():
    results = [{'provider': 'hn', 'status': 'ok'},
               {'provider': 'dataforseo', 'status': 'ok', 'balance_usd': 50.3, 'api_key': 'sk-secret-value'},
               {'provider': 'serper', 'status': 'insufficient_credits'}]
    rows = ph.report(results)
    assert [r['provider'] for r in rows][0] == 'serper'
    text = ph.render(rows) + json.dumps(rows)
    assert 'sk-secret-value' not in text
    assert '50.3 (balance_usd)' in text and 'Blocks' in text and 'serp_landscape' in text


def test_every_billing_entry_is_complete():
    kinds = ph.load_config('provider-billing.json')['billing_kinds']
    for name, entry in BILLING.items():
        assert entry['billing'] in kinds, name
        if entry['billing'] in {'prepaid', 'subscription', 'pay_as_you_go'}:
            assert entry.get('fund_url', '').startswith('https://'), name


def test_health_requests_route_to_the_evidence_scout_mode_without_a_gate():
    from scripts import route_workflow as router
    for request in ('Check the data sources', 'Which data sources work and what do I need to top up?',
                    'Run a provider health check'):
        packet = router.route_request(request)
        assert (packet['route_id'], packet['skill'], packet['mode']) == ('provider-health', 'evidence-scout', 'provider-health')
        assert not packet.get('gate_blocked')
        assert '.agents/skills/evidence-scout/references/provider-health.md' in packet['required_references']


def test_odd_validator_fields_never_become_key_names():
    odd = ph.advise({'provider': 'unlisted', 'status': 'missing_credentials',
                     'credential_source': {'google': None, 'apple_key': None}}, {}, [])
    assert odd['todo'].startswith('Add the key')
    keyless = ph.advise({'provider': 'x2', 'status': 'missing_credentials', 'credential_source': 'none (keyless)'}, {}, [])
    assert 'none' not in keyless['todo']
    assert ph.advise({'provider': 'meta', 'status': 'scope_denied'}, BILLING['meta'], [])['action'] == 'renew_key'
