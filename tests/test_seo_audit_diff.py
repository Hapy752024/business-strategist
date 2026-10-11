from copy import deepcopy
import pytest
from scripts.brand.seo_checks import check,sitemap_urls
from scripts.brand.compare_seo_audits import compare


def payload():
    return {'base':'https://site.example/','inventory':[{'path':'/','expectedCanonical':'https://site.example/',
        'expectedIndexable':True,'sitemapExpected':True,'entry':True}],
        'pages':[{'path':'/','canonical':'https://site.example/','raw_html':'<link rel="canonical" href="https://site.example/">','robots':[],'links':[]}],
        'sitemaps':[{'body':'<urlset><url><loc>https://site.example/</loc></url></urlset>'}]}


@pytest.mark.parametrize('issue',['canonical','noindex','sitemap','unreachable','alternates'])
def test_declared_defects(issue):
    p=payload();row=p['inventory'][0];page=p['pages'][0]
    assert not check(p)['errors']
    if issue=='canonical':page['canonical']='https://site.example/wrong'
    if issue=='noindex':page['robots']=['noindex']
    if issue=='sitemap':p['sitemaps'][0]['body']='<urlset/>'
    if issue=='unreachable':row['entry']=False
    if issue=='alternates':row['alternates']={'de':'https://site.example/de'}
    assert check(p)['errors']


def test_preview_noindex_and_sitemap_xml_declarations():
    p=payload();p['inventory'][0]['expectedIndexable']=False;p['pages'][0]['robots']=['noindex']
    assert not check(p)['errors']
    with pytest.raises(ValueError):sitemap_urls('<!DOCTYPE a [<!ENTITY a SYSTEM "file:///etc/passwd">]><urlset/>')


def test_audit_comparison_requires_compatible_identity_and_dates():
    a={'schema_version':1,'checker_version':'v1','site_identity':'site','inventory_sha256':'abc','config_sha256':'abc',
       'coverage':{'complete':True,'routes':['/']},'source_revision':'one','checked_at':'2026-10-01T00:00:00Z','errors':['canonical']}
    b={**a,'source_revision':'two','checked_at':'2026-10-02T00:00:00Z','errors':['noindex']}
    report=compare(a,b)
    assert report['resolved']==['canonical'] and report['new_regressions']==['noindex']
    assert compare(a,{**b,'config_sha256':'changed'})['status']=='non_comparable'
    assert compare(b,a)['status']=='non_comparable'


def test_robots_policy_conflict_and_extended_syntax_remains_unmeasured():
    p=payload();p['inventory'][0]['expectedCrawlable']=True
    p['robots']='User-agent: *\nDisallow: /'
    assert any('robots access conflicts' in e for e in check(p)['errors'])
    p['robots']='User-agent: *\nDisallow: /*.pdf$'
    assert any('extended syntax' in e for e in check(p)['limits'])


def test_redirected_sitemap_url_and_uncaptured_index_children():
    p=payload()
    p['inventory'].append({'path':'/old','expectedCanonical':'https://site.example/old',
                           'redirect':{'status':301,'to':'/'}})
    p['sitemaps'][0]['body']='<urlset><url><loc>https://site.example/old</loc></url></urlset>'
    assert any('redirected/excluded' in e for e in check(p)['errors'])
    p['sitemaps'][0]['body']='<sitemapindex><sitemap><loc>https://site.example/pages.xml</loc></sitemap></sitemapindex>'
    assert any('children were not fully checked' in e for e in check(p)['limits'])


def test_preservation_coverage_cannot_disappear_in_comparison():
    a = {'schema_version':1,'checker_version':'seo-audit-v3','site_identity':'site','inventory_sha256':'a','config_sha256':'a',
         'coverage':{'complete':True,'routes':['/']},'source_revision':'one','checked_at':'2026-10-01T00:00:00Z',
         'errors':['missing estimator'], 'preservation':[{'path':'/','id':'estimate','width':390,'status':'fail'}]}
    b = {**deepcopy(a),'source_revision':'two','checked_at':'2026-10-02T00:00:00Z','errors':[]}
    b['preservation'][0]['status'] = 'pass'
    assert compare(a,b)['resolved'] == ['missing estimator']
    assert compare(a,{**b,'preservation':[]})['status'] == 'non_comparable'
    assert compare(a,{k:v for k,v in b.items() if k != 'preservation'})['status'] == 'non_comparable'
