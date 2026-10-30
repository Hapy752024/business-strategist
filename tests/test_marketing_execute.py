"""Approval-bound marketing execution: no external write without a matching human approval."""
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.marketing import execute as ex  # noqa: E402
from scripts.marketing.execution import authorization_digest  # noqa: E402

SENTINEL = "sk-SENTINEL-never-in-receipts-0123456789"
NOW = datetime(2026, 10, 31, 12, 0, tzinfo=timezone.utc)


def base_action(kind="create_campaign", **overrides):
    requests = {
        "create_campaign": {"ad_account_id": "1234", "name": "Pilot test", "objective": "OUTCOME_TRAFFIC",
                            "special_ad_categories": [], "spend_cap": 10000},
        "schedule_post": {"date": "2026-11-05T10:00:00Z",
                          "posts": [{"integration": {"id": "int-1"}, "value": [{"content": "Hello", "image": []}],
                                     "settings": {"__type": "linkedin"}}]},
        "send_broadcast": {"audience_id": "aud-1", "from": "Founder <founder@example.test>",
                           "subject": "Update", "html": "<p>Hi</p>"},
        "create_experiment": {"name": "Hero copy", "feature_flag_key": "hero-copy-test",
                              "parameters": {"feature_flag_variants": [{"key": "control", "rollout_percentage": 50},
                                                                       {"key": "test", "rollout_percentage": 50}]}},
    }
    action = {"id": "act-1", "schema_version": 2, "action_kind": kind, "intended_result": "paused test campaign exists",
              "recipient": None, "destination": "provider account", "prepared_materials": [],
              "authorization_basis": "founder approved pilot test", "commitment_state": "accepted",
              "execution_status": "prepared", "provider_request": requests[kind]}
    action.update(overrides)
    return action


def approval_for(action, **overrides):
    approval = {"action_id": action["id"], "digest": authorization_digest(action), "scope": action["action_kind"],
                "granted_by": "Habib Gzara", "granted_at": (NOW - timedelta(hours=1)).isoformat(),
                "founder_email": "founder@example.test"}
    approval.update(overrides)
    return approval


class FakeHTTP:
    def __init__(self, responses=None):
        self.calls = []
        self.responses = list(responses or [])

    def __call__(self, method, url, headers, body):
        self.calls.append({"method": method, "url": url, "headers": headers, "body": body})
        return self.responses.pop(0) if self.responses else {"id": f"prov-{len(self.calls)}"}


def secrets(*names):
    return names[0], SENTINEL if not names[0].endswith(("BASE_URL", "HOST")) else "https://provider.example.test"


def run(action, approval, tmp_path, http=None, **kw):
    http = http or FakeHTTP()
    kw.setdefault("dry_run", False)
    result = ex.execute(action, approval, marketing_root=tmp_path, http=http, secret=secrets, now=NOW, **kw)
    return result, http


def receipts(tmp_path):
    return [json.loads(p.read_text()) for p in sorted((tmp_path / "receipts").glob("*.json"))]


def test_refuses_without_matching_digest(tmp_path):
    action = base_action()
    approval = approval_for(action)
    action["provider_request"]["spend_cap"] = 999999  # changed after approval
    result, http = run(action, approval, tmp_path)
    assert result["outcome"] == "refused" and any("digest" in r for r in result["reasons"])
    assert http.calls == []
    assert receipts(tmp_path)[0]["outcome"] == "refused"


def test_meta_campaign_created_paused(tmp_path):
    action = base_action()
    result, http = run(action, approval_for(action), tmp_path)
    assert result["outcome"] == "executed", result
    assert len(http.calls) == 1
    call = http.calls[0]
    assert call["method"] == "POST" and call["url"].endswith("/act_1234/campaigns")
    assert call["body"]["status"] == "PAUSED"
    assert result["provider_ids"] == {"campaign_id": "prov-1"}


def test_meta_refuses_active_status_even_if_approved(tmp_path):
    action = base_action()
    action["provider_request"]["status"] = "ACTIVE"
    result, http = run(action, approval_for(action), tmp_path)
    assert result["outcome"] == "refused" and http.calls == []


def test_meta_refuses_without_spend_limit(tmp_path):
    action = base_action()
    del action["provider_request"]["spend_cap"]
    result, http = run(action, approval_for(action), tmp_path)
    assert result["outcome"] == "refused" and any("spend" in r for r in result["reasons"])
    assert http.calls == []


def test_dry_run_is_default_and_makes_no_adapter_call(tmp_path):
    action = base_action()
    http = FakeHTTP()
    result = ex.execute(action, approval_for(action), marketing_root=tmp_path, http=http, secret=secrets, now=NOW)
    assert result["outcome"] == "dry_run"
    assert http.calls == []
    assert result["would_send"][0]["body"]["status"] == "PAUSED"


def test_dry_run_does_not_call_custom_adapter(tmp_path):
    called = []

    class Adapter:
        REQUIRES_ENV = ()
        def validate(self, request, approval): return []
        def describe(self, request, approval): return [{"method": "POST", "url": "x", "body": {}}]
        def run(self, request, approval, *, http, secret): called.append(1); return {"status": "ok", "provider_ids": {}}

    action = base_action()
    result = ex.execute(action, approval_for(action), marketing_root=tmp_path, adapters={"create_campaign": Adapter()},
                        secret=secrets, now=NOW)
    assert result["outcome"] == "dry_run" and called == []


@pytest.mark.parametrize("who", ["claude", "Claude Opus", "AGENT", "assistant", "subagent", "tool", "", "  "])
def test_agent_identity_granted_by_rejected(tmp_path, who):
    action = base_action()
    result, http = run(action, approval_for(action, granted_by=who), tmp_path)
    assert result["outcome"] == "refused" and http.calls == []


def test_expired_approval_rejected(tmp_path):
    action = base_action()
    old = (NOW - timedelta(days=8)).isoformat()
    result, http = run(action, approval_for(action, granted_at=old), tmp_path)
    assert result["outcome"] == "refused" and any("expired" in r for r in result["reasons"])
    assert http.calls == []
    result, _ = run(action, approval_for(action, granted_at=old), tmp_path, validity=timedelta(days=10))
    assert result["outcome"] == "executed"


def test_missing_or_future_granted_at_rejected(tmp_path):
    action = base_action()
    for value in (None, (NOW + timedelta(days=1)).isoformat(), "not a date"):
        result, http = run(action, approval_for(action, granted_at=value), tmp_path)
        assert result["outcome"] == "refused" and http.calls == []


def test_scope_mismatch_rejected(tmp_path):
    action = base_action()
    result, http = run(action, approval_for(action, scope="schedule_post"), tmp_path)
    assert result["outcome"] == "refused" and any("scope" in r for r in result["reasons"])
    assert http.calls == []


def test_idempotent_second_execute_refused(tmp_path):
    action = base_action()
    approval = approval_for(action)
    first, http = run(action, approval, tmp_path)
    assert first["outcome"] == "executed"
    second, http2 = run(action, approval, tmp_path)
    assert second["outcome"] == "refused" and any("already" in r for r in second["reasons"])
    assert http2.calls == []


def test_uncertain_failure_also_blocks_retry(tmp_path):
    def boom(method, url, headers, body):
        raise OSError(f"connection reset with header {headers}")
    action = base_action()
    result = ex.execute(action, approval_for(action), dry_run=False, marketing_root=tmp_path, http=boom,
                        secret=secrets, now=NOW)
    assert result["outcome"] == "uncertain"
    again, http = run(action, approval_for(action), tmp_path)
    assert again["outcome"] == "refused" and http.calls == []
    assert SENTINEL not in json.dumps(receipts(tmp_path))


def test_real_execute_requires_receipt_store():
    action = base_action()
    http = FakeHTTP()
    result = ex.execute(action, approval_for(action), dry_run=False, marketing_root=None, http=http,
                        secret=secrets, now=NOW)
    assert result["outcome"] == "refused" and http.calls == []


def test_receipts_contain_no_secrets(tmp_path):
    for kind in ("create_campaign", "schedule_post", "send_broadcast", "create_experiment"):
        action = base_action(kind, id=f"act-{kind}")
        http = FakeHTTP([{"id": "x1", "token": SENTINEL}, {"id": "x2"}])
        result, http = run(action, approval_for(action), tmp_path, http=http)
        assert result["outcome"] == "executed", result
        assert any(SENTINEL in json.dumps(c["headers"]) for c in http.calls)  # the secret was actually used
        assert SENTINEL not in json.dumps(result)
    text = "".join(p.read_text() for p in (tmp_path / "receipts").glob("*.json"))
    assert text and SENTINEL not in text


def test_resend_defaults_to_test_send_to_founder(tmp_path):
    action = base_action("send_broadcast")
    result, http = run(action, approval_for(action), tmp_path)
    assert result["outcome"] == "executed"
    assert len(http.calls) == 1
    assert http.calls[0]["url"].endswith("/emails")
    assert http.calls[0]["body"]["to"] == ["founder@example.test"]


def test_resend_requires_audience_and_founder_email(tmp_path):
    action = base_action("send_broadcast")
    del action["provider_request"]["audience_id"]
    result, http = run(action, approval_for(action), tmp_path)
    assert result["outcome"] == "refused" and http.calls == []
    action = base_action("send_broadcast", id="act-2")
    approval = approval_for(action)
    del approval["founder_email"]
    result, http = run(action, approval, tmp_path)
    assert result["outcome"] == "refused" and http.calls == []


def test_resend_full_broadcast_only_when_test_send_explicitly_false(tmp_path):
    action = base_action("send_broadcast")
    action["provider_request"]["test_send"] = False
    result, http = run(action, approval_for(action), tmp_path)
    assert result["outcome"] == "executed"
    assert [c["url"] for c in http.calls] == ["https://api.resend.com/broadcasts",
                                              "https://api.resend.com/broadcasts/prov-1/send"]
    assert http.calls[0]["body"]["send"] is False and http.calls[0]["body"]["segment_id"] == "aud-1"


def test_postiz_schedules_never_posts_now(tmp_path):
    action = base_action("schedule_post")
    result, http = run(action, approval_for(action), tmp_path)
    assert result["outcome"] == "executed"
    assert http.calls[0]["url"] == "https://provider.example.test/public/v1/posts"
    assert http.calls[0]["body"]["type"] == "schedule"
    action = base_action("schedule_post", id="act-now")
    action["provider_request"]["type"] = "now"
    result, http = run(action, approval_for(action), tmp_path)
    assert result["outcome"] == "refused" and http.calls == []


def test_posthog_experiment_is_created_as_draft(tmp_path):
    action = base_action("create_experiment")
    result, http = run(action, approval_for(action), tmp_path)
    assert result["outcome"] == "executed"
    assert "/experiments/" in http.calls[0]["url"] and "start_date" not in http.calls[0]["body"]
    action = base_action("create_experiment", id="act-launch")
    action["provider_request"]["start_date"] = "2026-11-01T00:00:00Z"
    result, http = run(action, approval_for(action), tmp_path)
    assert result["outcome"] == "refused" and http.calls == []


def test_unknown_action_kind_refused(tmp_path):
    action = base_action()
    action["action_kind"] = "send_pitch"
    result, http = run(action, approval_for(action), tmp_path)
    assert result["outcome"] == "refused" and http.calls == []


def test_digest_binds_provider_request():
    action = base_action()
    before = authorization_digest(action)
    action["provider_request"]["name"] = "Other"
    assert authorization_digest(action) != before


def _cli(args, env_extra=None, tmp_path=None):
    env = {k: v for k, v in os.environ.items() if k != "MARKETING_APPROVAL_PIN"}
    env.update(env_extra or {})
    return subprocess.run([sys.executable, str(ROOT / "scripts/marketing/execute.py"), *args], capture_output=True,
                          text=True, stdin=subprocess.DEVNULL, env=env, cwd=tmp_path)


def test_non_interactive_approve_refused_without_pin(tmp_path):
    path = tmp_path / "action.json"
    path.write_text(json.dumps(base_action()))
    out = tmp_path / "approval.json"
    proc = _cli(["approve", str(path), "--by", "Habib", "--out", str(out)], tmp_path=tmp_path)
    assert proc.returncode != 0 and not out.exists()
    proc = _cli(["approve", str(path), "--by", "Habib", "--out", str(out), "--i-am-the-founder", "--pin", "1234"],
                tmp_path=tmp_path)
    assert proc.returncode != 0 and not out.exists()  # no env PIN set
    proc = _cli(["approve", str(path), "--by", "Habib", "--out", str(out), "--i-am-the-founder", "--pin", "9999"],
                {"MARKETING_APPROVAL_PIN": "1234"}, tmp_path)
    assert proc.returncode != 0 and not out.exists()  # wrong PIN


def test_non_interactive_approve_with_matching_pin_writes_bound_approval(tmp_path):
    action = base_action()
    path = tmp_path / "action.json"
    path.write_text(json.dumps(action))
    out = tmp_path / "approval.json"
    proc = _cli(["approve", str(path), "--by", "Habib", "--out", str(out), "--i-am-the-founder", "--pin", "1234",
                 "--founder-email", "founder@example.test"], {"MARKETING_APPROVAL_PIN": "1234"}, tmp_path)
    assert proc.returncode == 0, proc.stderr
    approval = json.loads(out.read_text())
    assert approval["digest"] == authorization_digest(action) and approval["scope"] == "create_campaign"
    assert "1234" not in out.read_text()
    assert "PAUSED" in proc.stdout  # plain-language summary shown


def test_approve_refuses_agent_identity_even_with_pin(tmp_path):
    path = tmp_path / "action.json"
    path.write_text(json.dumps(base_action()))
    out = tmp_path / "approval.json"
    proc = _cli(["approve", str(path), "--by", "claude", "--out", str(out), "--i-am-the-founder", "--pin", "1234"],
                {"MARKETING_APPROVAL_PIN": "1234"}, tmp_path)
    assert proc.returncode != 0 and not out.exists()


def test_cli_run_defaults_to_dry_run(tmp_path):
    action = base_action()
    (tmp_path / "action.json").write_text(json.dumps(action))
    approval = approval_for(action, granted_at=datetime.now(timezone.utc).isoformat())
    (tmp_path / "approval.json").write_text(json.dumps(approval))
    proc = _cli(["run", str(tmp_path / "action.json"), "--approval", str(tmp_path / "approval.json"),
                 "--marketing-root", str(tmp_path / "mk")], tmp_path=tmp_path)
    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout)["outcome"] == "dry_run"
