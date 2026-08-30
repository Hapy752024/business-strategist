"""Tests for validate-component.py."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "validate-component.py"


def _make_component(folder: Path, name: str, *, has_test: bool = True, has_stories: bool = True, hardcoded_color: bool = False, references_token: bool = True) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    comp_text = '"use client";\n\nexport const ' + name + ' = () => (\n  <div className="' + ("bg-blue-500" if hardcoded_color else "bg-[var(--color-primary)]") + '">x</div>\n);\n'
    (folder / f"{name}.tsx").write_text(comp_text)
    if has_test:
        (folder / f"{name}.test.tsx").write_text('import { describe, it, expect } from "vitest";\ndescribe("' + name + '", () => { it("renders", () => { expect(true).toBe(true); }); });\n')
    if has_stories:
        (folder / f"{name}.stories.tsx").write_text('export default {};\n')


def test_valid_components_pass(tmp_path: Path) -> None:
    comp_dir = tmp_path / "components"
    _make_component(comp_dir / "core" / "input", "Input")
    scope = {"core": ["input"], "extended": [], "domains": [], "custom": []}
    scope_path = tmp_path / "scope.json"
    scope_path.write_text(json.dumps(scope))
    cmd = [sys.executable, str(SCRIPT), "--components-dir", str(comp_dir), "--scope", str(scope_path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0, f"stderr: {result.stderr}"


def test_missing_test_file_fails(tmp_path: Path) -> None:
    comp_dir = tmp_path / "components"
    _make_component(comp_dir / "core" / "input", "Input", has_test=False)
    scope = {"core": ["input"], "extended": [], "domains": [], "custom": []}
    scope_path = tmp_path / "scope.json"
    scope_path.write_text(json.dumps(scope))
    cmd = [sys.executable, str(SCRIPT), "--components-dir", str(comp_dir), "--scope", str(scope_path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 1


def test_missing_stories_file_fails(tmp_path: Path) -> None:
    comp_dir = tmp_path / "components"
    _make_component(comp_dir / "core" / "input", "Input", has_stories=False)
    scope = {"core": ["input"], "extended": [], "domains": [], "custom": []}
    scope_path = tmp_path / "scope.json"
    scope_path.write_text(json.dumps(scope))
    cmd = [sys.executable, str(SCRIPT), "--components-dir", str(comp_dir), "--scope", str(scope_path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 1


def test_hardcoded_color_fails(tmp_path: Path) -> None:
    comp_dir = tmp_path / "components"
    _make_component(comp_dir / "core" / "input", "Input", hardcoded_color=True)
    scope = {"core": ["input"], "extended": [], "domains": [], "custom": []}
    scope_path = tmp_path / "scope.json"
    scope_path.write_text(json.dumps(scope))
    cmd = [sys.executable, str(SCRIPT), "--components-dir", str(comp_dir), "--scope", str(scope_path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 1


def test_component_not_referencing_token_fails(tmp_path: Path) -> None:
    comp_dir = tmp_path / "components"
    folder = comp_dir / "core" / "input"
    _make_component(folder, "Input", references_token=False)
    # Overwrite component to have neither hardcoded color nor token reference
    (folder / "Input.tsx").write_text('"use client";\n\nexport const Input = () => <div className="rounded-md">x</div>;\n')
    scope = {"core": ["input"], "extended": [], "domains": [], "custom": []}
    scope_path = tmp_path / "scope.json"
    scope_path.write_text(json.dumps(scope))
    cmd = [sys.executable, str(SCRIPT), "--components-dir", str(comp_dir), "--scope", str(scope_path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 1


def test_scope_missing_components_fails(tmp_path: Path) -> None:
    comp_dir = tmp_path / "components"
    _make_component(comp_dir / "core" / "input", "Input")
    scope = {"core": ["input", "radio-group"], "extended": [], "domains": [], "custom": []}  # radio-group missing
    scope_path = tmp_path / "scope.json"
    scope_path.write_text(json.dumps(scope))
    cmd = [sys.executable, str(SCRIPT), "--components-dir", str(comp_dir), "--scope", str(scope_path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 1


def test_usage_error_on_missing_scope_file(tmp_path: Path) -> None:
    cmd = [sys.executable, str(SCRIPT), "--components-dir", str(tmp_path), "--scope", str(tmp_path / "nope.json")]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 2
