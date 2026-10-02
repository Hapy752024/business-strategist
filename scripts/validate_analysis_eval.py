#!/usr/bin/env python3
"""Validate the VOC evaluation scaffold or summarize imported blinded ratings.

Offline only: this command never invokes a model or retrieval provider.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'evals/voc/analysis-eval-manifest.json'

def validate(manifest: dict, manifest_dir: Path | None = None) -> list[str]:
    errors = []
    tasks = manifest.get('tasks', [])
    ids = [t.get('id') for t in tasks]
    if len(ids) != len(set(ids)): errors.append('duplicate task id')
    groups: dict[str, set[str]] = {}
    for task in tasks:
        groups.setdefault(task.get('group', ''), set()).add(task.get('split', ''))
        packet = task.get('packet')
        packet_kind = 'synthetic'
        if packet:
            base = Path(manifest_dir) if manifest_dir else MANIFEST.parent
            packet_path = (base / packet).resolve()
            if not packet_path.is_relative_to(base.resolve()) or not packet_path.is_file():
                errors.append(f"{task.get('id')}: packet missing: {packet}")
            else:
                try:
                    fixture = json.loads(packet_path.read_text(encoding='utf-8'))
                    packet_kind = fixture.get('packet_kind', task.get('packet_kind', 'synthetic'))
                    if fixture.get('task_id') != task.get('id'):
                        errors.append(f"{task.get('id')}: packet identity/synthetic marker invalid")
                    if packet_kind not in {'synthetic', 'reviewed_source'}:
                        errors.append(f"{task.get('id')}: unsupported packet_kind")
                    if packet_kind == 'synthetic' and fixture.get('synthetic_only') is not True:
                        errors.append(f"{task.get('id')}: synthetic packets require synthetic_only=true")
                    if packet_kind == 'reviewed_source' and not (fixture.get('source_locators') and fixture.get('source_sha256')):
                        errors.append(f"{task.get('id')}: reviewed_source packets require locators and source digest")
                    if not isinstance(fixture.get('generation_input'), dict) or not fixture['generation_input']:
                        errors.append(f"{task.get('id')}: generation input missing")
                except (OSError, json.JSONDecodeError):
                    errors.append(f"{task.get('id')}: packet is not valid JSON")
        for field in ('review_key', 'paired_examples'):
            relative = task.get(field)
            if relative:
                base = Path(manifest_dir) if manifest_dir else MANIFEST.parent
                artifact = (base / relative).resolve()
                if not artifact.is_relative_to(base.resolve()) or not artifact.is_file():
                    errors.append(f"{task.get('id')}: {field} missing or escapes manifest directory")
                else:
                    try:
                        payload = json.loads(artifact.read_text(encoding='utf-8'))
                        if payload.get('synthetic_only') is not True or payload.get('task_id') != task.get('id'):
                            errors.append(f"{task.get('id')}: {field} identity/synthetic marker invalid")
                    except (OSError, json.JSONDecodeError):
                        errors.append(f"{task.get('id')}: {field} is not valid JSON")
            elif packet and packet_kind == 'synthetic':
                errors.append(f"{task.get('id')}: {field} reference missing")
    if any(len(splits) > 1 for splits in groups.values()): errors.append('connected group crosses splits')
    expected = manifest.get('split_counts', {'development': 8, 'held_out': 4})
    for split, count in expected.items():
        if sum(t.get('split') == split for t in tasks) != count: errors.append(f'expected {count} {split} task slots')
    status = manifest.get('status')
    if status not in {'design_only_packets_and_scores_pending', 'comparison_ready'}:
        errors.append('unexpected evaluation status')
    if status == 'comparison_ready' and not all((manifest.get('packets_reviewed') is True,
            manifest.get('criteria_frozen') is True, manifest.get('reviewer_calibration') == 'complete',
            bool(manifest.get('adoption_rule')))):
        errors.append('comparison_ready requires reviewed packets, frozen criteria, calibrated reviewers and an adoption rule')
    if not manifest.get('critical_failures') or not manifest.get('dimensions'): errors.append('rubric missing')
    return errors

def summarize(scores: dict, manifest: dict, *, allow_subset: bool = False) -> dict:
    dims = manifest['dimensions']
    rows = scores.get('ratings', [])
    by_task: dict[str, dict[str, dict]] = {}
    errors = []
    known_tasks = {str(task.get('id')) for task in manifest.get('tasks', [])}
    for row in rows:
        task, variant = row.get('task_id'), row.get('variant')
        if task not in known_tasks:
            errors.append(f'{task}: unknown evaluation task')
            continue
        if variant not in {'A', 'B'}: errors.append(f'{task}: variant must be blinded A or B'); continue
        if type(row.get('critical_failure')) is not bool: errors.append(f'{task}/{variant}: critical_failure must be a boolean')
        ratings = row.get('ratings', {})
        if set(ratings) != set(dims) or any(type(ratings[d]) is not int or ratings[d] not in range(1,5) for d in dims):
            errors.append(f'{task}/{variant}: ratings must cover all dimensions with integers 1-4')
        if not row.get('rationale'): errors.append(f'{task}/{variant}: rationale required')
        if variant in by_task.setdefault(task, {}): errors.append(f'{task}: duplicate variant {variant}')
        by_task[task][variant] = row
    manifest_dir = Path(scores.get('_manifest_dir', MANIFEST.parent)).resolve()
    manifest_errors = validate(manifest, manifest_dir)
    if errors or manifest_errors: return {'valid': False, 'errors': errors + manifest_errors}
    outcomes = {'A_wins': 0, 'B_wins': 0, 'ties': 0, 'critical_failures': 0}
    dimension_outcomes = {dimension: {'A_better': 0, 'B_better': 0, 'ties': 0} for dimension in dims}
    for task, pair in by_task.items():
        if set(pair) != {'A','B'}: errors.append(f'{task}: requires both blinded variants'); continue
        a, b = pair['A'], pair['B']
        outcomes['critical_failures'] += int(a['critical_failure']) + int(b['critical_failure'])
        for dimension in dims:
            av, bv = a['ratings'][dimension], b['ratings'][dimension]
            dimension_outcomes[dimension]['A_better' if av > bv else 'B_better' if bv > av else 'ties'] += 1
        # Keep a descriptive task comparison only. Adding unlike dimensions can
        # conceal source-fidelity or uncertainty regressions.
        if all(a['ratings'][d] >= b['ratings'][d] for d in dims) and any(a['ratings'][d] > b['ratings'][d] for d in dims):
            outcomes['A_wins'] += 1
        elif all(b['ratings'][d] >= a['ratings'][d] for d in dims) and any(b['ratings'][d] > a['ratings'][d] for d in dims):
            outcomes['B_wins'] += 1
        else:
            outcomes['ties'] += 1

    required_tasks = known_tasks if not allow_subset else set(by_task)
    missing_tasks = sorted(required_tasks - set(by_task))
    if missing_tasks:
        errors.append('missing required task pairs: ' + ', '.join(missing_tasks))
    complete = not errors and set(by_task) == known_tasks
    # This manifest intentionally has no reviewed packets, frozen decision
    # threshold, or calibrated reviewers. Rating syntax can be summarized, but
    # no quality/adoption pass can be inferred from it.
    output_manifest_path = scores.get('paired_output_manifest_path')
    review_record_path = scores.get('review_record_path')
    output_manifest_digest = scores.get('paired_output_manifest_sha256')
    review_record_digest = scores.get('review_record_sha256')
    bound_artifacts_valid = False
    if output_manifest_path and review_record_path and output_manifest_digest and review_record_digest:
        try:
            output_path = (manifest_dir / output_manifest_path).resolve()
            review_path = (manifest_dir / review_record_path).resolve()
            if not output_path.is_relative_to(manifest_dir) or not review_path.is_relative_to(manifest_dir):
                raise ValueError('evaluation artifacts must remain inside the manifest directory')
            def digest(path: Path) -> str:
                return hashlib.sha256(path.read_bytes()).hexdigest()
            outputs = json.loads(output_path.read_text())
            review = json.loads(review_path.read_text())
            output_rows = outputs.get('tasks', []) if outputs.get('schema_version') == 1 else []
            output_tasks = {item.get('task_id'): item for item in output_rows}
            expected_ids = {str(task.get('id')) for task in manifest.get('tasks', [])}
            task_specs = {str(task.get('id')): task for task in manifest.get('tasks', [])}
            paths_valid = len(output_tasks) == len(output_rows)
            for task_id in expected_ids:
                task_outputs = output_tasks.get(task_id, {}).get('variants', {})
                for variant in ('A', 'B'):
                    row = task_outputs.get(variant, {})
                    artifact = (manifest_dir / row.get('path', '')).resolve()
                    trace = (manifest_dir / row.get('tool_trace_path', '')).resolve()
                    packet_path = (manifest_dir / task_specs[task_id].get('packet', '')).resolve()
                    paths_valid = paths_valid and artifact.is_relative_to(manifest_dir) and artifact.is_file() and digest(artifact) == row.get('sha256')
                    paths_valid = paths_valid and trace.is_relative_to(manifest_dir) and trace.is_file() and digest(trace) == row.get('tool_trace_sha256')
                    paths_valid = paths_valid and packet_path.is_file() and row.get('source_sha256') == digest(packet_path)
                    paths_valid = paths_valid and bool(row.get('model_id')) and bool(row.get('prompt_sha256'))
                    paths_valid = paths_valid and type(row.get('latency_ms')) is int and row['latency_ms'] >= 0
                    paths_valid = paths_valid and isinstance(row.get('usage'), dict)
            ratings_digest = hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()
            bound_artifacts_valid = (digest(output_path) == output_manifest_digest and digest(review_path) == review_record_digest
                and set(output_tasks) == expected_ids and paths_valid and review.get('blind') is True
                and isinstance(review.get('reviewer_ids'), list) and bool(review['reviewer_ids'])
                and review.get('criteria_version') == manifest.get('criteria_version')
                and review.get('ratings_sha256') == ratings_digest)
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            bound_artifacts_valid = False
    decision_ready = (complete and manifest.get('status') == 'comparison_ready'
                      and manifest.get('packets_reviewed') is True
                      and manifest.get('criteria_frozen') is True
                      and manifest.get('reviewer_calibration') == 'complete'
                      and bound_artifacts_valid)
    critical = outcomes['critical_failures'] > 0
    result = {'valid': not errors, 'errors': errors, 'comparison_complete': complete,
              'evaluation_ready_for_decision': decision_ready,
              'task_outcomes': outcomes, 'dimension_outcomes': dimension_outcomes,
              'critical_failures': critical,
              'limitation': 'Ratings and review identities are supplied inputs; this summarizer does not independently verify human judgment.'}
    if decision_ready:
        result['decision'] = 'critical_failure' if critical else 'review_required'
        result['overall_quality_pass'] = False
        result['decision_note'] = 'A human review must apply the frozen adoption rule to paired outputs and dimension-level results.'
    return result

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest', type=Path, default=MANIFEST, help='Evaluation manifest (VOC by default)')
    p.add_argument('--scores', type=Path, help='Optional blinded ratings JSON to summarize')
    p.add_argument('--allow-subset', action='store_true', help='Summarize an explicit exploratory subset; never qualifies it as complete.')
    a = p.parse_args()
    manifest = json.loads(a.manifest.read_text())
    if a.scores:
        scores = json.loads(a.scores.read_text())
        scores['_manifest_dir'] = str(a.manifest.resolve().parent)
        result = summarize(scores, manifest, allow_subset=a.allow_subset)
    else:
        errors = validate(manifest, a.manifest.resolve().parent)
        result = {'valid': not errors, 'errors': errors, 'status': manifest['status'], 'task_slots': len(manifest['tasks'])}
    print(json.dumps(result, indent=2))
    return int(not result['valid'])

if __name__ == '__main__':
    raise SystemExit(main())
