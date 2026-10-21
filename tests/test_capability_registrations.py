"""New provider capability registrations stay valid and discoverable."""
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
    assert 'subreddit_query_rows.py' in item['example'] and '--scope local' in item['setup']
