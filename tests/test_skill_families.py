"""Phase 4 skill-family merges: merged skills keep every former route ID and old names still resolve."""
import json
import re
import subprocess
from pathlib import Path

import pytest

from scripts import route_workflow

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / '.agents/skills'

# merged skill -> former skills it absorbed. Later family merges add one entry.
FAMILIES = {
    'brand-identity': [
        'brand-designer', 'brand-discovery-interviewer', 'brand-workspace-manager', 'brand-guideline-researcher',
        'brand-typography-researcher', 'brand-strategy-director', 'brand-guidelines-writer', 'brand-exporter',
        'brand-quality-reviewer',
    ],
    'brand-ui-system': [
        'brand-ui-kit-producer', 'brand-ui-component-producer', 'brand-motion-designer', 'brand-frontend-app-designer',
    ],
    'competitor-research': ['competitor-scout', 'competitive-landscape-builder', 'competitor-marketing-analyzer'],
    'challenge-review': ['startup-challenge-panel', 'strategy-draft-tournament', 'service-customer-perspective-challenger'],
    'precedent-research': ['business-archetype-playbook-researcher', 'growth-case-analyzer'],
    'marketing': ['marketing-strategy-builder', 'social-digital-marketing-planner', 'social-media-idea-validator'],
    'positioning-gtm': ['archetype-gtm-strategist', 'company-operating-system'],
    'evidence-scout': ['interview-bridge'],
}
# Hosts that absorbed a former skill keep their own pre-existing routes as they were (route ID, mode or no mode);
# only the absorbed skills' routes gain a mode and a references/<mode>.md.
ABSORBING_HOSTS = {'evidence-scout'}
FORMER = [(merged, former) for merged, formers in FAMILIES.items() for former in formers]
# Paths stay in git history; docs/ and .superpowers/ are dated records of that history. The research-business-plan
# eval is a completed recorded comparison: its manifest snapshot paths are pinned to its baseline revision and results.
# evals/non-video/ holds a digest-pinned frozen baseline snapshot whose manifest keys name files in that snapshot;
# the workflow-quality manifest's baseline_renames name pre-merge paths read at its baseline revision.
HISTORY_PREFIXES = ('docs/', '.superpowers/', 'evals/research-business-plan/', 'evals/non-video/',
                    'evals/workflow-quality/manifest.json')


def _routes():
    return {route['id']: route for route in route_workflow.load_routes()}


def _words(path):
    return len(path.read_text(encoding='utf-8').split())


@pytest.mark.parametrize('merged', sorted(FAMILIES))
def test_merged_skill_has_one_skill_md_and_a_reference_per_mode(merged):
    skill_md = SKILLS / merged / 'SKILL.md'
    assert skill_md.is_file(), f'{merged} missing'
    assert _words(skill_md) <= 450
    routes = _routes()
    modes = [route.get('mode') for route in routes.values() if route['skill'] == merged]
    if merged in ABSORBING_HOSTS:
        modes = [routes[route_workflow.SKILL_ALIASES[former]].get('mode') for former in FAMILIES[merged]]
    assert None not in modes and len(modes) == len(set(modes)), modes
    assert len(modes) >= len(FAMILIES[merged])
    for mode in modes:
        assert (SKILLS / merged / 'references' / f'{mode}.md').is_file(), f'{merged}: references/{mode}.md missing'


@pytest.mark.parametrize('merged,former', FORMER)
def test_former_skill_directory_is_gone_and_its_route_is_repointed(merged, former):
    assert not (SKILLS / former).exists()
    assert not (ROOT / '.claude/skills' / former).exists()
    route_id = route_workflow.SKILL_ALIASES[former]
    route = _routes()[route_id]
    assert route['skill'] == merged and route.get('mode'), route


@pytest.mark.parametrize('merged,former', FORMER)
def test_former_name_resolves_to_its_route_and_names_the_new_skill(merged, former):
    packet = route_workflow.route_request('explicit specialist task', intent=former, check_skill=merged)
    assert packet['route_id'] == route_workflow.SKILL_ALIASES[former]
    assert packet['skill'] == merged
    assert merged in packet['alias_note'] and former in packet['alias_note']


@pytest.mark.parametrize('merged,former', FORMER)
def test_dispatch_check_with_a_former_name_explains_the_merge(merged, former):
    with pytest.raises(ValueError, match=f'merged into {merged}'):
        route_workflow.route_request('explicit specialist task', intent=former, check_skill=former)


@pytest.mark.parametrize('merged', sorted(FAMILIES))
def test_bare_merged_skill_intent_lists_its_route_ids(merged):
    if merged in {route['id'] for route in _routes().values()}:
        # A host whose own route ID is its skill name keeps resolving the bare name to that route.
        assert route_workflow.route_request('explicit specialist task', intent=merged)['route_id'] == merged
        return
    with pytest.raises(ValueError) as excinfo:
        route_workflow.route_request('explicit specialist task', intent=merged)
    for route_id in (route['id'] for route in _routes().values() if route['skill'] == merged):
        assert route_id in str(excinfo.value)


def test_catalog_lists_only_merged_skills():
    catalog = json.loads((ROOT / 'config/skill-catalog.json').read_text(encoding='utf-8'))
    text = json.dumps(catalog)
    for merged, former in FORMER:
        assert former not in catalog['skills']
        assert f'"{former}"' not in text, former
    for merged in FAMILIES:
        assert len(catalog['skills'][merged]['required_references']) <= 3


def test_no_file_outside_history_mentions_former_skill_directories():
    names = '|'.join(re.escape(former) for _, former in FORMER)
    pattern = re.compile(rf'(?:skills/|\.\./)(?:{names})(?![\w-])')
    files = subprocess.run(['git', 'ls-files'], cwd=ROOT, text=True, capture_output=True, check=True).stdout.split()
    offenders = []
    for rel in files:
        if rel.startswith(HISTORY_PREFIXES) or not (ROOT / rel).is_file():
            continue
        try:
            text = (ROOT / rel).read_text(encoding='utf-8')
        except UnicodeDecodeError:
            continue
        offenders += [f'{rel}: {m.group(0)}' for m in pattern.finditer(text)]
    assert offenders == [], '\n'.join(offenders)


BRAND_ROUTE_IDS = [
    'standalone-brand', 'brand-research', 'app-ui', 'brand-discovery-interviewer', 'brand-exporter',
    'brand-guidelines-writer', 'brand-motion-designer', 'brand-quality-reviewer', 'brand-strategy-director',
    'brand-typography-researcher', 'brand-ui-component-producer', 'brand-ui-kit-producer', 'brand-workspace-manager',
]


# requires_pain_gate per brand route as frozen at 74e72de (before the merge).
BRAND_PAIN_GATE = {
    'standalone-brand': True, 'brand-research': False, 'app-ui': True, 'brand-discovery-interviewer': False,
    'brand-exporter': True, 'brand-guidelines-writer': True, 'brand-motion-designer': True,
    'brand-quality-reviewer': True, 'brand-strategy-director': True, 'brand-typography-researcher': False,
    'brand-ui-component-producer': True, 'brand-ui-kit-producer': True, 'brand-workspace-manager': False,
}


def test_brand_route_ids_unchanged():
    routes = _routes()
    assert len(BRAND_ROUTE_IDS) == 13 and set(BRAND_PAIN_GATE) == set(BRAND_ROUTE_IDS)
    for route_id in BRAND_ROUTE_IDS:
        assert route_id in routes, route_id
        assert routes[route_id]['skill'] in FAMILIES
        assert bool(routes[route_id].get('requires_pain_gate', False)) is BRAND_PAIN_GATE[route_id], route_id


@pytest.mark.parametrize('request_text,expected_route', [
    ('Build React components for my Next.js landing page', 'website-build'),
    ('Add React components to my website hero section', 'clarify'),
    ('fix the design tokens on my website', 'clarify'),
])
def test_website_requests_do_not_route_to_brand_ui_system(request_text, expected_route):
    packet = route_workflow.route_request(request_text)
    assert packet['skill'] != 'brand-ui-system'
    assert packet['route_id'] == expected_route


# Plain-text requests near the competitor family's boundary, frozen from the router at 935f5fc (before the merge).
@pytest.mark.parametrize('request_text,expected_route', [
    ('Find competitors for my invoice automation idea', 'competitor-discovery'),
    ('Map the competitive landscape and similar companies abroad', 'competitive-landscape'),
    ('competitor analysis for my bakery', 'competitive-landscape'),
    ('Analyze competitor website positioning and CTA', 'competitor-analysis'),
    ('Analyze competitor pricing for dog walking apps', 'competitor-analysis'),
    ('Monitor competitor pricing and track competitor changes', 'competitor-monitoring'),
    ('Build a landing page that beats our competitors', 'website-build'),
    ('Write marketing messaging that differentiates us from competitors', 'marketing-strategy'),
    ('Research which customers complain about competitor X', 'clarify'),
])
def test_competitor_boundary_routes_unchanged(request_text, expected_route):
    assert route_workflow.route_request(request_text)['route_id'] == expected_route


@pytest.mark.parametrize('request_text,expected_route', [
    ('Find competitors for my meal-planning app', 'competitor-discovery'),
    ('Build the competitive landscape with similar companies', 'competitive-landscape'),
    ('Analyze competitor website and competitor pricing', 'competitor-analysis'),
])
def test_competitor_research_plain_text_infers_its_mode(request_text, expected_route):
    assert route_workflow.infer_mode('competitor-research', request_text)[0] == expected_route


# Plain-text requests near the challenge family's boundary. Unchanged against 935f5fc except the new specific
# phrases, which move requests from clarification to their mode; a compound request now asks for scope.
@pytest.mark.parametrize('request_text,expected_route', [
    ('Run a startup challenge panel on my launch plan', 'startup-challenge-panel'),
    ('Red-team my business plan', 'startup-challenge-panel'),
    ('Compare strategy drafts for our pricing', 'strategy-draft-tournament'),
    ('Compare competing strategy drafts for launch', 'strategy-draft-tournament'),
    ('Do a customer perspective review of my relocation service', 'service-customer-perspective-challenger'),
    ('Do a buyer perspective review of our insurance service', 'service-customer-perspective-challenger'),
    ('Generate alternative go-to-market strategies and pick the best', 'gtm-strategy'),
    ('Challenge my marketing strategy', 'marketing-strategy'),
    ('Write landing page copy from the buyer perspective', 'website-build'),
    ('Write ad copy for our fixed-scope service', 'marketing-strategy'),
    ('Pressure-test this idea: software for care homes', 'idea-validation'),
    ('Red-team my website security', 'clarify'),
    ('Red team my business plan and build the GTM strategy', 'clarify'),
])
def test_challenge_boundary_routes(request_text, expected_route):
    assert route_workflow.route_request(request_text)['route_id'] == expected_route


def test_challenge_protocols_are_separate_and_complete():
    refs = SKILLS / 'challenge-review' / 'references'
    panel = (refs / 'panel.md').read_text(encoding='utf-8')
    tournament = (refs / 'tournament.md').read_text(encoding='utf-8')
    customer = (refs / 'customer-perspective.md').read_text(encoding='utf-8')
    assert 'Decision Arbiter' in panel and 'cross-examination' in panel
    assert 'Judge Round' in tournament and 'Feedback Round' in tournament
    for marker in ('Evidence hierarchy', 'Customer-role cross-examination', 'Behavioral validation', 'Simulated customer voice'):
        assert marker in customer, marker
    assert 'Judge Round' not in panel + customer and 'Decision Arbiter' not in tournament + customer
    assert (refs / 'regional-lenses.md').is_file()


def test_precedent_modes_state_operator_lessons_are_not_demand_evidence():
    refs = SKILLS / 'precedent-research' / 'references'
    for mode in ('playbook', 'case'):
        text = (refs / f'{mode}.md').read_text(encoding='utf-8').lower()
        assert 'lessons are not demand evidence' in text, mode


# Plain-text requests near the precedent family's boundary, unchanged against 935f5fc (no match phrases changed).
@pytest.mark.parametrize('request_text,expected_route', [
    ('Find founder playbooks for B2B SaaS in Europe', 'business-archetype-playbook-researcher'),
    ('operator playbooks for local cleaning services', 'business-archetype-playbook-researcher'),
    ('Analyze a company growth case: Airbnb', 'growth-case-analyzer'),
    ('analyze a company failure like Homejoy', 'growth-case-analyzer'),
    ('How did similar startups get their first customers?', 'gtm-strategy'),
    ('Build a go-to-market strategy to get our first customers', 'gtm-strategy'),
    ('Find customer problems in independent elder care', 'market-discovery'),
    ('Research comparable businesses abroad', 'clarify'),
])
def test_precedent_boundary_routes_unchanged(request_text, expected_route):
    assert route_workflow.route_request(request_text)['route_id'] == expected_route


# Plain-text requests near the marketing family's boundary. Frozen from the router at 33710cc (before the merge);
# the rows marked "new" moved from clarification to their mode through the specific match phrases added in the merge.
@pytest.mark.parametrize('request_text,expected_route', [
    ('Create a marketing strategy for my bakery', 'marketing-strategy'),
    ('Write ad copy for our fixed-scope service', 'marketing-strategy'),
    ('Research SEO keywords and build a keyword-to-page map', 'seo-page-planning'),
    ('Create a paid social media plan and content calendar', 'social-marketing'),
    ('Plan my social media for the next quarter: platforms and a posting calendar', 'social-marketing'),  # new
    ('Build an organic social plan for Instagram', 'social-marketing'),  # new
    ('Validate a content idea: a YouTube channel about mortgage basics', 'social-media-idea-validator'),
    ('Validate my channel idea: TikTok videos for insurance brokers', 'social-media-idea-validator'),  # new
    ('Give me content ideas for Instagram', 'clarify'),
    ('Find customer problems people share on social media about meal kits', 'market-discovery'),
    ('Build a landing page for our social media agency', 'website-build'),
    ('Optimize website SEO and SEO content for the landing page', 'website-build'),
    ('Monitor competitor social media and track competitor changes', 'competitor-monitoring'),
    ('Build a go-to-market strategy to get our first customers', 'gtm-strategy'),
    ('Set up marketing campaign for the launch', 'marketing-campaign-setup'),
    ('Research what customers say on social media about invoicing', 'clarify'),
])
def test_marketing_boundary_routes(request_text, expected_route):
    assert route_workflow.route_request(request_text)['route_id'] == expected_route


@pytest.mark.parametrize('request_text,expected_route', [
    ('Write a marketing strategy for my ceramics shop', 'marketing-strategy'),
    ('Do keyword research for our plumbing pages', 'seo-page-planning'),
    ('Plan my social media and a posting calendar for Instagram', 'social-marketing'),
    ('Validate my content idea before we film it', 'social-media-idea-validator'),
])
def test_marketing_plain_text_infers_its_mode(request_text, expected_route):
    assert route_workflow.infer_mode('marketing', request_text)[0] == expected_route


def test_marketing_modes_keep_their_contracts():
    refs = SKILLS / 'marketing' / 'references'
    seo = (refs / 'seo-page-planning.md').read_text(encoding='utf-8')
    for marker in ('keyword_map.py merge', 'keyword_volume.py', 'traffic_potential', 'business_potential',
                   'serp_shape', 'difficulty', 'ai_answerable', 'keyword-map.schema.json'):
        assert marker in seo, marker
    validation = (refs / 'channel-validation.md').read_text(encoding='utf-8')
    for marker in ('Gate 1', 'Gate 6', 'INSUFFICIENT EVIDENCE', 'GO-as-assist', '[DATA UNAVAILABLE]'):
        assert marker in validation, marker
    social = (refs / 'social.md').read_text(encoding='utf-8')
    assert 'Sequencing Gate' in social and 'Risk Review' in social
    assert 'Customer-Perspective Challenge Pass' in (refs / 'strategy.md').read_text(encoding='utf-8')
    for name in ('campaign-execution.md', 'paid-campaign-planning.md', 'product-marketing-context.md'):
        assert (refs / name).is_file(), name


def test_marketing_modes_keep_their_gates():
    routes = _routes()
    for route_id in ('marketing-strategy', 'seo-page-planning', 'social-marketing'):
        assert routes[route_id]['requires_pain_gate'] is True, route_id
    assert not routes['social-media-idea-validator'].get('requires_pain_gate')
    modes = json.loads((ROOT / 'config/skill-catalog.json').read_text(encoding='utf-8'))['skills']['marketing']['modes']
    stages = ['intake', 'segment_selection', 'customer_profile', 'problem_validation', 'opportunity_risk']
    assert modes['strategy']['strategy_stage_prerequisites'] == stages + ['operator_playbook']
    assert modes['seo-page-planning']['strategy_stage_prerequisites'] == stages + ['operator_playbook']
    assert modes['social']['strategy_stage_prerequisites'] == stages
    assert not modes['channel-validation'].get('strategy_stage_prerequisites')


STAGES = ['intake', 'segment_selection', 'customer_profile', 'problem_validation', 'opportunity_risk']


def test_positioning_gtm_modes_keep_their_gates():
    """Gate fields as frozen at 3f1635c: all three routes pain-gated; GTM and positioning keep six strategy stages,
    operations (formerly company-operating-system) has none."""
    routes = _routes()
    for route_id in ('gtm-strategy', 'business-positioning', 'company-operations'):
        assert routes[route_id]['requires_pain_gate'] is True, route_id
    modes = json.loads((ROOT / 'config/skill-catalog.json').read_text(encoding='utf-8'))['skills']['positioning-gtm']['modes']
    assert modes['gtm']['strategy_stage_prerequisites'] == STAGES + ['operator_playbook']
    assert modes['positioning']['strategy_stage_prerequisites'] == STAGES + ['operator_playbook']
    assert not modes['operations'].get('strategy_stage_prerequisites')
    assert route_workflow.route_request('Derive the operating model from our selected position')['task_scope'] == 'focused'


def test_operations_mode_derives_from_the_selected_position_first():
    text = (SKILLS / 'positioning-gtm' / 'references' / 'operations.md').read_text(encoding='utf-8')
    checklist = text.split('## Stage checklist', 1)[1]
    position = checklist.index('1. ')
    delivery = checklist.index('2. ')
    routines = checklist.index('3. ')
    assert position < delivery < routines
    assert 'selected position' in checklist[position:delivery]
    assert 'routines' in checklist[routines:].lower()


# Plain-text requests near the positioning/GTM/operations boundary, frozen from the router at 3f1635c (before the
# merge). No match phrase changed, so every route ID is unchanged.
@pytest.mark.parametrize('request_text,expected_route', [
    ('Build a go-to-market strategy to get our first customers', 'gtm-strategy'),
    ('Create a launch strategy for our new app', 'gtm-strategy'),
    ('Plan our first customers and partnerships in Germany', 'gtm-strategy'),
    ('Compare strategic positions for my business and derive the operating model', 'business-positioning'),
    ('Reposition the business toward enterprise buyers', 'business-positioning'),
    ('Derive the operating model from our selected position', 'company-operations'),
    ('Design an operating cadence for our selected position', 'company-operations'),
    ('Set up a weekly leadership meeting and company KPIs', 'company-operations'),
    ('Design our delivery model for the cleaning service', 'company-operations'),
    ('Create a marketing strategy for my bakery', 'marketing-strategy'),
    ('Build a landing page for our launch', 'website-build'),
    ('Brand positioning for my coffee shop', 'clarify'),
])
def test_positioning_gtm_boundary_routes_unchanged(request_text, expected_route):
    assert route_workflow.route_request(request_text)['route_id'] == expected_route


@pytest.mark.parametrize('request_text,expected_route', [
    ('Build a go-to-market strategy for our first customers', 'gtm-strategy'),
    ('Compare strategic positions before we pick one', 'business-positioning'),
    ('Design the operating model and operating cadence', 'company-operations'),
])
def test_positioning_gtm_plain_text_infers_its_mode(request_text, expected_route):
    assert route_workflow.infer_mode('positioning-gtm', request_text)[0] == expected_route


def test_evidence_scout_interview_kit_mode_keeps_its_contract():
    refs = SKILLS / 'evidence-scout' / 'references'
    kit = (refs / 'interview-kit.md').read_text(encoding='utf-8')
    for marker in ('build_interview_kit.py', 'source-review.json', '--responders', 'ingest_transcript_coding.py',
                   'interview-tracker.md', 'interview-screener.md', 'interview-guide.md',
                   'references/interview-recruitment.md', 'references/case-insights.md', 'Never pitch the solution'):
        assert marker in kit, marker
    assert 'unpaid' in kit.lower()
    skill = (SKILLS / 'evidence-scout' / 'SKILL.md').read_text(encoding='utf-8')
    assert 'references/interview-kit.md' in skill
    routes = _routes()
    assert routes['interview-bridge']['mode'] == 'interview-kit'
    assert not routes['interview-bridge'].get('requires_pain_gate') and not routes['evidence-scout'].get('requires_pain_gate')
    assert not routes['evidence-scout'].get('mode')
    catalog = json.loads((ROOT / 'config/skill-catalog.json').read_text(encoding='utf-8'))['skills']['evidence-scout']
    kit_mode = catalog['modes']['interview-kit']
    assert [c['artifact'] for c in kit_mode['consumes']] == ['evidence-run']
    assert [c['artifact'] for c in kit_mode['produces']] == ['interview-tracker']
    assert not kit_mode.get('strategy_stage_prerequisites')


# Plain-text requests near the interview/evidence boundary. Frozen from the router at 3f1635c (before the merge);
# rows marked "new" moved from clarification to interview-bridge through the specific phrases added in the merge.
@pytest.mark.parametrize('request_text,expected_route', [
    ('Build a customer interview guide from the evidence run', 'interview-bridge'),
    ('Write an interview screener for dentists', 'interview-bridge'),
    ('Create an interview kit for the meal-kit evidence', 'interview-bridge'),  # new
    ('Set up an interview tracker for our customer calls', 'interview-bridge'),  # new
    ('Collect customer evidence for invoice automation pain', 'evidence-scout'),
    ('Validate customer pain for dog walkers', 'evidence-scout'),
    ('What will customers search for?', 'evidence-scout'),
    ('Plan customer interviews to validate the pain', 'clarify'),
    ('Recruit customer interviews for my idea', 'clarify'),
    ('Find customer problems in independent elder care', 'market-discovery'),
    ('Pressure-test this idea: software for care homes', 'idea-validation'),
    ('Research what customers say on social media about invoicing', 'clarify'),
])
def test_evidence_interview_boundary_routes(request_text, expected_route):
    assert route_workflow.route_request(request_text)['route_id'] == expected_route


@pytest.mark.parametrize('request_text,expected_route', [
    ('Build the interview kit: screener and customer interview guide', 'interview-bridge'),
    ('Collect customer evidence and validate customer pain', 'evidence-scout'),
    # No phrase matches: the skill's own route stays the plain-text default, as when it was single-mode.
    ('Research pain points of freelance translators', 'evidence-scout'),
])
def test_evidence_scout_plain_text_infers_its_mode(request_text, expected_route):
    assert route_workflow.infer_mode('evidence-scout', request_text)[0] == expected_route


def test_evidence_scout_plain_text_dispatch_still_works_without_an_envelope():
    from scripts import enforce_skill_route as hook
    event = {'hook_event_name': 'PreToolUse', 'tool_name': 'Skill', 'session_id': 's1', 'tool_use_id': 't1',
             'cwd': str(ROOT), 'tool_input': {'skill': 'evidence-scout', 'args': 'Research pain points of freelance translators'}}
    out = hook.check_dispatch(event)
    assert '"route_id": "evidence-scout"' in out['hookSpecificOutput']['additionalContext']
