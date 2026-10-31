"""Approval-bound marketing execution: no external write without a matching human approval."""
import json
import os
import stat
import types
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


PRINCIPAL = "habib"


def _keygen(folder: Path, name: str) -> Path:
    key = folder / name
    subprocess.run(["ssh-keygen", "-t", "ed25519", "-N", "", "-q", "-C", f"test-only-{name}", "-f", str(key)],
                   check=True, capture_output=True)
    return key


@pytest.fixture(scope="session")
def keys(tmp_path_factory):
    """Throwaway, passphrase-less, test-only keys. Real approval keys must be passphrase-protected."""
    folder = tmp_path_factory.mktemp("approval-keys")
    founder, mallory = _keygen(folder, "founder"), _keygen(folder, "mallory")
    signers = folder / "allowed_signers"
    signers.write_text(f'{PRINCIPAL} namespaces="marketing-approval" {(folder / "founder.pub").read_text()}')
    return {"founder": founder, "mallory": mallory, "signers": signers}


def sign(message: str, key: Path, folder: Path) -> str:
    path = folder / f"msg-{abs(hash(message))}.txt"
    path.write_text(message)
    subprocess.run(["ssh-keygen", "-Y", "sign", "-f", str(key), "-n", "marketing-approval", str(path)],
                   check=True, capture_output=True)
    return Path(f"{path}.sig").read_text()


@pytest.fixture
def approval_for(keys, tmp_path):
    def build(action, *, key="founder", root=None, signed=True, **overrides):
        approval = {"action_id": action["id"], "digest": authorization_digest(action), "scope": action["action_kind"],
                    "granted_by": PRINCIPAL, "granted_at": (NOW - timedelta(hours=1)).isoformat(),
                    "valid_until": (NOW - timedelta(hours=1) + timedelta(days=7)).isoformat(),
                    "marketing_root": ex.canonical_root(root or tmp_path), "founder_email": "founder@example.test"}
        approval.update(overrides)
        if signed:
            approval["signature"] = sign(ex.signed_message({k: (v or "") for k, v in approval.items()}),
                                         keys[key], tmp_path)
        return approval
    return build


class FakeHTTP:
    def __init__(self, responses=None):
        self.calls = []
        self.responses = list(responses or [])

    def __call__(self, method, url, headers, body):
        self.calls.append({"method": method, "url": url, "headers": headers, "body": body})
        return self.responses.pop(0) if self.responses else {"id": f"prov-{len(self.calls)}"}


def secrets(*names):
    return names[0], SENTINEL if not names[0].endswith(("BASE_URL", "HOST")) else "https://provider.example.test"


SIGNERS = {}


@pytest.fixture(autouse=True)
def _signers(keys, monkeypatch):
    SIGNERS["path"] = keys["signers"]
    monkeypatch.setattr(ex, "_stat", _root_owned_signers_stat())


def _root_owned_signers_stat():
    """Tests cannot chown to root: report test signers files (and their folders) as root-owned, nothing else."""
    real = os.stat

    def fake(path):
        info = real(path)
        target = Path(path)
        is_signers = target.name == "allowed_signers" or (target.is_dir() and (target / "allowed_signers").exists())
        if is_signers and info.st_uid == os.getuid():
            return types.SimpleNamespace(st_uid=0, st_mode=info.st_mode)
        return info
    return fake


def run(action, approval, tmp_path, http=None, **kw):
    http = http or FakeHTTP()
    kw.setdefault("dry_run", False)
    kw.setdefault("allowed_signers", SIGNERS["path"])
    kw.setdefault("marketing_root", tmp_path)
    result = ex.execute(action, approval, http=http, secret=secrets, now=NOW, **kw)
    return result, http


def receipts(tmp_path):
    return [json.loads(p.read_text()) for p in sorted((tmp_path / "receipts").glob("*.json"))]


def test_refuses_without_matching_digest(tmp_path, approval_for):
    action = base_action()
    approval = approval_for(action)
    action["provider_request"]["spend_cap"] = 999999  # changed after approval
    result, http = run(action, approval, tmp_path)
    assert result["outcome"] == "refused" and any("digest" in r for r in result["reasons"])
    assert http.calls == []
    assert receipts(tmp_path)[0]["outcome"] == "refused"


def test_meta_campaign_created_paused(tmp_path, approval_for):
    action = base_action()
    result, http = run(action, approval_for(action), tmp_path)
    assert result["outcome"] == "executed", result
    assert len(http.calls) == 1
    call = http.calls[0]
    assert call["method"] == "POST" and call["url"].endswith("/act_1234/campaigns")
    assert call["body"]["status"] == "PAUSED"
    assert result["provider_ids"] == {"campaign_id": "prov-1"}


def test_meta_refuses_active_status_even_if_approved(tmp_path, approval_for):
    action = base_action()
    action["provider_request"]["status"] = "ACTIVE"
    result, http = run(action, approval_for(action), tmp_path)
    assert result["outcome"] == "refused" and http.calls == []


def test_meta_refuses_without_spend_limit(tmp_path, approval_for):
    action = base_action()
    del action["provider_request"]["spend_cap"]
    result, http = run(action, approval_for(action), tmp_path)
    assert result["outcome"] == "refused" and any("spend" in r for r in result["reasons"])
    assert http.calls == []


def test_dry_run_is_default_and_makes_no_adapter_call(tmp_path, approval_for):
    action = base_action()
    http = FakeHTTP()
    result = ex.execute(action, approval_for(action), marketing_root=tmp_path, http=http, secret=secrets, now=NOW,
                        allowed_signers=SIGNERS["path"])
    assert result["outcome"] == "dry_run"
    assert http.calls == []
    assert result["would_send"][0]["body"]["status"] == "PAUSED"


def test_dry_run_does_not_call_custom_adapter(tmp_path, approval_for):
    called = []

    class Adapter:
        REQUIRES_ENV = ()
        def validate(self, request, approval, now=None): return []
        def describe(self, request, approval): return [{"method": "POST", "url": "x", "body": {}}]
        def run(self, request, approval, *, http, secret): called.append(1); return {"status": "ok", "provider_ids": {}}

    action = base_action()
    result = ex.execute(action, approval_for(action), marketing_root=tmp_path, adapters={"create_campaign": Adapter()},
                        secret=secrets, now=NOW, allowed_signers=SIGNERS["path"])
    assert result["outcome"] == "dry_run" and called == []


@pytest.mark.parametrize("who", ["claude", "Claude-Opus", "AGENT", "assistant", "subagent", "tool", "", "  "])
def test_agent_identity_granted_by_rejected(tmp_path, who, approval_for):
    action = base_action()
    result, http = run(action, approval_for(action, granted_by=who), tmp_path)
    assert result["outcome"] == "refused" and http.calls == []


def test_expired_approval_rejected(tmp_path, approval_for):
    action = base_action()
    granted = NOW - timedelta(days=8)
    expired = approval_for(action, granted_at=granted.isoformat(), valid_until=(granted + timedelta(days=7)).isoformat())
    result, http = run(action, expired, tmp_path)
    assert result["outcome"] == "refused" and any("expired" in r for r in result["reasons"])
    assert http.calls == []
    longer = approval_for(action, granted_at=granted.isoformat(), valid_until=(granted + timedelta(days=10)).isoformat())
    result, _ = run(action, longer, tmp_path)
    assert result["outcome"] == "executed"


def test_validity_window_over_14_days_or_missing_refused(tmp_path, approval_for):
    action = base_action()
    granted = NOW - timedelta(hours=1)
    for valid_until in ((granted + timedelta(days=15)).isoformat(), None, (granted - timedelta(days=1)).isoformat()):
        result, http = run(action, approval_for(action, valid_until=valid_until), tmp_path)
        assert result["outcome"] == "refused" and any("valid" in r for r in result["reasons"]) and http.calls == []


def test_valid_until_is_signed(tmp_path, approval_for):
    action = base_action()
    approval = approval_for(action)
    extended = dict(approval, valid_until=(NOW + timedelta(days=10)).isoformat())
    result, http = run(action, extended, tmp_path, dry_run=True)
    assert result["outcome"] == "refused" and any("signature is invalid" in r for r in result["reasons"])


def test_canonical_message_field_order():
    message = ex.signed_message({"digest": "d", "scope": "s", "granted_at": "g", "valid_until": "v", "action_id": "a",
                                 "granted_by": "b", "marketing_root": "/m", "founder_email": "e@x"})
    assert message == "d|s|g|v|a|b|/m|e@x"


def test_run_has_no_validity_override():
    with pytest.raises(SystemExit):
        ex.main(["run", "a.json", "--approval", "b.json", "--marketing-root", "x", "--validity-days", "99"])


def test_missing_or_future_granted_at_rejected(tmp_path, approval_for):
    action = base_action()
    for value in (None, (NOW + timedelta(days=1)).isoformat(), "not a date"):
        result, http = run(action, approval_for(action, granted_at=value), tmp_path)
        assert result["outcome"] == "refused" and http.calls == []


def test_scope_mismatch_rejected(tmp_path, approval_for):
    action = base_action()
    result, http = run(action, approval_for(action, scope="schedule_post"), tmp_path)
    assert result["outcome"] == "refused" and any("scope" in r for r in result["reasons"])
    assert http.calls == []


def test_idempotent_second_execute_refused(tmp_path, approval_for):
    action = base_action()
    approval = approval_for(action)
    first, http = run(action, approval, tmp_path)
    assert first["outcome"] == "executed"
    second, http2 = run(action, approval, tmp_path)
    assert second["outcome"] == "refused" and any("already" in r for r in second["reasons"])
    assert http2.calls == []


def test_uncertain_failure_also_blocks_retry(tmp_path, approval_for):
    def boom(method, url, headers, body):
        raise OSError(f"connection reset with header {headers}")
    action = base_action()
    result = ex.execute(action, approval_for(action), dry_run=False, marketing_root=tmp_path, http=boom,
                        secret=secrets, now=NOW, allowed_signers=SIGNERS["path"])
    assert result["outcome"] == "uncertain"
    again, http = run(action, approval_for(action), tmp_path)
    assert again["outcome"] == "refused" and http.calls == []
    assert SENTINEL not in json.dumps(receipts(tmp_path))


def test_real_execute_requires_receipt_store(approval_for):
    action = base_action()
    http = FakeHTTP()
    result = ex.execute(action, approval_for(action), dry_run=False, marketing_root=None, http=http,
                        secret=secrets, now=NOW, allowed_signers=SIGNERS["path"])
    assert result["outcome"] == "refused" and http.calls == []


def test_receipts_contain_no_secrets(tmp_path, approval_for):
    for kind in ("create_campaign", "schedule_post", "send_broadcast", "create_experiment"):
        action = base_action(kind, id=f"act-{kind}")
        http = FakeHTTP([{"id": "x1", "token": SENTINEL}, {"id": "x2"}])
        result, http = run(action, approval_for(action), tmp_path, http=http)
        assert result["outcome"] == "executed", result
        assert any(SENTINEL in json.dumps(c["headers"]) for c in http.calls)  # the secret was actually used
        assert SENTINEL not in json.dumps(result)
    text = "".join(p.read_text() for p in (tmp_path / "receipts").glob("*.json"))
    assert text and SENTINEL not in text


def test_resend_defaults_to_test_send_to_founder(tmp_path, approval_for):
    action = base_action("send_broadcast")
    result, http = run(action, approval_for(action), tmp_path)
    assert result["outcome"] == "executed"
    assert len(http.calls) == 1
    assert http.calls[0]["url"].endswith("/emails")
    assert http.calls[0]["body"]["to"] == ["founder@example.test"]


def test_resend_requires_audience_and_founder_email(tmp_path, approval_for):
    action = base_action("send_broadcast")
    del action["provider_request"]["audience_id"]
    result, http = run(action, approval_for(action), tmp_path)
    assert result["outcome"] == "refused" and http.calls == []
    action = base_action("send_broadcast", id="act-2")
    approval = approval_for(action, founder_email="")
    result, http = run(action, approval, tmp_path)
    assert result["outcome"] == "refused" and http.calls == []


def test_resend_full_broadcast_only_when_test_send_explicitly_false(tmp_path, approval_for):
    action = base_action("send_broadcast")
    action["provider_request"]["test_send"] = False
    result, http = run(action, approval_for(action), tmp_path)
    assert result["outcome"] == "executed"
    assert [c["url"] for c in http.calls] == ["https://api.resend.com/broadcasts",
                                              "https://api.resend.com/broadcasts/prov-1/send"]
    assert http.calls[0]["body"]["send"] is False and http.calls[0]["body"]["segment_id"] == "aud-1"


def test_postiz_schedules_never_posts_now(tmp_path, approval_for):
    action = base_action("schedule_post")
    result, http = run(action, approval_for(action), tmp_path)
    assert result["outcome"] == "executed"
    assert http.calls[0]["url"] == "https://provider.example.test/public/v1/posts"
    assert http.calls[0]["body"]["type"] == "schedule"
    action = base_action("schedule_post", id="act-now")
    action["provider_request"]["type"] = "now"
    result, http = run(action, approval_for(action), tmp_path)
    assert result["outcome"] == "refused" and http.calls == []


def test_posthog_experiment_is_created_as_draft(tmp_path, approval_for):
    action = base_action("create_experiment")
    result, http = run(action, approval_for(action), tmp_path)
    assert result["outcome"] == "executed"
    assert "/experiments/" in http.calls[0]["url"] and "start_date" not in http.calls[0]["body"]
    action = base_action("create_experiment", id="act-launch")
    action["provider_request"]["start_date"] = "2026-11-01T00:00:00Z"
    result, http = run(action, approval_for(action), tmp_path)
    assert result["outcome"] == "refused" and http.calls == []


def test_unknown_action_kind_refused(tmp_path, approval_for):
    action = base_action()
    action["action_kind"] = "send_pitch"
    result, http = run(action, approval_for(action), tmp_path)
    assert result["outcome"] == "refused" and http.calls == []


def test_digest_binds_provider_request():
    action = base_action()
    before = authorization_digest(action)
    action["provider_request"]["name"] = "Other"
    assert authorization_digest(action) != before




# --------------------------------------------------------------------------- signed approvals

def test_unsigned_approval_refused(tmp_path, approval_for):
    action = base_action()
    result, http = run(action, approval_for(action, signed=False), tmp_path)
    assert result["outcome"] == "refused" and any("not signed" in r for r in result["reasons"])
    assert http.calls == []


def test_wrong_signer_refused(tmp_path, approval_for):
    action = base_action()
    result, http = run(action, approval_for(action, key="mallory"), tmp_path, dry_run=True)
    assert result["outcome"] == "refused" and any("signature is invalid" in r for r in result["reasons"])


def test_signature_over_different_digest_refused(tmp_path, approval_for):
    other = base_action()
    other["provider_request"]["spend_cap"] = 999999
    signed_other = approval_for(other)
    action = base_action()
    forged = dict(signed_other, digest=authorization_digest(action))  # swap digest, keep old signature
    result, http = run(action, forged, tmp_path, dry_run=True)
    assert result["outcome"] == "refused" and any("signature is invalid" in r for r in result["reasons"])


def test_tampered_founder_email_or_root_invalidates_signature(tmp_path, approval_for):
    action = base_action("send_broadcast")
    approval = dict(approval_for(action), founder_email="attacker@example.test")
    result, http = run(action, approval, tmp_path)
    assert result["outcome"] == "refused" and http.calls == []


def test_missing_allowed_signers_refused_with_setup_steps(tmp_path, approval_for):
    action = base_action()
    result, http = run(action, approval_for(action), tmp_path, dry_run=True,
                       allowed_signers=tmp_path / "nope" / "allowed_signers")
    assert result["outcome"] == "refused"
    assert any("allowed_signers" in r and "ssh-keygen -t ed25519" in r for r in result["reasons"])


def test_valid_signature_accepted_in_dry_run(tmp_path, approval_for):
    action = base_action()
    result, http = run(action, approval_for(action), tmp_path, dry_run=True)
    assert result["outcome"] == "dry_run", result
    assert http.calls == []


def test_approval_bound_to_marketing_root(tmp_path, approval_for):
    action = base_action()
    approval = approval_for(action)
    first, _ = run(action, approval, tmp_path)
    assert first["outcome"] == "executed"
    elsewhere = tmp_path / "other-root"
    result, http = run(action, approval, tmp_path, marketing_root=elsewhere)
    assert result["outcome"] == "refused" and any("marketing root" in r for r in result["reasons"])
    assert http.calls == []


def test_action_id_required_in_approval(tmp_path, approval_for):
    action = base_action()
    result, http = run(action, approval_for(action, action_id=""), tmp_path)
    assert result["outcome"] == "refused" and any("action_id" in r for r in result["reasons"])


def test_claim_without_final_receipt_is_uncertain(tmp_path, approval_for):
    action = base_action()
    (tmp_path / "receipts").mkdir()
    (tmp_path / "receipts" / "act-1.claim").write_text(json.dumps({"claimed_at": "2026-10-31T11:00:00+00:00", "pid": 4242}))
    result, http = run(action, approval_for(action), tmp_path)
    assert result["outcome"] == "uncertain" and "4242" in result["reasons"][0]
    assert http.calls == []


def test_claim_records_timestamp_and_pid(tmp_path, approval_for):
    action = base_action()
    run(action, approval_for(action), tmp_path)
    claim = json.loads((tmp_path / "receipts" / "act-1.claim").read_text())
    assert claim["pid"] == os.getpid() and claim["claimed_at"].startswith("2026-10-31")


def test_resend_broadcast_without_id_fails(tmp_path, approval_for):
    action = base_action("send_broadcast")
    action["provider_request"]["test_send"] = False
    result, http = run(action, approval_for(action), tmp_path, http=FakeHTTP([{"object": "broadcast"}]))
    assert result["outcome"] == "failed" and len(http.calls) == 1


def test_resend_send_failure_records_draft_id(tmp_path, approval_for):
    calls = []

    def flaky(method, url, headers, body):
        calls.append(url)
        if url.endswith("/send"):
            raise OSError("reset")
        return {"id": "draft-9"}

    action = base_action("send_broadcast")
    action["provider_request"]["test_send"] = False
    result = ex.execute(action, approval_for(action), dry_run=False, marketing_root=tmp_path, http=flaky,
                        secret=secrets, now=NOW, allowed_signers=SIGNERS["path"])
    assert result["outcome"] == "uncertain" and result["provider_ids"] == {"draft_broadcast_id": "draft-9"}
    assert receipts(tmp_path)[-1]["provider_ids"] == {"draft_broadcast_id": "draft-9"}


def test_postiz_requires_future_date(tmp_path, approval_for):
    action = base_action("schedule_post")
    action["provider_request"]["date"] = "2026-10-01T10:00:00Z"
    result, http = run(action, approval_for(action), tmp_path)
    assert result["outcome"] == "refused" and any("future" in r for r in result["reasons"])


def test_scrubbing_ignores_short_and_numeric_values():
    assert ex._scrub({"a": "12345678", "b": "short"}, ["12345678", "short"]) == {"a": "12345678", "b": "short"}
    assert ex._scrub({"a": "x-longsecret-x"}, ["longsecret"]) == {"a": "x-***-x"}


def test_ai_token_not_treated_as_agent():
    assert not ex.is_agent_identity("kai.ai")  # 'ai' alone is no longer an agent token
    assert ex.is_agent_identity("my-agent")


# --------------------------------------------------------------------------- CLI

@pytest.fixture
def cli(keys, monkeypatch, capsys):
    """In-process CLI with the fixed signers path patched for the test; the CLI exposes no override."""
    monkeypatch.setattr(ex, "default_signers_path", lambda: keys["signers"])

    def call(args):
        code = ex.main(args)
        out = capsys.readouterr()
        return code, out.out, out.err
    return call


def test_cli_request_sign_attach_and_dry_run(tmp_path, keys, cli):
    action = base_action()
    path = tmp_path / "action.json"
    path.write_text(json.dumps(action))
    root = tmp_path / "mk"
    code, out, err = cli(["approval-request", str(path), "--by", PRINCIPAL, "--marketing-root", str(root)])
    assert code == 0, err
    assert "ssh-keygen -Y sign" in out and "PAUSED" in out
    message = tmp_path / "action.approval-message.txt"
    assert message.read_text().startswith(authorization_digest(action) + "|create_campaign|")
    # the founder signs in their own terminal; simulated here with a throwaway test key
    subprocess.run(["ssh-keygen", "-Y", "sign", "-f", str(keys["founder"]), "-n", "marketing-approval", str(message)],
                   check=True, capture_output=True)
    code, out, err = cli(["attach-signature", str(path), f"{message}.sig"])
    assert code == 0, err
    code, out, err = cli(["run", str(path), "--approval", str(tmp_path / "action.approval.json"), "--marketing-root", str(root)])
    assert code == 0, err
    assert json.loads(out)["outcome"] == "dry_run"


def test_cli_attach_refuses_wrong_signer(tmp_path, keys, cli):
    path = tmp_path / "action.json"
    path.write_text(json.dumps(base_action()))
    assert cli(["approval-request", str(path), "--by", PRINCIPAL, "--marketing-root", str(tmp_path)])[0] == 0
    message = tmp_path / "action.approval-message.txt"
    subprocess.run(["ssh-keygen", "-Y", "sign", "-f", str(keys["mallory"]), "-n", "marketing-approval", str(message)],
                   check=True, capture_output=True)
    code, _, _ = cli(["attach-signature", str(path), f"{message}.sig"])
    assert code != 0 and not (tmp_path / "action.approval.json").exists()


def test_cli_request_refuses_agent_principal(tmp_path, cli):
    path = tmp_path / "action.json"
    path.write_text(json.dumps(base_action()))
    assert cli(["approval-request", str(path), "--by", "claude", "--marketing-root", str(tmp_path)])[0] != 0


def test_cli_exposes_no_signers_override():
    with pytest.raises(SystemExit):
        ex.main(["run", "a.json", "--approval", "b.json", "--marketing-root", "x", "--allowed-signers", "s"])


# --------------------------------------------------------------------------- fixed signers path

def test_signers_env_var_is_ignored(tmp_path, keys, approval_for, monkeypatch):
    monkeypatch.setenv("MARKETING_ALLOWED_SIGNERS", str(keys["signers"]))
    monkeypatch.setattr(ex, "default_signers_path", lambda: tmp_path / "absent" / "allowed_signers")
    action = base_action()
    result = ex.execute(action, approval_for(action), marketing_root=tmp_path, secret=secrets, now=NOW)
    assert result["outcome"] == "refused" and any("no allowed_signers file" in r for r in result["reasons"])


def test_default_signers_path_uses_real_home_not_env(monkeypatch, tmp_path):
    import pwd
    monkeypatch.setenv("HOME", str(tmp_path))
    assert ex.default_signers_path() == Path(pwd.getpwuid(os.getuid()).pw_dir) / ".config/business-strategist/allowed_signers"


def test_explicit_test_signers_path_works(tmp_path, keys, approval_for):
    action = base_action()
    result = ex.execute(action, approval_for(action), marketing_root=tmp_path, secret=secrets, now=NOW,
                        allowed_signers=keys["signers"])
    assert result["outcome"] == "dry_run", result


@pytest.mark.parametrize("target", ["file", "dir"])
def test_group_writable_signers_refused(tmp_path, keys, approval_for, target):
    folder = tmp_path / "cfg"
    folder.mkdir(mode=0o700)
    signers = folder / "allowed_signers"
    signers.write_text(keys["signers"].read_text())
    (signers if target == "file" else folder).chmod(0o664 if target == "file" else 0o770)
    action = base_action()
    result = ex.execute(action, approval_for(action), marketing_root=tmp_path, secret=secrets, now=NOW,
                        allowed_signers=signers)
    assert result["outcome"] == "refused" and any("group- or world-writable" in r for r in result["reasons"])


@pytest.mark.parametrize("where", ["repo", "temp"])
def test_signers_symlink_into_repo_or_temp_refused(tmp_path, keys, approval_for, where):
    link = tmp_path / "allowed_signers-link"
    link.symlink_to(ROOT / "AGENTS.md" if where == "repo" else keys["signers"])
    action = base_action()
    result = ex.execute(action, approval_for(action), marketing_root=tmp_path, secret=secrets, now=NOW,
                        allowed_signers=link)
    assert result["outcome"] == "refused" and any("symlink" in r for r in result["reasons"])


def test_cli_has_no_pin_or_self_approve_path():
    source = (ROOT / "scripts/marketing/execute.py").read_text()
    assert "MARKETING_APPROVAL_PIN" not in source and "isatty" not in source and "i-am-the-founder" not in source


def test_settings_deny_self_approval_paths():
    perms = json.loads((ROOT / ".claude/settings.json").read_text())["permissions"]
    required = ["Bash(*MARKETING_APPROVAL_PIN*)", "Bash(*MARKETING_ALLOWED_SIGNERS*)", "Bash(*ssh-keygen*-Y sign*)", "Write(**/*.approval.json)",
                "Edit(**/*.approval.json)", "Write(**/receipts/**)", "Edit(**/receipts/**)",
                "Write(~/.config/business-strategist/**)", "Edit(~/.config/business-strategist/**)",
                "Bash(*allowed_signers*)", "Bash(*-Y sign*)"]
    for rule in required:
        assert rule in perms["deny"], rule
    assert not any("execute.py" in rule or "ssh-keygen" in rule for rule in perms["allow"])


# --------------------------------------------------------------------------- pinned verifier and ownership

def test_hostile_path_ssh_keygen_is_ignored(tmp_path, approval_for, monkeypatch):
    fake_dir = tmp_path / "evil-bin"
    fake_dir.mkdir()
    fake = fake_dir / "ssh-keygen"
    fake.write_text("#!/bin/sh\nexit 0\n")
    fake.chmod(0o755)
    action = base_action()
    forged = approval_for(action, key="mallory")  # signed before the hostile PATH is installed
    monkeypatch.setenv("PATH", f"{fake_dir}:{os.environ.get('PATH', '')}")
    result, http = run(action, forged, tmp_path, dry_run=True)
    assert result["outcome"] == "refused" and any("signature is invalid" in r for r in result["reasons"])


def test_untrusted_verifier_location_refused(tmp_path, approval_for, monkeypatch):
    fake = tmp_path / "ssh-keygen"
    fake.write_text("#!/bin/sh\nexit 0\n")
    fake.chmod(0o755)
    monkeypatch.setattr(ex, "VERIFIER_CANDIDATES", (fake,))  # user-owned, not root-owned
    action = base_action()
    result, http = run(action, approval_for(action, key="mallory"), tmp_path, dry_run=True)
    assert result["outcome"] == "refused" and any("no trusted ssh-keygen" in r for r in result["reasons"])


def test_verifier_is_root_owned_system_binary():
    path, problems = ex.verifier_path()
    assert path is not None and str(path).startswith(("/usr/bin/", "/bin/")) and not problems


def _fake_stat(uid, extra_mode=0):
    real = os.stat

    def fake(path):
        info = real(path)
        return types.SimpleNamespace(st_uid=uid, st_mode=info.st_mode | extra_mode)
    return fake


def test_root_owned_signers_file_accepted(tmp_path, keys, approval_for, monkeypatch):
    monkeypatch.setattr(ex, "_stat", _fake_stat(0))
    assert ex.signers_file_problems(keys["signers"]) == []
    action = base_action()
    result, http = run(action, approval_for(action), tmp_path, dry_run=True)
    assert result["outcome"] == "dry_run", result


def test_group_writable_root_owned_signers_refused(keys, monkeypatch):
    monkeypatch.setattr(ex, "_stat", _fake_stat(0, stat.S_IWGRP))
    problems = ex.signers_file_problems(keys["signers"])
    assert problems and all("group- or world-writable" in p for p in problems)


def test_signers_owned_by_other_user_refused(keys, monkeypatch):
    monkeypatch.setattr(ex, "_stat", _fake_stat(os.getuid() + 12345))
    assert any("not owned by root" in p for p in ex.signers_file_problems(keys["signers"]))


def test_user_owned_signers_file_refused_even_read_only(tmp_path, keys, approval_for, monkeypatch):
    """C1: the agent runs as the founder's OS user, so a user-owned file (even 0444 in a 0700 dir) is forgeable."""
    monkeypatch.setattr(ex, "_stat", _fake_stat(os.getuid()))
    folder = tmp_path / "cfg"
    folder.mkdir(mode=0o700)
    signers = folder / "allowed_signers"
    signers.write_text(keys["signers"].read_text())
    signers.chmod(0o444)
    problems = ex.signers_file_problems(signers)
    assert problems and all("not owned by root" in p for p in problems)
    assert not any("user-owned" in p or "0444" in p for p in problems)
    action = base_action()
    result = ex.execute(action, approval_for(action), marketing_root=tmp_path, secret=secrets, now=NOW,
                        allowed_signers=signers)
    assert result["outcome"] == "refused"


def test_user_owned_signers_directory_refused(keys, monkeypatch):
    real = os.stat

    def fake(path):
        info = real(path)
        uid = 0 if Path(path).name == "allowed_signers" else os.getuid()
        return types.SimpleNamespace(st_uid=uid, st_mode=info.st_mode)
    monkeypatch.setattr(ex, "_stat", fake)
    problems = ex.signers_file_problems(keys["signers"])
    assert problems and all(str(keys["signers"].parent) in p for p in problems)


def test_no_user_owned_alternative_in_setup_text():
    source = (ROOT / "scripts/marketing/execute.py").read_text()
    assert "0444" not in source and "user-owned read-only" not in source
    assert "root:root" in ex.SETUP_STEPS and "passphrase" in ex.SETUP_STEPS


def test_signers_directory_symlink_into_temp_refused(tmp_path, keys, approval_for):
    link_dir = tmp_path / "cfg-link"
    link_dir.symlink_to(keys["signers"].parent, target_is_directory=True)
    action = base_action()
    result, http = run(action, approval_for(action), tmp_path, dry_run=True,
                       allowed_signers=link_dir / "allowed_signers")
    assert result["outcome"] == "refused" and any("symlink" in r for r in result["reasons"])


def test_runbook_step0_requires_root_owned_signers_and_dedicated_key():
    text = (ROOT / ".agents/skills/marketing-campaign-operator/references/first-campaign-runbook.md").read_text()
    step0 = text.split("## 0.", 1)[1].split("## 1.", 1)[0]
    assert "0444" not in step0 and "accepted but weaker" not in step0
    for phrase in ("dedicated", "passphrase", "ssh-agent", "outside the repository", "root"):
        assert phrase in step0, phrase
    doc = (ROOT / "references/marketing-execution.md").read_text()
    assert "0444" not in doc and "accepted but is weaker" not in doc


def test_cli_dry_run_prints_verified_signer(tmp_path, keys, approval_for, monkeypatch, capsys):
    """I3: the runbook's step-6 check reads the verified signer from the dry-run output."""
    monkeypatch.setattr(ex, "default_signers_path", lambda: keys["signers"])
    action = base_action()
    approval = approval_for(action, granted_at=(datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
                            valid_until=(datetime.now(timezone.utc) + timedelta(days=6)).isoformat())
    (tmp_path / "a.json").write_text(json.dumps(action))
    (tmp_path / "a.approval.json").write_text(json.dumps(approval))
    code = ex.main(["run", str(tmp_path / "a.json"), "--approval", str(tmp_path / "a.approval.json"),
                    "--marketing-root", str(tmp_path)])
    out = json.loads(capsys.readouterr().out)
    assert code == 0 and out["outcome"] == "dry_run" and out["verified_signer"] == PRINCIPAL


def test_cli_refusal_prints_no_verified_signer(tmp_path, keys, approval_for, monkeypatch, capsys):
    monkeypatch.setattr(ex, "default_signers_path", lambda: keys["signers"])
    action = base_action()
    approval = approval_for(action, key="mallory")
    (tmp_path / "a.json").write_text(json.dumps(action))
    (tmp_path / "a.approval.json").write_text(json.dumps(approval))
    code = ex.main(["run", str(tmp_path / "a.json"), "--approval", str(tmp_path / "a.approval.json"),
                    "--marketing-root", str(tmp_path)])
    out = json.loads(capsys.readouterr().out)
    assert code == 1 and "verified_signer" not in out
