"""Tests for scaffold-component.py."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "scaffold-component.py"


def test_scaffold_creates_three_files(tmp_path: Path) -> None:
    out_dir = tmp_path / "components"
    cmd = [
        sys.executable, str(SCRIPT),
        "--name", "Input",
        "--tier", "core",
        "--base", "input",
        "--output-dir", str(out_dir),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0, f"stderr: {result.stderr}"
    folder = out_dir / "core" / "input"
    assert (folder / "Input.tsx").exists()
    assert (folder / "Input.test.tsx").exists()
    assert (folder / "Input.stories.tsx").exists()


def test_component_file_uses_client_directive(tmp_path: Path) -> None:
    out_dir = tmp_path / "components"
    cmd = [sys.executable, str(SCRIPT), "--name", "Dialog", "--tier", "core", "--base", "dialog", "--output-dir", str(out_dir)]
    subprocess.run(cmd, check=True)
    text = (out_dir / "core" / "dialog" / "Dialog.tsx").read_text()
    assert '"use client"' in text


def test_test_file_imports_component(tmp_path: Path) -> None:
    out_dir = tmp_path / "components"
    cmd = [sys.executable, str(SCRIPT), "--name", "RadioGroup", "--tier", "core", "--base", "radio-group", "--output-dir", str(out_dir)]
    subprocess.run(cmd, check=True)
    text = (out_dir / "core" / "radio-group" / "RadioGroup.test.tsx").read_text()
    assert "RadioGroup" in text
    assert "render(" in text or "it(" in text or "test(" in text


def test_stories_file_has_default_export(tmp_path: Path) -> None:
    out_dir = tmp_path / "components"
    cmd = [sys.executable, str(SCRIPT), "--name", "Card", "--tier", "core", "--base", "card", "--output-dir", str(out_dir)]
    subprocess.run(cmd, check=True)
    text = (out_dir / "core" / "card" / "Card.stories.tsx").read_text()
    assert "export default" in text
    assert "Card" in text


def test_domains_tier_creates_nested_path(tmp_path: Path) -> None:
    out_dir = tmp_path / "components"
    cmd = [sys.executable, str(SCRIPT), "--name", "KpiCard", "--tier", "domains/dashboard", "--base", "card", "--output-dir", str(out_dir)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0, f"stderr: {result.stderr}"
    folder = out_dir / "domains" / "dashboard" / "kpi-card"
    assert (folder / "KpiCard.tsx").exists()
