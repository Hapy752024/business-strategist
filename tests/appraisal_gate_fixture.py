"""Isolate legacy publisher tests from the separately tested research gate."""

from scripts.evidence_scout import validate_research_completion as completion


def install(monkeypatch):
    def reviewed_input(_root, _case_id, bindings=()):
        # These tests exercise economics, transactionality and handoffs. The
        # actual research/run validator is covered in its own focused tests.
        return {'status': 'eligible', 'missing': [], 'eligible_runs': [
            {'claim_ledger': binding['path']} for binding in bindings]}
    monkeypatch.setattr(completion, 'initial_case_evidence', reviewed_input)
