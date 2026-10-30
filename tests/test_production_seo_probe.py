import pytest
from scripts.brand.production_seo_probe import analyze, search_console_owner_action

WWW = 'https://www.example.com'
APEX = 'https://example.com'
BODY_WORDS = ' '.join(['word'] * 300)


def page(url, *, canonical=None, og=None, title='Short title', robots='', extra=''):
    canonical = canonical or url
    og = og or canonical
    head = f'<title>{title}</title><link rel="canonical" href="{canonical}"><meta property="og:url" content="{og}">'
    if robots:
        head += f'<meta name="robots" content="{robots}">'
    return {'status': 200, 'body': f'<html><head>{head}</head><body><p>{BODY_WORDS}</p>{extra}</body></html>'}


def sitemap(*urls):
    locs = ''.join(f'<url><loc>{u}</loc></url>' for u in urls)
    return {'status': 200, 'body': f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{locs}</urlset>'}


def healthy():
    return {
        'robots': {'status': 200, 'body': f'User-Agent: *\nAllow: /\n\nSitemap: {WWW}/sitemap.xml\n'},
        'sitemap': sitemap(f'{WWW}/', f'{WWW}/guide'),
        'pages': {f'{WWW}/': page(f'{WWW}/'), f'{WWW}/guide': page(f'{WWW}/guide')},
    }


def test_consistent_production_host_passes():
    result = analyze(WWW, healthy())
    assert result['errors'] == [] and result['warnings'] == [] and result['limits'] == []


def test_canonical_host_that_redirects_is_caught():
    """Regression: site declares apex canonicals/sitemap while apex 308-redirects to www."""
    obs = {
        'robots': {'status': 200, 'body': f'Sitemap: {APEX}/sitemap.xml\n'},
        'sitemap': sitemap(f'{APEX}', f'{APEX}/guide'),
        'pages': {
            APEX: {'status': 308, 'location': f'{WWW}/'},
            f'{APEX}/guide': {'status': 308, 'location': f'{WWW}/guide'},
            f'{APEX}/sitemap.xml': {'status': 308, 'location': f'{WWW}/sitemap.xml'},
        },
    }
    errors = analyze(WWW, obs)['errors']
    assert any('robots.txt sitemap points at example.com' in e for e in errors)
    assert any('sitemap URL on example.com' in e for e in errors)
    assert any('redirects (308)' in e for e in errors)


def test_page_canonical_on_other_host_is_caught():
    obs = healthy()
    obs['pages'][f'{WWW}/guide'] = page(f'{WWW}/guide', canonical=f'{APEX}/guide')
    obs['pages'][f'{APEX}/guide'] = {'status': 308, 'location': f'{WWW}/guide'}
    errors = analyze(WWW, obs)['errors']
    assert any('/guide: canonical https://example.com/guide differs' in e for e in errors)
    assert any('https://example.com/guide: canonical URL redirects (308)' in e for e in errors)


def test_og_url_on_other_host_and_noindex_in_sitemap_are_errors():
    obs = healthy()
    obs['pages'][f'{WWW}/guide'] = page(f'{WWW}/guide', og=f'{APEX}/guide', robots='noindex, follow')
    errors = analyze(WWW, obs)['errors']
    assert any('og:url on example.com' in e for e in errors)
    assert any('listed in the sitemap but marked noindex' in e for e in errors)


def test_root_canonical_spellings_are_equivalent():
    obs = healthy()
    obs['pages'][f'{WWW}/'] = page(f'{WWW}/', canonical=WWW)
    assert analyze(WWW, obs)['errors'] == []


def test_long_title_thin_page_and_article_signals_warn_only():
    obs = healthy()
    obs['pages'][f'{WWW}/guide'] = {'status': 200, 'body': '<title>' + 'T' * 70 + f'</title><link rel="canonical" href="{WWW}/guide"><p>few words</p>'}
    result = analyze(WWW, obs, article_prefixes=('/guide',))
    assert result['errors'] == []
    joined = '\n'.join(result['warnings'])
    for expected in ['title is 70 characters', 'thin indexable page', 'no visible updated date', 'no sources section', 'no Article structured data']:
        assert expected in joined


def test_complete_article_has_no_article_warnings():
    extra = ('<time datetime="2026-10-30">30 October 2026</time><section id="sources"></section>'
             '<script type="application/ld+json">{"@type":"Article","headline":"x"}</script>')
    obs = healthy()
    obs['pages'][f'{WWW}/guide'] = page(f'{WWW}/guide', extra=extra)
    assert analyze(WWW, obs, article_prefixes=('/guide',))['warnings'] == []


@pytest.mark.parametrize('seen,ok', [
    ({'status': 308, 'location': f'{WWW}/'}, True),
    ({'status': 301, 'location': f'{WWW}/'}, True),
    ({'status': 302, 'location': f'{WWW}/'}, False),
    ({'status': 308, 'location': 'https://elsewhere.test/'}, False),
    ({'status': 'unreachable'}, False),
])
def test_secondary_domain_redirect_decision(seen, ok):
    obs = healthy(); obs['domains'] = {'old.test': seen}
    errors = analyze(WWW, obs, domains={'old.test': 'redirect'})['errors']
    assert (errors == []) is ok


def test_domain_requires_a_recorded_decision():
    obs = healthy(); obs['domains'] = {'old.test': {'status': 'unreachable'}}
    assert analyze(WWW, obs, domains={'old.test': 'lapse'})['errors'] == []
    assert any('domain decision must be one of' in e for e in analyze(WWW, obs, domains={'old.test': ''})['errors'])


def test_missing_robots_or_sitemap_fails():
    obs = healthy(); obs['robots'] = {'status': 404}; obs['sitemap'] = {'status': 'unreachable'}
    errors = analyze(WWW, obs)['errors']
    assert any(e.startswith('robots.txt: expected 200') for e in errors)
    assert any(e.startswith('sitemap: expected 200') for e in errors)


def test_unfetched_sitemap_url_is_a_limit_not_a_pass():
    obs = healthy(); del obs['pages'][f'{WWW}/guide']
    assert analyze(WWW, obs)['limits'] == [f'{WWW}/guide: not fetched']


def test_owner_action_row_uses_domain_property_and_production_sitemap():
    row = search_console_owner_action(WWW + '/', '2026-10-30')
    assert row.startswith('| search-console / proposed 2026-10-30 |')
    assert '`example.com`' in row and f'`{WWW}/sitemap.xml`' in row
    assert 'Import from Google Search Console' in row and row.count('|') == 6
