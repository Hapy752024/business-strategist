import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/validate_apis"))

import key_audit as key_audit_module  # noqa: E402
from key_audit import key_audit  # noqa: E402


def test_key_audit_flags_missing_env(tmp_path, monkeypatch):
    monkeypatch.setattr(key_audit_module, "get_secret", lambda *n: (None, None))
    rows = key_audit(ROOT / "config/source-capabilities.json", {"APIFY_TOKEN": "x"})
    missing = {r["env"] for r in rows if not r["present"]}
    assert "SERPER_DEV_API_KEY" in missing
    assert all(not r["present"] or r["env"] == "APIFY_TOKEN" for r in rows)
    assert all(set(r) == {"capability", "env", "present", "family"} for r in rows)


def test_key_audit_resolves_secrets_like_validators(monkeypatch):
    monkeypatch.setattr(key_audit_module, "get_secret",
                        lambda *n: (n[0], "v") if n[0] == "SERPER_DEV_API_KEY" else (None, None))
    rows = key_audit(ROOT / "config/source-capabilities.json", {})
    by_env = {r["env"]: r["present"] for r in rows}
    assert by_env["SERPER_DEV_API_KEY"] is True
    assert by_env["META_ACCESS_TOKEN"] is False
