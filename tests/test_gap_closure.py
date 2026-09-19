"""Normal command and state-sequence regressions from the independent review."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import case_workspace as c, subprojects, route_workflow as routing
from scripts.case_outputs import run_staged, asset_operation
from scripts.case_economics import calculate, input_digest
from scripts.evidence_scout import workspace as w
from scripts.evidence_scout.test_landscape_artifacts import LandscapeArtifactTests
from test_case_end_to_end import setup, appraisal, selected_plan
from test_case_economics import inputs

REPO = Path(__file__).resolve().parents[1]
BRAND = '.agents/skills/brand-workspace-manager/scripts/workspace_cli.py'
MANAGER = '.agents/skills/brand-workspace-manager/scripts/manage-brand-workspace.py'
SITE = '.agents/skills/brand-website-designer-builder/scripts/scaffold-site.mjs'


def cli(*args):
    return subprocess.run(args, cwd=REPO, capture_output=True, text=True)


def snapshot(root):
    return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*') if p.is_file() and p.name != 'project.lock'}


@pytest.mark.parametrize('first', ['branding', 'website', 'others', 'business'])
def test_independent_subprojects_start_without_upstream(first, tmp_path, monkeypatch):
    root = tmp_path / 'projects/topic'
    destination = subprojects.start(root, first, 'A topic')
    assert destination == root / subprojects.PATHS[first]
    m = c.read_project(root)
    assert m['controller_kind'] == 'umbrella' and 'cases' not in m and 'selection' not in m
    assert 'implementation' not in (root / 'README.md').read_text()
    if first != 'business':
        assert not (root / 'business-analysis').exists()
    for name in subprojects.PATHS:
        subprojects.start(root, name)
    assert c.read_project(root / 'business-analysis')['project_id'] == 'topic'
    monkeypatch.setattr(routing, 'ROOT', tmp_path)
    packet = routing.route_request('Build website', intent='website-build', project='topic')
    assert packet['output_root'] == str(root / 'digital-assets/website')
    assert not packet.get('gate_blocked')
    with pytest.raises(ValueError, match='selected'):
        routing.route_request('Build GTM', intent='gtm-strategy', project='topic')
    monkeypatch.setattr(w, 'ROOT', tmp_path)
    found = w.find_existing_workspaces()
    assert len(found) == 1 and found[0]['path'] == str(root / 'business-analysis')


@pytest.mark.parametrize('mode', ['outside', 'v2', 'umbrella', 'legacy'])
def test_normal_brand_and_website_commands_need_no_research(mode, tmp_path):
    root = tmp_path / 'topic'
    if mode == 'v2':
        c.initialize(root, 'Topic')
    elif mode == 'umbrella':
        subprojects.initialize(root, 'Topic')
    elif mode == 'legacy':
        w.create_project_workspace('Topic', str(root), layout_version=1)
    for command in [[sys.executable, BRAND, 'create', '--name', 'branding', '--base-dir', str(root)],
                    [sys.executable, MANAGER, '--name', 'branding', '--base-dir', str(root)]]:
        result = cli(*command)
        assert result.returncode == 0, result.stderr
    website = root / ('digital-assets/website' if mode == 'umbrella' else 'web-site')
    result = cli('node', SITE, str(website))
    assert result.returncode == 0, result.stderr
    result = cli(sys.executable, 'scripts/brand/init_website.py', str(website), '--website-id', 'test')
    assert result.returncode == 0, result.stderr
    assert (root / 'branding/brand-manifest.json').is_file()
    assert (website / 'scaffold-command.txt').is_file()
    if mode in {'v2', 'umbrella'}:
        assert c.read_project(root).get('selection') is None
        assert (website / 'publication.json').is_file()


@pytest.mark.parametrize('script', [BRAND, MANAGER, SITE])
def test_pending_blocks_normal_design_writers_before_any_write(script, tmp_path):
    root = setup(tmp_path)
    def crash(where):
        if where == 'pending':
            raise RuntimeError('interruption')
    with pytest.raises(RuntimeError):
        c.publish(root, {'cases/a/README.md': 'new'}, expected_revision=c.read_project(root)['manifest_revision'],
                  decision_id='pending', reason='Interrupted', fault=crash)
    before = snapshot(root)
    command = ['node', script, str(root / 'web-site')] if script == SITE else [sys.executable, script, *(['create'] if script == BRAND else []), '--name', 'branding', '--base-dir', str(root)]
    result = cli(*command)
    assert result.returncode != 0
    assert snapshot(root) == before


def test_staged_publication_conflict_preserves_outside_change(tmp_path):
    root = setup(tmp_path)
    dest = root / 'branding'
    dest.mkdir()
    (dest / 'brief.md').write_text('Original')
    def edit(stage):
        (stage / 'brief.md').write_text('Proposed')
        (dest / 'brief.md').write_text('Concurrent author')
    with pytest.raises(ValueError, match='conflict'):
        run_staged(dest, 'brand', edit)
    assert (dest / 'brief.md').read_text() == 'Concurrent author'
    assert not (dest / 'publication.json').exists()


def test_research_authority_mismatch_and_default_symlink_are_no_write(tmp_path):
    root = setup(tmp_path)
    legacy = w.create_project_workspace('Legacy', str(tmp_path / 'legacy'), layout_version=1)
    output = root / 'cases/a/market_research/solution_alternatives/runs/existing'
    output.mkdir(parents=True)
    (output / 'preserve.md').write_text('Preserve')
    before = snapshot(root)
    with pytest.raises(ValueError, match='authorities'):
        w.prepare_research_output(output, workspace_arg=str(legacy))
    assert snapshot(root) == before
    outside = tmp_path / 'outside'; outside.mkdir()
    (root / 'cases/a/market_research/market_discovery').symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match='symlink'):
        w.resolve_run_dir(topic='test', workspace_arg=str(root), case_id='a', out_dir='', legacy_output=False,
                          workspace_subdir='market_research/market_discovery/runs')
    assert list(outside.iterdir()) == []


def test_shared_normal_builder_declares_inputs_and_correction_reaches_checkpoint(tmp_path):
    root = setup(tmp_path)
    source = root / 'market_research/shared.json'; source.parent.mkdir()
    source.write_text(json.dumps(LandscapeArtifactTests().landscape([{'name':'DirectCo','url':'https://direct.example',
        'primary_lane':'competitive_market','competitive_role':'direct','verification_status':'verified',
        'social_presence':[{'status':'not_found_in_checked_sources'}]}])))
    out = root / 'cases/a/market_research/solution_alternatives/runs/derived'
    command = [sys.executable, 'scripts/evidence_scout/build_landscape_artifacts.py', '--entities-json', str(source),
               '--workspace', str(root), '--case', 'a', '--out-dir', str(out)]
    assert cli(*command).returncode != 0
    assert not out.exists()
    bindings = tmp_path / 'bindings.json'
    bindings.write_text(c.encoded([c.source_binding(root, 'market_research/shared.json', locator='entities', applicability='Case A alternatives')]))
    result = cli(*command, '--source-bindings', str(bindings))
    assert result.returncode == 0, result.stderr
    cm = c.case_manifest(root, 'a')
    assert cm['stages']['competitive_landscape']['status'] == 'passed'
    c.correct(root, [], 'Same bytes; interpretation withdrawn', 'withdraw-shared', source_path='market_research/shared.json')
    assert c.case_manifest(root, 'a')['stages']['competitive_landscape']['status'] == 'blocked'


def test_changed_input_blocks_closure_and_recursive_lineage_is_retained(tmp_path):
    root = setup(tmp_path)
    scope = c.resolve(root, 'a')
    source = scope / 'market_research/pain_points/evidence.md'
    first = scope / 'market_research/solution_alternatives/runs/one'
    w.prepare_research_output(first, input_paths=[source])
    artifact = first / 'derived.md'; artifact.write_text('Derived interpretation')
    second = scope / 'market_research/solution_alternatives/runs/two'
    w.prepare_research_output(second, input_paths=[artifact])
    final = second / 'result.md'; final.write_text('Synthesis')
    assert str(source.relative_to(root)) in [b['path'] for b in c.load(second / '.case-context.json')['source_bindings']]
    source.write_text('Changed evidence')
    with pytest.raises(ValueError, match='stale research input'):
        w.update_stage(scope, 'competitive_landscape', run_dir=second, status='passed', gate_result='pass', artifacts=[final])


def test_numeric_correction_requires_fresh_bound_prose_and_updates_root_comparison(tmp_path):
    root = setup(tmp_path)
    draft = appraisal(root)
    draft['economics_input_digest'] = input_digest(draft['economics_inputs'])
    draft['documents']['business-case.md'] = '# Business case\nContribution: {{economics.results.contribution_per_unit}}. Required monthly sales: {{economics.results.required_sales}}.'
    c.publish_assessment(root, 'a', draft, 'first', 'First model')
    current = appraisal(root)
    current['economics_inputs']['revenue_per_unit'] = 150
    current['documents']['business-case.md'] = '# Business case\nContribution is EUR 50; 80 completed sales are required per month.'
    before = snapshot(root)
    with pytest.raises(ValueError, match='placeholders'):
        c.publish_assessment(root, 'a', current, 'stale-prose', 'Changed model')
    assert snapshot(root) == before
    current['documents'] = draft['documents']
    current['economics_input_digest'] = draft['economics_input_digest']
    with pytest.raises(ValueError, match='digest'):
        c.publish_assessment(root, 'a', current, 'stale-digest', 'Changed model')
    current['economics_input_digest'] = input_digest(current['economics_inputs'])
    current['comparison']['summary'] = 'Improved arithmetic; demand still unproven.'
    c.publish_assessment(root, 'a', current, 'updated', 'Refreshed model')
    body = (root / 'cases/a/business-case.md').read_text()
    assert 'Contribution: 100.0' in body and 'Required monthly sales: 40.' in body
    assert current['comparison']['summary'] in (root / 'README.md').read_text()
    c.correct(root, ['a'], 'New uncertainty', 'reassess')
    assert 'Review required' in (root / 'README.md').read_text()
    assert c.read_project(root)['selection'] is None


def test_freeze_rejects_cross_case_and_publishes_valid_baseline(tmp_path):
    root = setup(tmp_path); selected_plan(root)
    command = [sys.executable, 'scripts/strategy_review.py', 'freeze', '--plan', str(root / 'strategy/strategy-plan.json')]
    before = snapshot(root)
    result = cli(*command, '--output', str(root / 'cases/b/baseline.json'))
    assert result.returncode != 0
    assert snapshot(root) == before
    target = root / 'strategy/baselines/first.json'
    result = cli(*command, '--output', str(target))
    assert result.returncode == 0, result.stderr
    assert target.is_file()
    assert c.read_project(root)['last_completed_operation_id'].startswith('baseline-')


def test_owner_accounting_recurring_contribution_and_scenario_limits():
    d = inputs(); d['ignored_labor'] = 10000
    with pytest.raises(ValueError, match='unsupported'):
        calculate(d)
    d.pop('ignored_labor'); d['owner_cash_in_service_cost'] = True
    with pytest.raises(ValueError, match='twice'):
        calculate(d)
    d.update(owner_cash_per_month=0, imputed_owner_labor_per_month=1000, model='recurring',
        horizon_months=1, opening_cash=10000, startup_cash_cost=0, new_customers_per_month=[2], opening_customers=0,
        monthly_retention=1, new_customer_billing='immediate', receipt_lag_months=1,
        service_payment_lag_months=0, acquisition_payment_lag_months=0)
    r = calculate(d)['results']; month = r['cash']['months'][0]
    assert month['contribution'] == 100 and month['cash_receipts'] == 0
    assert month['cash_payments'] == 1600 and month['surplus_after_imputed_labor'] == -2400
    assert r['coverage']['downside']['status'] == 'unresolved'
    d['sensitivities'] = {'monthly_retention': [.5, .8]}
    assert len(calculate(d)['results']['sensitivities']['monthly_retention']) == 2


@pytest.mark.parametrize('text', ['Contribution:\nEUR 50 per sale.\nRequired monthly sales:\n80.', 'Contribution EUR 50; required monthly sales 80.'])
@pytest.mark.parametrize('field', ['business-case.md', 'comparison'])
def test_multiline_and_root_comparison_cannot_publish_old_model_values(tmp_path, text, field):
    root = setup(tmp_path)
    draft = appraisal(root); draft['economics_inputs']['revenue_per_unit'] = 150
    if field == 'comparison':
        draft['comparison']['summary'] = text
    else:
        draft['documents'][field] = text
    before = snapshot(root)
    with pytest.raises(ValueError, match='placeholders'):
        c.publish_assessment(root, 'a', draft, 'old-model', 'Changed input')
    assert snapshot(root) == before


def test_new_layout_rejects_parallel_legacy_design_paths(tmp_path):
    root = tmp_path / 'topic'
    business = subprojects.start(root, 'business')
    for command in [[sys.executable, 'scripts/brand/init_website.py', str(root / 'web-site'), '--website-id', 'test'],
                    [sys.executable, BRAND, 'create', '--name', 'branding', '--base-dir', str(business)]]:
        before = snapshot(root)
        result = cli(*command)
        assert result.returncode != 0
        assert snapshot(root) == before


def test_external_context_still_respects_handoff_destination_pending(tmp_path):
    root = tmp_path / 'topic'; subprojects.initialize(root, 'Topic')
    context = tmp_path / 'context.json'; context.write_text('{}')
    c.atomic(root / c.PENDING, '{}')
    before = snapshot(root)
    result = cli(sys.executable, 'scripts/brand/build_business_to_brand_handoff.py', str(context), str(root / 'branding/handoff.json'))
    assert result.returncode != 0
    assert snapshot(root) == before


def test_nested_business_to_brand_handoff_is_optional_and_bound(tmp_path):
    root = tmp_path / 'topic'; business = subprojects.start(root, 'business')
    for cid in ['a', 'b']:
        scope = c.add_case(business, cid, cid)
        for section in ['customer_segments', 'customer_journey', 'pain_points']:
            p = scope / 'market_research' / section / 'evidence.md'
            p.parent.mkdir(parents=True, exist_ok=True); p.write_text('Synthetic conditional evidence')
    selected_plan(business)
    plan = business / 'strategy/strategy-plan.json'
    handoff = root / 'branding/handoff.json'
    command = [sys.executable, 'scripts/brand/build_business_to_brand_handoff.py', str(plan), str(handoff), '--strategy-plan', str(plan)]
    result = cli(*command)
    assert result.returncode == 0, result.stderr
    result = cli(sys.executable, BRAND, 'create', '--base-dir', str(root), '--name', 'branding',
                 '--entry-mode', 'business_linked', '--business-to-brand', str(handoff))
    assert result.returncode == 0, result.stderr
    assert c.load(root / 'branding/brand-manifest.json')['entry_mode'] == 'business_linked'
    from scripts.brand.validate_business_to_brand_handoff import validate
    assert validate(handoff, check_sources=True) == []
    c.correct(business, ['a'], 'Changed interpretation', 'correction')
    assert validate(handoff)
    before = snapshot(root)
    result = cli(sys.executable, BRAND, 'archive-stage', str(root / 'branding'), '--stage', 'logo')
    assert result.returncode != 0
    assert snapshot(root) == before


@pytest.mark.parametrize('replace_number', range(1, 6))
def test_recovery_at_each_replacement_and_interrupted_rollback(tmp_path, monkeypatch, replace_number):
    root = setup(tmp_path)
    paths = ['cases/a/README.md', 'cases/b/README.md']
    before = {p:(root / p).read_bytes() for p in paths}
    revision = c.read_project(root)['manifest_revision']
    calls = 0
    def fail(where):
        nonlocal calls
        if where == 'replace':
            calls += 1
            if calls == replace_number:
                raise RuntimeError('replacement interruption')
    with pytest.raises(RuntimeError):
        c.publish(root, {paths[0]:None, paths[1]:'Changed'}, expected_revision=revision,
                  decision_id='interrupted', reason='Archive and update', fault=fail)
    original = c.atomic
    interrupted = False
    def restoration(path, data):
        nonlocal interrupted
        original(path, data)
        if Path(path) == root / c.PROJECT and not interrupted:
            interrupted = True
            raise RuntimeError('rollback interruption')
    monkeypatch.setattr(c, 'atomic', restoration)
    with pytest.raises(RuntimeError, match='rollback'):
        c.recover(root)
    monkeypatch.setattr(c, 'atomic', original)
    assert c.recover(root) == 'rolled_back'
    assert c.read_project(root)['manifest_revision'] == revision
    assert {p:(root / p).read_bytes() for p in paths} == before


@pytest.mark.parametrize('script,arguments', [
    ('brand-asset-producer/scripts/export-brand-assets.py', ['{source}', '{brand}/export']),
    ('brand-asset-producer/scripts/export-logo-package.py', ['{source}', '{brand}/export']),
    ('brand-exporter/scripts/create-brand-agent-skill.py', ['--brand-name','Example','--workspace','{brand}']),
    ('brand-ui-component-producer/scripts/apply-brand-tokens.py', ['--component','{brand}/component.tsx','--tokens','{source}/tokens','--motion-css','{source}/motion.css','--motion-ts','{source}/motion.ts']),
    ('brand-motion-designer/scripts/promote-motion-iteration.py', ['--project','{brand}','--phase','pillar','--name','responsive']),
    ('brand-motion-designer/scripts/generate-demo.py', ['pillar','--pillar','responsive','--tokens','{source}/tokens','--output-dir','{brand}/demo']),
    ('brand-ui-component-producer/scripts/scaffold-component.py', ['--name','Button','--tier','core','--base','button','--output-dir','{brand}/components']),
    ('brand-asset-producer/scripts/generate-openrouter-images.py', ['--prompt','Synthetic','--out-dir','{brand}/images']),
    ('brand-designer/scripts/promote-approved-assets.py', ['{brand}']),
])
def test_specialized_design_writers_stop_before_work_when_pending(tmp_path, script, arguments):
    root = tmp_path / 'topic'; subprojects.initialize(root, 'Topic')
    source = tmp_path / 'inputs'; source.mkdir()
    c.atomic(root / c.PENDING, '{}')
    before = snapshot(root)
    args = [a.format(source=source, brand=root / 'branding') for a in arguments]
    result = cli(sys.executable, '.agents/skills/' + script, *args)
    assert result.returncode != 0 and 'pending publication' in result.stderr, result.stderr
    assert snapshot(root) == before


def test_staged_asset_records_reference_final_existing_files(tmp_path):
    from argparse import Namespace
    root = tmp_path / 'topic'; subprojects.start(root, 'others')
    output = root / 'digital-assets/others/images'
    record = root / 'digital-assets/others/assets.json'
    def synthetic_download(args):
        args.output_dir.mkdir(parents=True)
        asset = args.output_dir / 'image.png'; asset.write_bytes(b'synthetic fixture')
        data = {'assets':[{'path':str(asset)}]}
        args.record.write_text(json.dumps(data))
        return data
    result = asset_operation(Namespace(output_dir=output, record=record), synthetic_download)
    recorded = c.load(record)['assets'][0]['path']
    assert recorded == str(output / 'image.png') and Path(recorded).exists()
    assert result['assets'][0]['path'] == recorded


def test_cross_project_handoff_does_not_publish_invalid_snapshot(tmp_path):
    from scripts.brand.build_business_to_brand_handoff import build_snapshot
    source = setup(tmp_path / 'source'); selected_plan(source)
    destination = setup(tmp_path / 'destination'); selected_plan(destination)
    handoff = tmp_path / 'external-handoff.json'
    handoff.write_text(c.encoded(build_snapshot(source / 'strategy/strategy-plan.json', source / 'strategy/strategy-plan.json')))
    before = snapshot(destination)
    result = cli(sys.executable, BRAND, 'create', '--base-dir', str(destination), '--name', 'branding',
                 '--entry-mode', 'business_linked', '--business-to-brand', str(handoff))
    assert result.returncode != 0 and 'authority conflicts' in result.stderr
    assert snapshot(destination) == before


@pytest.mark.parametrize('name', ['/tmp/external', '../external', 'safe/../../external', 'a/b/c'])
def test_motion_selector_cannot_escape_workspace(tmp_path, name):
    root = tmp_path / 'topic'; subprojects.start(root, 'branding')
    before = snapshot(root)
    result = cli(sys.executable, '.agents/skills/brand-motion-designer/scripts/promote-motion-iteration.py',
        '--project', str(root / 'branding'), '--phase', 'pillar', '--name', name, '--dry-run')
    assert result.returncode == 2 and 'safe pillar' in result.stderr
    assert snapshot(root) == before


def test_existing_business_linked_writer_cannot_fall_back_to_standalone(tmp_path):
    root = setup(tmp_path)
    selected_plan(root)
    website = root / 'web-site'
    result = cli(sys.executable, 'scripts/brand/init_website.py', str(website), '--website-id', 'site', '--entry-mode', 'business_linked')
    assert result.returncode == 0, result.stderr
    c.correct(root, ['a'], 'Changed business assumptions', 'business-change')
    before = snapshot(root)
    with pytest.raises(ValueError, match='review required'):
        run_staged(website, 'website', lambda stage: (stage / 'current.txt').write_text('Replacement') and None)
    assert snapshot(root) == before


def test_nested_research_resume_uses_latest_manifest_without_duplicate_entry(tmp_path, monkeypatch):
    monkeypatch.setattr(w, 'ROOT', tmp_path)
    root = tmp_path / 'projects/topic'
    business = subprojects.start(root, 'business', 'Topic')
    run, scope = w.resolve_run_dir(topic='Topic', workspace_arg=str(root), out_dir='', legacy_output=False,
        workspace_subdir='market_research/market_discovery/runs')
    assert scope == business
    artifact = run / 'report.md'; artifact.write_text('Synthetic discovery findings')
    w.update_stage(scope, 'market_discovery', status='passed', gate_result='pass', artifacts=[artifact],
                   run_dir=run, next_action='Choose a candidate for investigation')
    found = w.find_existing_workspaces()
    assert len(found) == 1 and found[0]['slug'] == 'topic'
    assert found[0]['path'] == str(business)
    assert found[0]['next_action'] == 'Choose a candidate for investigation'


@pytest.mark.parametrize('registered', ['business', 'business-analysis'])
def test_business_analysis_name_respects_registered_layout(registered, tmp_path, monkeypatch):
    root = tmp_path / 'projects/topic'
    subprojects.initialize(root, 'Topic')
    manifest = c.read_project(root)
    manifest['subprojects']['business']['path'] = registered
    c.publish(root, {}, expected_revision=manifest['manifest_revision'], project=manifest,
              decision_id='fixture-layout', reason='Existing registered layout fixture')
    result = cli(sys.executable, 'scripts/subprojects.py', '--workspace', str(root),
                 '--start', 'business-analysis')
    assert result.returncode == 0, result.stderr
    business = root / registered
    assert Path(result.stdout.strip()) == business
    assert subprojects.business(root) == business
    other = 'business' if registered == 'business-analysis' else 'business-analysis'
    assert not (root / other).exists()
    result = cli(sys.executable, 'scripts/case_workspace.py', 'add', '--workspace', str(root),
                 '--case', 'english', '--title', 'English-speaking customers')
    assert result.returncode == 0, result.stderr
    assert (business / 'cases/english/README.md').is_file()
    assert registered + '/history/evolution.md' in (root / 'README.md').read_text()
    from jsonschema import Draft202012Validator
    schema = json.loads((REPO / 'schemas/project-manifest.schema.json').read_text())
    assert not list(Draft202012Validator(schema).iter_errors(c.read_project(root)))
    monkeypatch.setattr(w, 'ROOT', tmp_path)
    found = w.find_existing_workspaces()
    assert any(item.get('case_id') == 'english' and item['path'] == str(business / 'cases/english') for item in found)
    before = snapshot(root)
    for forbidden in ['business/README.md', 'business-analysis/README.md']:
        with pytest.raises(ValueError, match='business outputs'):
            c.publish(root, {forbidden: 'Invalid ownership'}, expected_revision=c.read_project(root)['manifest_revision'],
                      decision_id='forbidden-write', reason='Cannot write analysis through umbrella')
        assert snapshot(root) == before
