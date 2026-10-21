"""New provider capability registrations stay valid and discoverable."""
from scripts import capability_lookup as cl


def test_dialog_reddit_mcp_registered_and_labelled_hosted():
    catalog = cl.load_catalog()
    assert cl.validate_catalog(catalog) == []
    item = next(i for i in catalog['capabilities'] if i['id'] == 'reddit_dialog_mcp')
    assert item['hosted_third_party'] is True and item['family'] == 'customer_pain'
    best = max(catalog['capabilities'], key=lambda i: cl.score(i, 'semantic reddit search across subreddits mcp'))
    assert best['id'] == 'reddit_dialog_mcp'


def test_trends_fallback_records_upstream_status():
    item = next(i for i in cl.load_catalog()['capabilities'] if i['id'] == 'google_trends')
    assert 'archived' in item['caveat'] and 'trends-checker' in item['caveat']
