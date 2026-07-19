#!/usr/bin/env python3
"""Shared event emission for fetch/helper scripts.

Appends one JSONL event per call to research/agentic-events.jsonl (gitignored,
durable across sessions — unlike the previous /tmp location). This gives
CrewAI/smolagents-style step logs without adopting a runtime: who ran, with
what inputs, from which vendor, producing which artifact, and how it ended.

Emission must never break the caller: all failures are swallowed.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


def log_path() -> Path:
    override = os.environ.get("AGENTIC_EVENT_LOG")
    if override:
        return Path(override)
    return Path(__file__).resolve().parent.parent / "research" / "agentic-events.jsonl"


def emit(
    script: str,
    status: str,
    vendor: str = "",
    period: str = "",
    output_path: str = "",
    row_count: int | None = None,
    warnings: list[str] | None = None,
    failure_reason: str = "",
    inputs: dict | None = None,
) -> None:
    event = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "script": script,
        "status": status,
        "vendor": vendor,
        "period": period,
        "output_path": output_path,
        "row_count": row_count,
        "warnings": warnings or [],
        "failure_reason": failure_reason,
        "inputs": inputs or {},
    }
    try:
        path = log_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")
    except OSError:
        pass


def emit_for_argv(script: str, status: int, failure_reason: str = "") -> None:
    """Emit one event derived from sys.argv. status: process exit code."""
    argv = sys.argv[1:]

    def flag(name: str) -> str:
        if name in argv and argv.index(name) + 1 < len(argv):
            return argv[argv.index(name) + 1]
        return ""

    emit(
        script,
        "error" if failure_reason or status != 0 else "ok",
        output_path=flag("--output") or flag("--output-dir"),
        failure_reason=failure_reason,
        inputs={"argv": argv[:16]},
    )
