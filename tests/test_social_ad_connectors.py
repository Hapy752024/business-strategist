"""Meta Ads MCP and Postiz connectors: read through MCP, every write only through scripts/marketing/execute.py."""
import json
import re
from pathlib import Path

from scripts.marketing.adapters import meta_ads, postiz

ROOT = Path(__file__).resolve().parents[1]
MCP = json.loads((ROOT / '.mcp.json').read_text())['mcpServers']
PERMS = json.loads((ROOT / '.claude/settings.json').read_text())['permissions']
PROVIDERS = json.loads((ROOT / 'config/marketing/providers.json').read_text())['providers']
DOC = (ROOT / 'references/ad-platform-connections.md').read_text()

# Write/mutating tools documented by Meta (Ads MCP tool pages, checked 2026-10-31).
META_WRITE_TOOLS = (
    'ads_create_campaign', 'ads_create_ad_set', 'ads_create_ad', 'ads_update_entity', 'ads_activate_entity',
    'ads_create_creative', 'ads_boost_ig_post', 'ads_create_custom_audience', 'ads_update_custom_audience',
    'ads_update_custom_audience_users', 'ads_delete_custom_audience',
    'ads_catalog_create', 'ads_catalog_update_catalog', 'ads_catalog_product_create', 'ads_catalog_update_product',
    'ads_catalog_delete_product', 'ads_catalog_create_product_set', 'ads_catalog_update_product_set',
    'ads_catalog_product_set_delete', 'ads_catalog_create_product_feed', 'ads_catalog_update_product_feed',
    'ads_catalog_create_product_feed_upload_session', 'ads_catalog_product_feed_delete', 'ads_catalog_create_feed_rule',
    'ads_catalog_product_feed_delete_rule', 'ads_catalog_event_source_connect', 'ads_catalog_event_source_disconnect',
    'ads_pixel_event_create', 'ads_pixel_event_update', 'ads_pixel_event_delete', 'ads_pixel_parameter_create',
    'ads_pixel_parameter_update', 'ads_pixel_parameter_delete',
    'ads_experiment_abtest_create_test', 'ads_experiment_abtest_update_test', 'ads_experiment_lift_create_test',
)
META_READ_TOOLS = ('ads_get_ad_accounts', 'ads_get_ad_entities', 'ads_insights_performance_trend', 'ads_get_errors',
                   'ads_get_dataset_quality', 'ads_account_get_activity_logs', 'ads_catalog_list_catalogs')
# Postiz MCP tools that create, change, publish or spend (docs.postiz.com/mcp/tools, checked 2026-10-31).
POSTIZ_WRITE_TOOLS = ('schedulePostTool', 'postSettingsTool', 'triggerTool', 'uploadFromUrlTool', 'generateImageTool',
                      'generateVideoTool', 'videoFunctionTool', 'clippingTool')
POSTIZ_READ_TOOLS = ('integrationList', 'groupList', 'integrationSchema', 'postsListTool', 'mediaListTool',
                     'mediaStatusTool', 'generateVideoOptions', 'clippingStatusTool')


def _matches(rule: str, tool: str) -> bool:
    return re.fullmatch(re.escape(rule).replace(r'\*', '.*'), tool) is not None


def _denied(tool: str) -> bool:
    return any(_matches(rule, tool) for rule in PERMS['deny'] if rule.startswith('mcp__'))


def test_meta_connection_scope_is_read_plus_mcp_management():
    meta = PROVIDERS['meta_ads']
    assert sorted(meta['requested_permissions']) == ['ads_mcp_management', 'ads_read']
    assert 'ads_management' not in json.dumps(meta['requested_permissions'])
    assert meta['status'] == 'read_connector_available' and meta['mcp_server'] == 'meta-ads'
    assert meta['writes'] == 'scripts/marketing/execute.py'
    assert 'ads_management' not in json.dumps({k: v for k, v in MCP['meta-ads'].items() if not k.startswith('_')})
    section = DOC.split('### Meta', 1)[1].split('\n### ', 1)[0]
    assert 'ads_mcp_management' in section and 'ads_read' in section
    for sentence in re.split(r'(?<=[.;])\s', DOC):
        if '`ads_management`' in sentence:
            assert re.search(r'\b(not|never|Do not)\b', sentence), sentence


def test_meta_and_postiz_mcp_entries_exist():
    assert MCP['meta-ads']['type'] == 'http' and MCP['meta-ads']['url'] == 'https://mcp.facebook.com/ads'
    assert 'headers' not in MCP['meta-ads'], 'Meta uses client-side OAuth; no token header in the repo'
    postiz_entry = MCP['postiz']
    assert postiz_entry['type'] == 'http' and postiz_entry['url'].startswith('${POSTIZ_BASE_URL')
    assert postiz_entry['url'].endswith('/mcp')
    assert postiz_entry['headers'] == {'Authorization': 'Bearer ${POSTIZ_API_KEY:-}'}


def test_meta_and_postiz_write_tools_denied_and_nothing_allowed():
    for tool in META_WRITE_TOOLS:
        assert 'mcp__meta-ads__' + tool in PERMS['deny'], tool
    for tool in POSTIZ_WRITE_TOOLS:
        assert 'mcp__postiz__' + tool in PERMS['deny'], tool
    for tool in META_READ_TOOLS:
        assert not _denied('mcp__meta-ads__' + tool), tool
    for tool in POSTIZ_READ_TOOLS:
        assert not _denied('mcp__postiz__' + tool), tool
    assert not [a for a in PERMS['allow'] if a.startswith('mcp__')]


def test_meta_write_globs_catch_undocumented_mutations():
    for hypothetical in ('ads_create_lead_form', 'ads_update_budget', 'ads_delete_campaign', 'ads_activate_ad_set',
                         'ads_boost_fb_post'):
        assert _denied('mcp__meta-ads__' + hypothetical), hypothetical


SECRET_PATTERNS = (r'EAA[A-Za-z0-9]{20,}', r'\bsk-[A-Za-z0-9_-]{8,}', r'\bpos_[A-Za-z0-9]{8,}', r'ya29\.',
                   r'apify_api_[A-Za-z0-9]{8,}', r'(?i)bearer\s+(?!\$\{)[A-Za-z0-9._-]{8,}')


def test_no_literal_tokens_in_mcp_json():
    for name, server in MCP.items():
        for field in ('env', 'headers'):
            for key, value in (server.get(field) or {}).items():
                stripped = re.sub(r'\$\{[A-Z0-9_]+(:-[^}]*)?\}', '', value)
                assert stripped.strip() in ('', 'Bearer'), f'{name}.{field}.{key} must reference an env var only'
        text = json.dumps({k: v for k, v in server.items() if not k.startswith('_')})
        for pattern in SECRET_PATTERNS:
            assert not re.search(pattern, text), f'{name} contains a literal credential ({pattern})'
        assert not re.search(r'/mcp/[^"$/]{6,}', server.get('url', '')), f'{name} embeds a key in its URL'


def test_postiz_provider_documented_not_connected_with_owner_steps():
    entry = PROVIDERS['postiz']
    assert entry['status'] == 'documented_not_connected' and entry['mcp_server'] == 'postiz'
    assert entry['writes'] == 'scripts/marketing/execute.py'
    steps = ' '.join(entry['owner_steps'])
    assert 'postiz-docker-compose' in steps and 'POSTIZ_API_KEY' in steps and 'POSTIZ_BASE_URL' in steps
    section = DOC.split('### Scheduling (Postiz', 1)[1].split('\n## ', 1)[0]
    for needle in ('gitroomhq/postiz-docker-compose', 'Settings', 'POSTIZ_API_KEY', '/mcp', '/public/v1'):
        assert needle in section, needle


def test_meta_adapter_uses_current_graph_version_and_explicit_budget_sharing():
    request = {'ad_account_id': '1234', 'name': 'Pilot', 'objective': 'OUTCOME_TRAFFIC', 'spend_cap': 10000}
    assert meta_ads.validate(request, {}) == []
    [call] = meta_ads.describe(request, {})
    assert call['url'] == 'https://graph.facebook.com/v26.0/act_1234/campaigns'
    assert call['body']['is_adset_budget_sharing_enabled'] is False and call['body']['status'] == 'PAUSED'
    with_budget = dict(request, daily_budget=2000)
    assert 'is_adset_budget_sharing_enabled' not in meta_ads.describe(with_budget, {})[0]['body']
    assert meta_ads.validate(dict(request, is_adset_budget_sharing_enabled=True), {}) == []


def test_postiz_adapter_targets_backend_public_api():
    [call] = postiz.describe({'date': '2026-11-05T10:00:00Z', 'posts': []}, {})
    assert call['url'] == '{POSTIZ_BASE_URL}/public/v1/posts'
    assert 'backend' in (postiz.__doc__ or '') and '/api/public/v1' in (postiz.__doc__ or '')
