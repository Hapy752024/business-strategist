import pytest
from scripts.brand.seo_checks import check


def payload(expected='https://example.com', html='https://example.com', dom='https://example.com/'):
    return {
        'base': 'http://localhost:3012',
        'inventory': [{'path': '/', 'expectedCanonical': expected, 'expectedIndexable': True,
                       'sitemapExpected': True}],
        'pages': [{'path': '/', 'canonical': dom, 'final_url': 'http://localhost:3012/',
                   'raw_html': f'<link rel="canonical" href="{html}">'}],
        'sitemaps': [{'body': '<urlset><url><loc>https://example.com</loc></url></urlset>'}],
    }


@pytest.mark.parametrize('expected', ['https://example.com', 'https://example.com/'])
def test_equivalent_root_http_dom_and_sitemap_urls_pass(expected):
    result = check(payload(expected=expected))
    assert result['errors'] == []
    assert result['limits'] == []


@pytest.mark.parametrize('mismatch', ['https://example.com/wrong', 'https://example.com/?variant=wrong'])
def test_root_normalization_does_not_hide_path_or_query_mismatch(mismatch):
    result = check(payload(html=mismatch, dom=mismatch))
    assert any('canonical differs' in error for error in result['errors'])
