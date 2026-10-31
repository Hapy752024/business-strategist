"""Providers dropped for lack of credentials/use stay gone from every registry."""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/evidence_scout"))
sys.path.insert(0, str(ROOT / "scripts/validate_apis"))

import collect  # noqa: E402
import run_all  # noqa: E402

REMOVED_CAPABILITIES = {"china_public", "china_social", "trustpilot_reviews", "bluesky"}
REMOVED_PROVIDERS = {
    "china_bilibili", "china_bilibili_comments", "china_v2ex", "china_web", "china_xiaohongshu",
    "trustpilot_reviews", "bluesky", "china_public", "china_social", "china",
}


def test_removed_providers_absent():
    caps = json.loads((ROOT / "config/source-capabilities.json").read_text())["capabilities"]
    ids = {c["id"] for c in caps}
    assert not ids & REMOVED_CAPABILITIES
    for cap in caps:
        referenced = {cap.get("collector_provider"), *cap.get("provider_aliases", []),
                      *cap.get("validation_providers", []), *cap.get("fallbacks", [])}
        assert not referenced & (REMOVED_PROVIDERS | REMOVED_CAPABILITIES | {"v2ex_public_hot"}), cap["id"]
        assert cap.get("family") != "china_sources"
    # collect.py: no dispatch entry, no alias expansion, no CLI flags
    for name in REMOVED_PROVIDERS - {"china"}:
        assert not hasattr(collect, f"collect_{name}"), name
    assert not hasattr(collect, "_collect_bluesky_query")
    assert collect.selected_providers("china_public,china_social,china") == ["china_public", "china_social", "china"]
    help_text = subprocess.run([sys.executable, str(ROOT / "scripts/evidence_scout/collect.py"), "--help"],
                               capture_output=True, text=True, check=True).stdout
    assert not re.search(r"trustpilot|china|bluesky", help_text, re.I)
    # validators
    assert "validate_bluesky.py" not in run_all.SCRIPTS
    assert not (ROOT / "scripts/validate_apis/validate_bluesky.py").exists()
    assert not (ROOT / "scripts/evidence_scout/providers/bluesky.py").exists()
