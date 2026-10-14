"""Behavioral contract tests for the repository-local evaluation operations."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('local_evaluation', Path(__file__).with_name('local_evaluation.py'))
ev = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ev)


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'evals').mkdir()
        (self.root / 'AGENTS.md').write_text('Fixture instructions, not production configuration.')
        (self.root / 'evals/rubric.json').write_text(json.dumps({'criteria': [{'id': 'truth', 'description': 'Do not invent demand'}]}))
        self.case = {'id': 'source-gap', 'task': 'Investigate this synthetic source gap.',
                     'instructions': ['AGENTS.md'], 'inputs': [], 'rubric': 'evals/rubric.json', 'split': 'development'}
        self.manifest = {'schema_version': 1, 'cases': [self.case]}
        self.save_manifest()
        self.config = {'project': 'test-agent', 'checks': [['python3', '-c', 'print("fixture only")']],
                       'full_checks': [['python3', '-c', 'raise SystemExit(1)']]}

    def save_manifest(self):
        (self.root / 'evals/local-evaluation.json').write_text(json.dumps(self.manifest))

    def prepare(self):
        return ev.prepare(self.root, self.config, 'source-gap', 'candidate-session', 'current', 'development')

    def native_result(self):
        run, row, work = self.prepare()
        (run / 'answer.txt').write_text('Demand is unverified.')
        row.update(execution_kind='native-claude', observed_model='observed-model', execution={'status': 'completed'})
        ev.seal(run, row)
        ratings = {'reviewer': 'human-reviewer', 'reviewer_session': 'fresh-session',
                   'independence': 'separate reviewer; host isolation not attested',
                   'calibration': 'human rubric reviewed', 'output_sha256': ev.sha(run / 'answer.txt'),
                   'ratings': [{'criterion': 'truth', 'verdict': 'PASS', 'evidence': 'unverified', 'rationale': 'No invented demand.'}]}
        path = self.root / 'ratings.json'; path.write_text(json.dumps(ratings))
        return run, ratings, path

    def test_check_is_fixture_only_and_unknown_cost(self):
        run, row = ev.check(self.root, self.config, 10)
        self.assertEqual(row['verdict'], 'PASS')
        self.assertEqual(row['evidence_kind'], 'deterministic')
        self.assertIsNone(row['observed_model'])
        self.assertIsNone(row['cost_usd'])
        self.assertEqual(ev.verify(run), row)

    def test_failed_check_remains_failure(self):
        run, row = ev.check(self.root, self.config, 10, full=True)
        self.assertEqual(row['verdict'], 'FAIL')

    def test_timeout_retains_partial_output(self):
        r, out, err = ev.execute([sys.executable, '-u', '-c', 'import time; print("partial"); time.sleep(10)'], cwd=self.root, timeout=0.1)
        self.assertEqual(r['status'], 'timeout')
        self.assertIn(b'partial', out)

    def test_missing_host_classified_as_infrastructure(self):
        r, _, _ = ev.execute(['/nonexistent-eval-command'], cwd=self.root, timeout=1)
        self.assertEqual(r['status'], 'unavailable')

    def test_candidate_workspace_excludes_key(self):
        run, row, work = self.prepare()
        self.assertTrue((work / 'AGENTS.md').is_file())
        self.assertFalse((work / 'evals/rubric.json').exists())
        self.assertFalse((work / 'review-template.json').exists())
        self.assertEqual(row['verdict'], 'UNVERIFIED')

    def test_held_out_requires_explicit_split(self):
        self.case['split'] = 'held_out'; self.save_manifest()
        with self.assertRaises(ValueError): self.prepare()

    def test_path_escape_rejected(self):
        self.case['inputs'] = ['../private.json']; self.save_manifest()
        with self.assertRaises(ValueError): self.prepare()

    def test_symlink_input_rejected(self):
        (self.root / 'linked.md').symlink_to(self.root / 'AGENTS.md')
        self.case['inputs'] = ['linked.md']; self.save_manifest()
        with self.assertRaises(ValueError): self.prepare()

    def test_grading_key_input_rejected(self):
        self.case['inputs'] = [self.case['rubric']]; self.save_manifest()
        with self.assertRaises(ValueError): self.prepare()

    def test_result_tampering_rejected(self):
        run, row, work = self.prepare(); ev.seal(run, row)
        (work / 'AGENTS.md').write_text('changed')
        with self.assertRaises(ValueError): ev.verify(run)

    def test_live_requires_explicit_budget_before_artifacts(self):
        args = argparse.Namespace(live=True, model='selected', runtime_root=self.root, auth_file=self.root / 'auth', budget_usd=None)
        with self.assertRaises(ValueError): ev.trial(self.root, self.config, args)
        self.assertFalse((self.root / 'evals/local-runs').exists())

    def test_synthetic_cannot_be_reviewed_as_live(self):
        run, row, work = self.prepare(); row.update(evidence_kind='deterministic', execution_kind='synthetic'); ev.seal(run, row)
        with self.assertRaises(ValueError): ev.review(run, self.root / 'ratings.json')

    def test_self_review_rejected(self):
        run, ratings, path = self.native_result(); ratings['reviewer'] = 'candidate-session'; path.write_text(json.dumps(ratings))
        with self.assertRaises(ValueError): ev.review(run, path)

    def test_unbound_review_rejected(self):
        run, ratings, path = self.native_result(); ratings['output_sha256'] = 'wrong'; path.write_text(json.dumps(ratings))
        with self.assertRaises(ValueError): ev.review(run, path)

    def test_keyword_only_grade_rejected(self):
        run, ratings, path = self.native_result(); ratings['ratings'][0]['evidence'] = 'not in output'; path.write_text(json.dumps(ratings))
        with self.assertRaises(ValueError): ev.review(run, path)

    def test_all_criteria_required(self):
        run, ratings, path = self.native_result(); ratings['ratings'] = []; path.write_text(json.dumps(ratings))
        with self.assertRaises(ValueError): ev.review(run, path)

    def test_append_only_review_preserves_baseline(self):
        run, ratings, path = self.native_result(); before = ev.sha(run / 'result.json')
        first = ev.review(run, path); second = ev.review(run, path)
        self.assertNotEqual(first, second)
        self.assertEqual(ev.sha(run / 'result.json'), before)
        self.assertEqual(ev.report(self.root)['runs'][0]['quality_reviews'], ['PASS', 'PASS'])

    def test_unknown_criterion_blocks_quality_pass(self):
        run, ratings, path = self.native_result(); ratings['ratings'][0]['verdict'] = 'UNVERIFIED'; path.write_text(json.dumps(ratings))
        self.assertEqual(ev.read(ev.review(run, path))['quality_verdict'], 'UNVERIFIED')

    def test_failed_grade_is_retained(self):
        run, ratings, path = self.native_result(); ratings['ratings'][0]['verdict'] = 'FAIL'; path.write_text(json.dumps(ratings))
        self.assertEqual(ev.read(ev.review(run, path))['quality_verdict'], 'FAIL')

    def test_export_is_allowlisted_and_idempotent(self):
        run, row, work = self.prepare(); ev.seal(run, row)
        out = self.root / 'outbox'; target = ev.export(run, out)
        self.assertEqual(ev.export(run, out), target)
        summary = ev.read(target)
        self.assertNotIn('ratings', summary)
        self.assertNotIn('bindings', summary)
        self.assertNotIn('usage', summary)
        self.assertEqual(ev.verify(run)['telemetry']['status'], 'not-requested')

    def test_conflicting_export_cannot_overwrite(self):
        run, row, work = self.prepare(); ev.seal(run, row)
        out = self.root / 'outbox'; target = ev.export(run, out); target.write_text('{}')
        with self.assertRaises(ValueError): ev.export(run, out)

    def test_export_failure_does_not_change_quality(self):
        run, row, work = self.prepare(); ev.seal(run, row); before = ev.sha(run / 'result.json')
        out = self.root / 'not-directory'; out.write_text('file')
        with self.assertRaises(OSError): ev.export(run, out)
        self.assertEqual(ev.sha(run / 'result.json'), before)

    def test_requested_model_is_not_observed(self):
        _, observed, _, cost = ev.parse_response('{"type":"result","result":"text","total_cost_usd":null}')
        self.assertIsNone(observed); self.assertIsNone(cost)

    def test_sandbox_has_no_home_or_repository_mount(self):
        run, row, work = self.prepare()
        if not ev.shutil.which('bwrap'):
            with self.assertRaises(ValueError): ev.sandbox(work, ['/usr/bin/true'])
            return
        args = ev.sandbox(work, ['/usr/bin/true'])
        self.assertIn('--unshare-all', args)
        self.assertNotIn('--share-net', args)
        self.assertNotIn(str(self.root), args)
        self.assertNotIn('--ro-bind / /', ' '.join(args))

    def test_blind_pair_excludes_arm_identity(self):
        a, _, _ = self.native_result()
        # A test-only independent root supplies the baseline; real runs are immutable.
        row = ev.read(a / 'result.json'); row['arm'] = 'baseline'
        (a / 'result.json').write_text(json.dumps(row))
        b, _, _ = self.native_result()
        packet = ev.review_packet(a, b, self.root / 'packet')
        self.assertEqual((packet / 'A.txt').read_text(), 'Demand is unverified.')
        self.assertEqual((packet / 'B.txt').read_text(), 'Demand is unverified.')
        self.assertFalse((packet / 'mapping.json').exists())
        self.assertTrue((packet.parent / 'coordinator/mapping.json').is_file())
        self.assertNotIn('observed-model', (packet / 'A.txt').read_text())

    def test_blind_pair_rejects_different_case(self):
        a, _, _ = self.native_result()
        row = ev.read(a / 'result.json'); row['arm'] = 'baseline'
        (a / 'result.json').write_text(json.dumps(row))
        b, _, _ = self.native_result()
        row = ev.read(b / 'result.json'); row['case_id'] = 'another-case'
        (b / 'result.json').write_text(json.dumps(row))
        with self.assertRaises(ValueError): ev.review_packet(a, b, self.root / 'packet')

    def test_live_cannot_substitute_fixture(self):
        args = argparse.Namespace(live=True, model='selected', runtime_root=self.root,
                                  auth_file=self.root / 'auth', budget_usd=1, fixture_command_json='["true"]')
        with self.assertRaises(ValueError): ev.trial(self.root, self.config, args)

    def test_duplicate_cases_rejected(self):
        self.manifest['cases'].append(self.case.copy()); self.save_manifest()
        with self.assertRaises(ValueError): self.prepare()

    def test_stdout_oauth_error_is_infrastructure(self):
        out = b'{"type":"result","is_error":true,"result":"Failed to authenticate: OAuth session expired"}'
        verdict, reason = ev.native_status({'status':'completed'}, out, b'')
        self.assertEqual(verdict, 'INFRASTRUCTURE_ERROR')
        self.assertEqual(reason, 'authentication-unavailable')

    def test_completed_native_response_needs_quality_review(self):
        self.assertEqual(ev.native_status({'status':'completed'}, b'{"type":"result","result":"answer"}', b'')[0], 'UNVERIFIED')

    def test_runtime_reclassification_preserves_original(self):
        run, row, work = self.prepare()
        (run/'stdout.txt').write_text('{"type":"result","is_error":true,"result":"OAuth expired"}')
        (run/'stderr.txt').write_text('')
        row.update(verdict='FAIL',execution_kind='native-claude',execution={'status':'failed'})
        ev.seal(run,row); before=ev.sha(run/'result.json')
        ev.reclassify(run)
        self.assertEqual(ev.sha(run/'result.json'),before)
        self.assertEqual(ev.report(self.root)['runs'][0]['verdict'],'INFRASTRUCTURE_ERROR')
        summary=ev.read(ev.export(run,self.root/'outbox'))
        self.assertEqual(summary['verdict'],'INFRASTRUCTURE_ERROR')
        self.assertEqual(summary['historical_verdict'],'FAIL')

    def test_prepare_binds_original_instructions(self):
        run, row, work = self.prepare()
        original = row['instruction_sha256']['AGENTS.md']
        (work/'AGENTS.md').write_text('edited candidate instructions')
        self.assertNotEqual(original, ev.sha(work/'AGENTS.md'))

    def test_export_reports_quality_without_reviewer_identity(self):
        run, ratings, path = self.native_result(); ev.review(run,path)
        summary=ev.read(ev.export(run,self.root/'outbox'))
        self.assertEqual(summary['quality_reviews'][0]['verdict'],'PASS')
        self.assertNotIn('human-reviewer',json.dumps(summary))
        self.assertNotIn('Demand is unverified',json.dumps(summary))


if __name__ == '__main__':
    unittest.main()
