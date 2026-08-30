"""Tests for promote-motion-iteration.py."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "promote-motion-iteration.py"


def _setup_project(tmp_path: Path) -> Path:
    project = tmp_path / "brand-projects" / "acme"
    (project / "stages" / "motion" / "pillars" / "responsive").mkdir(parents=True)
    (project / "stages" / "motion" / "pillars" / "responsive" / "tokens.json").write_text(json.dumps({
        "durations": [{"variant": "default", "ms": 150}],
        "easings": [{"variant": "standard", "cssBezier": "cubic-bezier(0.25, 1, 0.5, 1)"}],
        "springs": []
    }))
    return project


def test_promote_pillar_copies_tokens_to_canonical(tmp_path: Path) -> None:
    project = _setup_project(tmp_path)
    cmd = [sys.executable, str(SCRIPT), "--project", str(project), "--phase", "pillar", "--name", "responsive"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0, f"stderr: {result.stderr}"
    canonical = project / "motion" / "pillars" / "responsive" / "tokens.json"
    assert canonical.exists(), f"Canonical file not created at {canonical}"


def test_promote_element_copies_spec_to_canonical(tmp_path: Path) -> None:
    project = _setup_project(tmp_path)
    elem_dir = project / "stages" / "motion" / "elements" / "press-feedback" / "button"
    elem_dir.mkdir(parents=True)
    (elem_dir / "spec.json").write_text(json.dumps({
        "category": "press-feedback",
        "element": "button",
        "pillar": "responsive",
        "description": "button press",
        "cssProperties": ["transform: scale(0.95)"],
        "overrides": []
    }))
    cmd = [sys.executable, str(SCRIPT), "--project", str(project), "--phase", "element", "--name", "press-feedback/button"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0, f"stderr: {result.stderr}"
    canonical = project / "motion" / "elements" / "press-feedback" / "button" / "spec.json"
    assert canonical.exists()


def test_promote_missing_source_returns_error(tmp_path: Path) -> None:
    project = _setup_project(tmp_path)
    cmd = [sys.executable, str(SCRIPT), "--project", str(project), "--phase", "pillar", "--name", "nonexistent"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 1


def test_dry_run_does_not_copy(tmp_path: Path) -> None:
    project = _setup_project(tmp_path)
    cmd = [sys.executable, str(SCRIPT), "--project", str(project), "--phase", "pillar", "--name", "responsive", "--dry-run"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0
    canonical = project / "motion" / "pillars" / "responsive" / "tokens.json"
    assert not canonical.exists()
