#!/usr/bin/env python3
from __future__ import annotations

import shutil
import subprocess

from common import finish


PROVIDER = "markitdown"


def main() -> int:
    cli = shutil.which("markitdown")
    if not cli:
        summary = {
            "status": "missing_cli",
            "required_cli": ["markitdown"],
            "install_hint": "pip install 'markitdown[all]'",
            "cost_note": "Local document converter. No API credits unless optional cloud/OCR plugins are configured.",
        }
        return finish(PROVIDER, summary, {"ok": False, "status": "missing_cli"})

    proc = subprocess.run([cli, "--help"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=20)
    summary = {
        "status": "ok" if proc.returncode == 0 else "warn",
        "cli": cli,
        "returncode": proc.returncode,
        "fields": ["stdout", "stderr"],
        "cost_note": "Use only with explicit --document-paths so document context stays scoped.",
    }
    return finish(PROVIDER, summary, {"ok": proc.returncode == 0, "stdout": proc.stdout[-1000:], "stderr": proc.stderr[-1000:]})


if __name__ == "__main__":
    raise SystemExit(main())
