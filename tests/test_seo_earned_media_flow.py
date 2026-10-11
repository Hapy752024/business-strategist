"""Synthetic Marketing workflow: preparation, captured placement and measured review."""
import json
from pathlib import Path

import pytest

from scripts import case_workspace, subprojects
from scripts.marketing import earned_media, execution, keyword_map, link_observations as links, observations

FIXTURE = Path(__file__).resolve().parents[1] / 'fixtures/marketing/earned-media'


def publish(root, files, status='active'):
    revision = case_workspace.read_project(root)['manifest_revision']
    subprojects.publish_marketing_workstream(root, files,
        expected_manifest_revision=revision,
        decision_id='synthetic-review-' + str(revision), reason='Synthetic reviewed workflow evidence.', status=status)


def test_preparation_placement_and_outcome_use_one_workstream(tmp_path):
    root = tmp_path / 'workshop'
    subprojects.start(root, 'marketing', 'Workshop', 'Prepare and verify one resource placement')
    row = json.loads((FIXTURE / 'opportunity.json').read_text())
    page_map = json.loads((FIXTURE / 'keyword-map.json').read_text())
    plan = earned_media.prepare(row, base=FIXTURE, material='pitch.md')
    resource = {'audience_job': 'Repair a bicycle safely', 'utility': 'Worked repair checklist',
        'source_bindings': page_map['rows'][0]['evidence_refs'], 'original_vs_compiled': 'Original worked examples; compiled safety notes',
        'limitations': 'Synthetic example, no mechanical safety certification', 'public_use_suitability': 'Public source only; no customer details',
        'destination_url': row['destination_url'], 'maintenance_trigger': 'Guidance changes',
        'maintenance_owner': 'Workshop owner', 'distribution_rationale': 'Relevant local cycling resources'}
    assert not keyword_map.validate_resource(resource, FIXTURE)
    brief = {'brief_id':'CB-001', 'platform':'blog', 'format':'guide', 'pillar':'maintenance',
        'audience_segment':'Cyclists', 'hook':'Repair checklist', 'key_message':'Worked examples',
        'proof':'Reviewed public sources', 'cta':'Request repair', 'conversion_bridge':'Service inquiry',
        'kpi':{'name':'Qualified inquiries','target':1,'window_days':30}, 'owner':'Workshop owner',
        'evidence_refs':['publisher.txt'], 'brand_voice_ref':None, 'status':'planned', 'public_resource':resource}
    publish(root, {'publisher.txt': (FIXTURE/'publisher.txt').read_bytes(),
        'pitch.md': (FIXTURE/'pitch.md').read_bytes(), 'keywords/keyword-map.json': json.dumps(page_map),
        'resource/content-brief.json': json.dumps(brief),
        'opportunities.json': json.dumps([row]), 'execution-plan.json': json.dumps(plan)}, 'complete')
    # Research/preparation scope can close without sending an optional proposal.
    assert subprojects.validate_marketing_workstream(root)['valid_for_use']
    assert plan['actions'][0]['commitment_state'] == 'proposed'
    required = {'id': 'placement', 'objective': 'Check public reference', 'actor': 'agent',
        'action_kind': 'verify_placement', 'intended_result': 'Observed anchor to resource',
        'source_url': row['source_url'], 'target_url': row['destination_url'], 'dependencies': [],
        'prepared_materials': [], 'next_step': 'Inspect public page', 'completion_criterion': 'Capture-backed matching anchor',
        'commitment_state': 'accepted', 'execution_status': 'prepared', 'required_for_scope': True}
    plan['actions'].append(required)
    with pytest.raises(ValueError, match='unverified'):
        publish(root, {'execution-plan.json': json.dumps(plan)}, 'complete')
    raw = ('<a href="' + row['destination_url'] + '" rel="nofollow">Repair guide</a>').encode()
    obs = links.observe(raw, source_url=row['source_url'], final_url=row['source_url'],
        target_url=row['destination_url'], capture_path='captures/one.html', ident='one')
    encoded = json.dumps(obs).encode()
    required.update(commitment_state='completed', execution_status='verified',
        observation={'path': 'captures/one.json', 'sha256': links.sha(encoded)})
    publish(root, {'execution-plan.json': json.dumps(plan), 'captures/one.html': raw, 'captures/one.json': encoded}, 'complete')
    assert subprojects.validate_marketing_workstream(root)['valid_for_use']
    assert execution.scope_complete(plan, subprojects.path(root, 'marketing'))
    with pytest.raises(ValueError, match='immutable'):
        publish(root, {'execution-plan.json': json.dumps(plan), 'captures/one.html': b'changed'})
    # Source-only updates must not silently certify a stale keyword/resource handoff.
    with pytest.raises(ValueError, match='digest changed'):
        publish(root, {'publisher.txt': b'changed'}, 'complete')
    baseline, followup = [], []
    for name, start, end, clicks in [('before','2026-09-01','2026-09-07',8), ('after','2026-10-01','2026-10-07',12)]:
        source = tmp_path/(name+'.csv'); source.write_text('Clicks\n'+str(clicks)+'\n')
        context = {'property': row['destination_url'], 'source': 'google_search_console',
            'period_start': start, 'period_end': end, 'timezone': 'UTC', 'metric': 'clicks',
            'unit': 'count', 'exported_at': '2026-10-11'}
        mapping = {key:key for key in context if key != 'exported_at'} | {'value':'Clicks'}
        (baseline if name == 'before' else followup).append(observations.normalize(source, mapping, context))
    review = observations.decision_record(action_id='placement', before=baseline[0], after=followup[0],
        changed_at='2026-09-15', expected_effect='Relevant visitors', applied_change='Resource reference',
        confounders=['Seasonal repair demand'], limitations=['Synthetic metrics; no ranking attribution'],
        next_decision='collect_more_data')
    assert review['comparison']['results'][0]['difference'] == 4
    assert review['causal_claim'] == 'not_established'
    publish(root, {'outcome-review.json': json.dumps(review)}, 'complete')
    assert subprojects.validate_marketing_workstream(root)['valid_for_use']
