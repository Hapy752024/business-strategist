#!/usr/bin/env python3
"""Preflight check for the brand identity skill family."""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
from pathlib import Path


ROOT = Path.cwd()
SKILLS = ROOT / ".agents" / "skills"


def exists(path: Path) -> bool:
    return path.exists()


def command(name: str) -> bool:
    return shutil.which(name) is not None


def python_module(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def local_venv_module(name: str) -> bool:
    python = ROOT / ".brand-tools" / "venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not python.exists():
        return False
    result = subprocess.run(
        [str(python), "-c", f"import {name}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.returncode == 0


def main() -> int:
    required_skills = [
        "brand-discovery-interviewer",
        "brand-workspace-manager",
        "brand-guideline-researcher",
        "brand-typography-researcher",
        "brand-strategy-director",
        "brand-asset-producer",
        "brand-ui-kit-producer",
        "brand-frontend-app-designer",
        "brand-quality-reviewer",
        "brand-exporter",
        "brand-guidelines-writer",
    ]
    missing_skills = [name for name in required_skills if not exists(SKILLS / name / "SKILL.md")]

    checks = {
        "skills": {
            "ok": not missing_skills,
            "missing": missing_skills,
            "install_command": "Restore/copy the missing .agents/skills/brand-* folders from this skill package.",
        },
        "inkscape": {
            "ok": command("inkscape"),
            "install_command": "sudo apt-get update && sudo apt-get install -y inkscape",
        },
        "imagemagick": {
            "ok": command("magick") or command("convert"),
            "install_command": "sudo apt-get update && sudo apt-get install -y imagemagick",
        },
        "pillow": {
            "ok": python_module("PIL") or local_venv_module("PIL"),
            "install_command": "python3 .agents/skills/brand-designer/scripts/install-brand-tooling.py --mode temp",
        },
        "cairosvg": {
            "ok": python_module("cairosvg") or local_venv_module("cairosvg"),
            "install_command": "python3 .agents/skills/brand-designer/scripts/install-brand-tooling.py --mode temp",
        },
        "openrouter_env": {
            "ok": bool(os.environ.get("OPENROUTER_API_KEY")) or exists(ROOT / ".env"),
            "install_command": "cp .agents/skills/brand-asset-producer/assets/.env.example .env",
        },
        "frontend_design_skill": {
            "ok": exists(SKILLS / "frontend-design" / "SKILL.md"),
            "install_command": "Install the Anthropic frontend-design skill with your normal Claude/Codex skill installer.",
            "optional": True,
        },
    }

    required_missing = {
        name: data
        for name, data in checks.items()
        if not data["ok"] and not data.get("optional")
    }
    optional_missing = {
        name: data
        for name, data in checks.items()
        if not data["ok"] and data.get("optional")
    }
    print(json.dumps({
        "ok": not required_missing,
        "required_missing": required_missing,
        "optional_missing": optional_missing,
        "install_options": [
            "1. Continue discovery/strategy now and install export tools later.",
            "2. Temporary local install: python3 .agents/skills/brand-designer/scripts/install-brand-tooling.py --mode temp",
            "3. System install commands: python3 .agents/skills/brand-designer/scripts/install-brand-tooling.py --mode system --print-only",
        ],
        "all_checks": checks,
    }, indent=2))
    return 0 if not required_missing else 1


if __name__ == "__main__":
    raise SystemExit(main())
