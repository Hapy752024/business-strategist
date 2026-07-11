#!/usr/bin/env python3
from __future__ import annotations

import shutil
import subprocess

from common import finish


PROVIDER = "scrapling"


def main() -> int:
    cli = shutil.which("scrapling")
    if not cli:
        summary = {
            "status": "missing_cli",
            "required_cli": ["scrapling"],
            "install_hint": "pip install 'scrapling[fetchers]' && scrapling install",
            "cost_note": "Local hard-page fallback. It can launch browsers and should stay explicit/opt-in.",
        }
        return finish(PROVIDER, summary, {"ok": False, "status": "missing_cli"})

    proc = subprocess.run([cli, "--help"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=20)
    summary = {
        "status": "ok" if proc.returncode == 0 else "warn",
        "cli": cli,
        "returncode": proc.returncode,
        "fields": ["stdout", "stderr"],
        "cost_note": "Use only as an explicit fallback for pages normal providers cannot extract.",
    }
    return finish(PROVIDER, summary, {"ok": proc.returncode == 0, "stdout": proc.stdout[-1000:], "stderr": proc.stderr[-1000:]})


if __name__ == "__main__":
    raise SystemExit(main())
