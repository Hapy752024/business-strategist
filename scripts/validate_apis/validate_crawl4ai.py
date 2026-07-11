#!/usr/bin/env python3
from __future__ import annotations

import shutil
import subprocess

from common import finish


PROVIDER = "crawl4ai"


def main() -> int:
    cli = shutil.which("crwl")
    if not cli:
        summary = {
            "status": "missing_cli",
            "required_cli": ["crwl"],
            "install_hint": "pip install crawl4ai && crawl4ai-setup",
            "cost_note": "Local extractor. No API credits, but it can launch a browser and use local compute.",
        }
        return finish(PROVIDER, summary, {"ok": False, "status": "missing_cli"})

    proc = subprocess.run([cli, "--help"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=20)
    summary = {
        "status": "ok" if proc.returncode == 0 else "warn",
        "cli": cli,
        "returncode": proc.returncode,
        "fields": ["stdout", "stderr"],
        "cost_note": "Local extractor. Use as an explicit fallback to avoid Firecrawl scrape credits on a small URL set.",
    }
    return finish(PROVIDER, summary, {"ok": proc.returncode == 0, "stdout": proc.stdout[-1000:], "stderr": proc.stderr[-1000:]})


if __name__ == "__main__":
    raise SystemExit(main())
