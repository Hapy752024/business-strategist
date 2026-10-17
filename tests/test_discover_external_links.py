import importlib.util
from pathlib import Path
import pytest

SPEC = importlib.util.spec_from_file_location('discover_external_links', Path(__file__).parents[1] / 'scripts/brand/discover_external_links.py')
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


def run(tmp_path, html):
    (tmp_path / 'page.html').write_text(html)
    return m.inventory([{'url': 'https://site.example/guide', 'file': 'page.html'}], tmp_path)


def test_inventory_deduplicates_and_preserves_occurrences(tmp_path):
    result = run(tmp_path, '<a href="https://RESOURCE.example:443/a#x">a</a><a href="//resource.example/a#y">b</a><a href="/internal">c</a>')
    assert len(result['links']) == 1
    assert result['links'][0]['url'] == 'https://resource.example/a'
    assert len(result['links'][0]['occurrences']) == 2
    assert result['network_checked'] is False


def test_inert_base_ignored_real_base_applies(tmp_path):
    result = run(tmp_path, '<template><base href="https://wrong.example/"><a href="https://hidden.example"></a></template><a href="item"></a><base href="https://resource.example/">')
    assert [r['url'] for r in result['links']] == ['https://resource.example/item']


def test_sensitive_and_non_http_values_never_leak(tmp_path):
    result = run(tmp_path, '<a href="https://example.com/?token=SECRET"></a><a href="https://USER:PASS@example.com/"></a><a href="mailto:PRIVATE@example.com"></a><a href="https://bad.example:invalid/a"></a>')
    assert result['links'] == []
    assert len(result['skipped']) == 4
    assert all(value not in str(result) for value in ['SECRET', 'USER', 'PASS', 'PRIVATE'])


def test_path_escape_rejected(tmp_path):
    with pytest.raises(ValueError, match='within'):
        m.inventory([{'url': 'https://site.example/', 'file': '../escape.html'}], tmp_path)


def test_page_credentials_rejected(tmp_path):
    with pytest.raises(ValueError, match='credential-free'):
        m.inventory([{'url': 'https://user:secret@site.example/', 'file': 'page.html'}], tmp_path)


def test_self_closing_template_remains_inert_in_html(tmp_path):
    result = run(tmp_path, '<template/><a href="https://hidden.example"></a></template><a href="https://visible.example"></a>')
    assert [row['url'] for row in result['links']] == ['https://visible.example/']


@pytest.mark.parametrize('base', ['https://[invalid', 'https://site.example:bad/', 'data:text/html,secret'])
def test_malformed_base_fails_explicitly_without_echoing_value(tmp_path, base):
    with pytest.raises(ValueError, match='invalid HTML base') as error:
        run(tmp_path, f'<base href="{base}"><a href="relative"></a>')
    assert base not in str(error.value)
