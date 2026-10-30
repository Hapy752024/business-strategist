#!/usr/bin/env python3
"""Audit which provider env vars are set. Prints names and present/absent only, never values."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Mapping

from common import get_secret

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CAPABILITIES = ROOT / "config" / "source-capabilities.json"


def key_audit(capabilities_path: Path, environ: Mapping[str, str] | None = None) -> list[dict]:
    """Presence is resolved like the validators: get_secret (process env, then ~/.secrets).

    If `environ` is given, it is checked in addition (explicit overrides).
    """
    data = json.loads(Path(capabilities_path).read_text(encoding="utf-8"))
    rows = []
    for cap in data.get("capabilities", []):
        for env in cap.get("requires_env") or []:
            rows.append({
                "capability": cap["id"],
                "env": env,
                "present": bool((environ or {}).get(env)) or get_secret(env)[1] is not None,
                "family": cap.get("family", ""),
            })
    return rows


def main() -> int:
    rows = key_audit(DEFAULT_CAPABILITIES)
    print(f"{'family':<26}{'capability':<36}{'env':<36}status")
    for r in sorted(rows, key=lambda r: (r["family"], r["capability"], r["env"])):
        print(f"{r['family']:<26}{r['capability']:<36}{r['env']:<36}{'present' if r['present'] else 'absent'}")
    missing = sum(1 for r in rows if not r["present"])
    print(f"\n{len(rows) - missing} present, {missing} absent of {len(rows)} required env vars", file=sys.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
