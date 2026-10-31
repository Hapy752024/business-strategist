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
    'opportunity-risk-designer': ['saas-fintech-pilot-designer'],
    'brand-website-designer-builder': ['geo-audit', 'stripe-best-practices'],
}
# Hosts that absorbed a former skill keep their own pre-existing routes as they were (route ID, mode or no mode);
# only the absorbed skills' routes gain a mode and a references/<mode>.md.
ABSORBING_HOSTS = {'evidence-scout', 'opportunity-risk-designer', 'brand-website-designer-builder'}
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
    # A mode may keep its former skill's name (geo-audit); only its own merged skill may carry that mode key.
    skills = {name: {**meta, 'modes': list(meta.get('modes', {}).values())} for name, meta in catalog['skills'].items()}
    text = json.dumps({**catalog, 'skills': skills})
    for name, meta in catalog['skills'].items():
        for mode in meta.get('modes', {}):
            assert mode not in route_workflow.SKILL_ALIASES or (name, mode) in FORMER, (name, mode)
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


def test_pilot_mode_keeps_its_gates_and_contract():
    """Gate fields as frozen at 3f1635c: the pilot route stays pain-gated with five strategy stages and no
    input/output contract (so `route_workflow.py status` still skips it)."""
    routes = _routes()
    assert routes['saas-fintech-pilot-designer']['requires_pain_gate'] is True
    assert routes['saas-fintech-pilot-designer']['mode'] == 'pilot'
    modes = json.loads((ROOT / 'config/skill-catalog.json').read_text(encoding='utf-8'))['skills']['opportunity-risk-designer']['modes']
    assert modes['pilot']['strategy_stage_prerequisites'] == STAGES
    assert modes['pilot']['prerequisites'] == ['product hypothesis']
    from scripts import case_status
    catalog = json.loads((ROOT / 'config/skill-catalog.json').read_text(encoding='utf-8'))['skills']
    assert case_status._consumes(catalog, 'opportunity-risk-designer', 'pilot') is None
    for route_id in ('opportunity-prioritization', 'case-insights', 'case-appraisal', 'claim-falsification', 'smoke-test-design'):
        assert not routes[route_id].get('requires_pain_gate'), route_id


def test_pilot_regulatory_content_has_its_own_reference():
    refs = SKILLS / 'opportunity-risk-designer' / 'references'
    pilot = (refs / 'pilot.md').read_text(encoding='utf-8')
    regulatory = (refs / 'pilot-regulatory.md').read_text(encoding='utf-8')
    assert 'pilot-regulatory.md' in pilot and 'not legal advice' in pilot
    for marker in ('FCA', 'Safeguards Rule', 'NIST Privacy Framework', 'Risk Ladder', 'licensed partner'):
        assert marker in regulatory, marker
        assert marker not in pilot, marker
    for marker in ('Conversion gate', 'Pilot Agreement Outline', 'Evidence Log Template', 'Pilot Scorecard Template'):
        assert marker in pilot, marker


# Plain-text requests near the pilot/risk boundary. Frozen from the router at 3f1635c (before the merge); rows
# marked "new" moved from clarification to the pilot route through the specific phrases added in the merge.
@pytest.mark.parametrize('request_text,expected_route', [
    ('Design a paid pilot for our claims software', 'saas-fintech-pilot-designer'),
    ('Plan a fintech pilot with a bank partner', 'saas-fintech-pilot-designer'),
    ('Design an insurtech pilot for broker quoting', 'saas-fintech-pilot-designer'),  # new
    ('Design a SaaS pilot for our scheduling tool', 'saas-fintech-pilot-designer'),  # new
    ('Should we apply for a regulatory sandbox?', 'saas-fintech-pilot-designer'),  # new
    ('Design a smoke test for the meal-kit offer', 'smoke-test-design'),
    ('What should I validate next?', 'opportunity-prioritization'),
    ('Rank opportunities and set decision gates', 'opportunity-prioritization'),
    ('Falsify claims in the case insights', 'claim-falsification'),
    ('Design an MVP for our budgeting app', 'clarify'),
    ('Set up a pilot program with our first customers', 'clarify'),
    ('Build a go-to-market strategy for our fintech', 'gtm-strategy'),
])
def test_pilot_boundary_routes(request_text, expected_route):
    assert route_workflow.route_request(request_text)['route_id'] == expected_route


@pytest.mark.parametrize('request_text,expected_route', [
    ('Design a paid pilot for our insurance API', 'saas-fintech-pilot-designer'),
    ('Design a smoke test with a fake door', 'smoke-test-design'),
    ('What should I validate next?', 'opportunity-prioritization'),
])
def test_opportunity_risk_plain_text_infers_its_mode(request_text, expected_route):
    assert route_workflow.infer_mode('opportunity-risk-designer', request_text)[0] == expected_route


# Fix round 1: two workflows of one merged skill in one request must still clarify, as two different skills did at
# fd05161 (branch base, before any merge). Run in a workspace whose pain gate has not passed, so a gated route cannot
# ride along with an ungated one.
TWO_WORKFLOW_REQUESTS = [
    'What should I validate next? Then plan a fintech pilot',
    'Prioritize ideas and rank opportunities using decision gates; also plan a fintech pilot',
    'Build a go-to-market strategy, then design our operating cadence',
    'Collect voice of customer from reviews, then write a customer interview guide',
    'Design a smoke test, then plan a fintech pilot',
    'Falsify claims in the draft, then design a paid pilot',
    # One representative per earlier family.
    'Do brand discovery, then write the brand book',
    'Find competitors for my app, then analyze competitor pricing',
    'Find founder playbooks for SaaS, then analyze a company growth case',
    'Write a marketing strategy, then build a content calendar',
    'Reposition the business; also design the delivery model',
    'Validate customer pain, then build an interview screener',
    'Run a GEO audit, then build a landing page',
]


@pytest.mark.parametrize('request_text', TWO_WORKFLOW_REQUESTS)
def test_two_workflows_of_one_merged_skill_clarify(tmp_path, monkeypatch, request_text):
    import sys
    sys.path.insert(0, str(ROOT / 'tests'))
    from test_workspace_gates import _write_manifest
    monkeypatch.setattr(route_workflow, 'ROOT', tmp_path)
    _write_manifest(tmp_path, 'gated', 'not_run', monkeypatch)
    packet = route_workflow.route_request(request_text, project='gated')
    assert packet['route_id'] == 'clarify', packet['route_id']
    assert packet['reason'] == 'multiple requested workflows; resolve scope before dispatch'


def test_plain_text_default_is_only_on_the_evidence_scout_route(tmp_path):
    import shutil
    from scripts import validate_skill_routes
    assert validate_skill_routes.validate() == []
    for rel in ('config', '.agents'):
        shutil.copytree(ROOT / rel, tmp_path / rel, symlinks=True)
    shutil.copytree(ROOT / 'references', tmp_path / 'references')
    path = tmp_path / 'config/workflow-routes.json'
    data = json.loads(path.read_text(encoding='utf-8'))
    next(r for r in data['routes'] if r['id'] == 'opportunity-prioritization')['plain_text_default'] = True
    path.write_text(json.dumps(data), encoding='utf-8')
    errors = validate_skill_routes.validate(tmp_path)
    assert any('plain_text_default is allowed only on route evidence-scout' in e for e in errors), errors


@pytest.mark.parametrize('former', [former for _, former in FORMER])
def test_skill_call_with_a_former_name_is_denied_with_its_replacement(former):
    from scripts import enforce_skill_route as hook
    event = {'hook_event_name': 'PreToolUse', 'tool_name': 'Skill', 'session_id': 's1', 'tool_use_id': 't1',
             'cwd': str(ROOT), 'tool_input': {'skill': former, 'args': 'do the task'}}
    route_id = route_workflow.SKILL_ALIASES[former]
    merged = _routes()[route_id]['skill']
    with pytest.raises(ValueError, match=f'{former} was merged into {merged}; dispatch {merged} with route {route_id}'):
        hook.check_dispatch(event)


WEBSITE = 'brand-website-designer-builder'


def test_website_absorbed_modes_keep_their_gates_and_packets():
    """Gate and packet fields as frozen at 3943842: geo-audit and stripe-best-practices stay ungated, keep their own
    prerequisites, cost and references, and stay outside the website design branch (no entry_mode/subproject)."""
    routes = _routes()
    modes = json.loads((ROOT / 'config/skill-catalog.json').read_text(encoding='utf-8'))['skills'][WEBSITE]['modes']
    expected = {
        'geo-audit': ('geo-audit', ['public URL or deployed preview URL of the site'],
                      ['.agents/skills/brand-website-designer-builder/geo/VENDOR.md',
                       '.agents/skills/brand-website-designer-builder/references/aeo-geo-visibility.md']),
        'stripe-best-practices': ('stripe', ['selected target application and bounded task'], []),
    }
    for route_id, (mode, prerequisites, references) in expected.items():
        route = routes[route_id]
        assert route['skill'] == WEBSITE and route['mode'] == mode and not route.get('requires_pain_gate')
        assert not modes[mode].get('strategy_stage_prerequisites')
        packet = route_workflow.route_request('explicit specialist task', intent=route_id, check_skill=WEBSITE)
        assert packet['prerequisites'] == prerequisites and packet['estimated_cost'] == 'low'
        assert packet['side_effect'] == 'local_files' and packet['required_references'] == references
        assert 'entry_mode' not in packet and 'subproject' not in packet and not packet.get('gate_blocked')
    assert [c['artifact'] for c in modes['geo-audit']['consumes']] == ['website_build']
    for route_id in ('website-build', 'website-experiment', 'validation-page', 'seo-technical-audit'):
        assert routes[route_id]['requires_pain_gate'] is True, route_id
    assert 'mode' not in routes['website-build']


def test_website_geo_and_stripe_references_are_reachable_from_the_skill():
    skill = (SKILLS / WEBSITE / 'SKILL.md').read_text(encoding='utf-8')
    assert 'references/geo-audit.md' in skill and 'references/stripe.md' in skill
    stripe = (SKILLS / WEBSITE / 'references' / 'stripe.md').read_text(encoding='utf-8')
    for name in ('payments', 'billing', 'connect', 'treasury'):
        assert f'references/stripe-{name}.md' in stripe and (SKILLS / WEBSITE / 'references' / f'stripe-{name}.md').is_file()
    assert 'security-review' in stripe and 'test mode' in stripe


# Plain-text requests near the website/GEO/Stripe boundary. Frozen from the router at 3943842 (before the merge);
# the row marked "new" moved from clarification to the stripe mode through the single "Stripe" phrase added, and
# the row marked "changed" is the one request that moved between routes.
@pytest.mark.parametrize('request_text,expected_route', [
    ('Run a GEO audit on https://www.example.com', 'geo-audit'),
    ('Do an AEO audit of our website', 'geo-audit'),
    ('Fix my website for AEO/GEO', 'website-build'),
    ('Structured data audit', 'website-build'),
    ('Is my site visible in ChatGPT?', 'competitor-monitoring'),
    ('Run a technical SEO audit of our site', 'seo-technical-audit'),
    ('Integrate Stripe checkout into our Next.js app', 'stripe-best-practices'),  # new
    ('Add Stripe checkout to my landing page', 'website-build'),
    ('Build a landing page and integrate Stripe payments', 'website-build'),
    ('Deploy the Stripe checkout to Vercel', 'website-build'),
    # changed: was standalone-brand through its 4-character "logo" phrase; any Stripe phrase outranks it.
    ('Add the Stripe logo to the checkout page', 'stripe-best-practices'),
    ('Review the payment flow security of our checkout', 'clarify'),
    ('Create a pricing strategy for our subscription plans', 'clarify'),
    ('Run a GEO audit, then build a landing page', 'clarify'),
])
def test_website_geo_stripe_boundary_routes(request_text, expected_route):
    assert route_workflow.route_request(request_text)['route_id'] == expected_route


@pytest.mark.parametrize('request_text,expected_route', [
    ('Run a GEO audit on the preview URL', 'geo-audit'),
    ('Review our Stripe subscription code', 'stripe-best-practices'),
    ('Build a landing page for the launch', 'website-build'),
])
def test_website_plain_text_infers_its_mode(request_text, expected_route):
    assert route_workflow.infer_mode(WEBSITE, request_text)[0] == expected_route
