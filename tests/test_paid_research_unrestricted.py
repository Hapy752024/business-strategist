"""Paid research sources run without a default cap or an approval step (AGENTS.md spend policy)."""
import json
from pathlib import Path

from scripts.evidence_scout import collect_ads

ROOT = Path(__file__).resolve().parents[1]
PAID_RESEARCH = ('dataforseo_keywords', 'dataforseo_backlinks', 'serp_landscape', 'vc_investment_activity',
                 'apify_ads', 'apify_brightdata', 'sonar')


def test_paid_research_capabilities_are_standing_authorized():
    caps = json.loads((ROOT / 'config/source-capabilities.json').read_text())['capabilities']
    items = caps if isinstance(caps, dict) else {c['id']: c for c in caps}
    for cap_id in PAID_RESEARCH:
        cap = items[cap_id]
        assert cap['approval_required'] is False, cap_id
        assert cap['authorization_policy'].startswith('standing_authorized_no_cap'), cap_id
        text = json.dumps(cap)
        for flag in ('--max-keywords', '--max-cost-usd', '--max-credits', '--max-searches', '--approve-paid'):
            assert flag not in text, (cap_id, flag)


def test_apify_ads_fallback_runs_without_approval(monkeypatch):
    sent = []
    monkeypatch.setattr(collect_ads, 'get_secret', lambda name: (name, 'token'))
    monkeypatch.setattr(collect_ads, 'http_post', lambda url, headers, data: sent.append(url) or {'ok': True, 'json': []})
    records, status = collect_ads.collect_apify_ads([('acme', 'competitor')], ['US'], 5, 'actor/name', [])
    assert sent and status.get('status') != 'approval_required'
