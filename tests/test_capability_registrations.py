"""New provider capability registrations stay valid and discoverable."""
import json
from pathlib import Path

from scripts import capability_lookup as cl


def test_dialog_reddit_mcp_registered_and_labelled_hosted():
    catalog = cl.load_catalog()
    assert cl.validate_catalog(catalog) == []
    item = next(i for i in catalog['capabilities'] if i['id'] == 'reddit_dialog_mcp')
    assert item['hosted_third_party'] is True and item['family'] == 'community_discovery'
    best = max(catalog['capabilities'], key=lambda i: cl.score(i, 'semantic reddit search across subreddits mcp'))
    assert best['id'] == 'reddit_dialog_mcp'


def test_trends_fallback_records_upstream_status():
    item = next(i for i in cl.load_catalog()['capabilities'] if i['id'] == 'google_trends')
    assert 'archived' in item['caveat'] and 'trends-checker' in item['caveat']


def test_dialog_entry_is_discovery_only_with_collector_handoff():
    item = next(i for i in cl.load_catalog()['capabilities'] if i['id'] == 'reddit_dialog_mcp')
    assert item['family'] == 'community_discovery' and item['evidence_strength'] == 'none_discovery_only'
    assert 'subreddit_query_rows.py' in item['example'] and 'project .mcp.json' in item['setup']


def capability(cap_id):
    path = Path(__file__).resolve().parents[1] / 'config' / 'source-capabilities.json'
    caps = json.loads(path.read_text())['capabilities']
    return next(c for c in caps if c['id'] == cap_id)


def test_reddit_capability_declares_sunset_and_fallbacks():
    cap = capability('reddit')
    assert cap['sunset']['public_api_end'] == '2027-03-31'
    assert cap['sunset']['fallback_order'][0] == 'apify_reddit'


def test_reddit_archive_and_scrapecreators_capabilities():
    sc = capability('scrapecreators_reddit')
    assert sc['collector_provider'] == 'scrapecreators_reddit' and sc['requires_env'] == ['SCRAPE_CREATORS_API_KEY']
    ar = capability('arctic_shift')
    assert ar['collector_provider'] == 'arctic_shift' and 'subreddit' in ar['caveat'] and 'volunteer' in ar['caveat'].lower()


def test_serp_landscape_registered_with_unobserved_serper_fallback():
    cap = capability('serp_landscape')
    assert cap['family'] == 'demand_proxy' and cap['requires_env'] == ['SERPAPI_API_KEY']
    roles = {p['id']: p for p in cap['providers']}
    assert roles['serpapi']['role'] == 'primary' and roles['serper_search']['ads_status'] == 'unobserved'
    assert 'not customer demand' in cap['caveat'] and 'unpersonalised' in cap['caveat']
