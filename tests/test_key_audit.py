import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/validate_apis"))

from key_audit import key_audit  # noqa: E402


def test_key_audit_flags_missing_env(tmp_path):
    rows = key_audit(ROOT / "config/source-capabilities.json", {"APIFY_TOKEN": "x"})
    missing = {r["env"] for r in rows if not r["present"]}
    assert "SERPER_DEV_API_KEY" in missing
    assert all(not r["present"] or r["env"] == "APIFY_TOKEN" for r in rows)
    assert all(set(r) == {"capability", "env", "present", "family"} for r in rows)
