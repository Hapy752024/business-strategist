import json

from scripts.marketing import link_ledger as ll
from scripts.marketing import link_prospects as lp

PAGE = b"""<html><head><title>Moving to Italy: resources</title><meta name="author" content="Laura Rossi"></head>
<body><script>var x = "<a href='https://competitor-a.com/hidden'>no</a>";</script>
<p>For the visa itself, <a href="https://www.competitor-a.com/guide">this elective residence guide</a> covers the consulate steps.
Then get a codice fiscale.</p><p>Questions? <a href="mailto:editor@expat-blog.com">email the editor</a> or use our
<a href="/contact">contact page</a>.</p></body></html>"""


def fetch_ok(url):
    return {'status': 200, 'final_url': url, 'raw': PAGE, 'content_type': 'text/html', 'redirects': []}


def test_prequalify_quotes_competitor_context_and_contacts():
    doc = ll.new_ledger('italyforretirees.com')
    ll.set_stage(doc, 'https://expat-blog.com/post', 'prospect', at='2026-10-31')
    ll.set_stage(doc, 'https://dead.com/p', 'prospect', at='2026-10-31')
    def fetcher(url):
        return fetch_ok(url) if 'expat-blog' in url else {'status': 404, 'final_url': url, 'raw': b'', 'content_type': 'text/html', 'redirects': []}
    rows = lp.prequalify(doc, {'competitor-a.com'}, max_rows=10, fetcher=fetcher)
    live, dead = rows
    assert live['page'] == 'live' and live['title'] == 'Moving to Italy: resources' and live['suggested'] == 'review'
    assert live['competitor_links'][0]['href'] == 'https://www.competitor-a.com/guide'
    assert 'elective residence guide' in live['competitor_links'][0]['context'] and 'hidden' not in json.dumps(live)
    assert live['contacts'] == {'mailto': ['mailto:editor@expat-blog.com'], 'contact_pages': ['https://expat-blog.com/contact'], 'author': 'Laura Rossi'}
    assert dead['page'] == 'dead' and dead['suggested'] == 'reject_dead'
    assert all(r['stage'] == 'prospect' for r in doc['rows'])  # report only


def test_check_indexed_matches_exact_url_and_tolerates_failure():
    assert lp.check_indexed('https://expat-blog.com/post', searcher=lambda q: {'organic': [{'link': 'https://expat-blog.com/post/'}]}) is True
    assert lp.check_indexed('https://expat-blog.com/post', searcher=lambda q: {'organic': [{'link': 'https://expat-blog.com/other'}]}) is False
    def boom(q):
        raise RuntimeError('no key')
    assert lp.check_indexed('https://expat-blog.com/post', searcher=boom) is None


def test_mentions_split_linked_from_unlinked_and_add_prospects():
    linked = b'<p>We like <a href="https://www.italyforretirees.com/check">Italy for Retirees</a>.</p>'
    unlinked = b'<p>The Italy for Retirees checklist was useful before our move.</p>'
    generic = b'<p>The cost of living in Italy for retirees is lower.</p>'
    pages = {'https://a.com/x': linked, 'https://b.com/y': unlinked, 'https://c.com/z': b'<p>nothing here</p>', 'https://d.com/g': generic,
             'https://www.google.com/goto?url=abc': unlinked}
    def fetcher(url):
        return {'status': 200, 'final_url': url, 'raw': pages[url], 'content_type': 'text/html', 'redirects': []}
    searcher = lambda q: {'organic': [{'link': u, 'title': u} for u in pages]}
    found = lp.find_mentions('Italy for Retirees', 'www.italyforretirees.com', searcher=searcher, fetcher=fetcher)
    assert found['query'] == '"Italy for Retirees" -site:italyforretirees.com'
    assert [m['source_url'] for m in found['linked']] == ['https://a.com/x']
    assert [m['source_url'] for m in found['unlinked']] == ['https://b.com/y'] and 'checklist' in found['unlinked'][0]['mention']
    assert [u['source_url'] for u in found['unchecked']] == ['https://c.com/z', 'https://d.com/g'] and found['results'] == 4
    doc = ll.new_ledger('italyforretirees.com')
    assert lp.add_mentions(doc, found, at='2026-10-31') == 1 and lp.add_mentions(doc, found, at='2026-10-31') == 0
    assert doc['rows'][0]['origin'] == 'unlinked_mention' and ll.validate(doc) == []


def test_diff_reports_new_and_gone_clean_domains():
    prev = {'retrieved_at': '2026-10-01', 'candidates': [{'source_domain': 'a.com', 'flags': [], 'domain_rank': 1}, {'source_domain': 'gone.com', 'flags': [], 'domain_rank': 1}, {'source_domain': 'spam.biz', 'flags': ['link_seller_page'], 'domain_rank': 9}]}
    cur = {'retrieved_at': '2026-11-01', 'candidates': [{'source_domain': 'a.com', 'flags': [], 'domain_rank': 1}, {'source_domain': 'new.org', 'flags': [], 'domain_rank': 400}, {'source_domain': 'spam.biz', 'flags': ['link_seller_page'], 'domain_rank': 9}]}
    d = lp.diff(prev, cur)
    assert [r['source_domain'] for r in d['new_domains']] == ['new.org'] and d['gone_domains'] == ['gone.com'] and d['unchanged'] == 1
