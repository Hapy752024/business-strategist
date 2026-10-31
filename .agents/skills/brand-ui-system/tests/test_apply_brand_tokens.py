"""Tests for apply-brand-tokens.py."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "apply-brand-tokens.py"


def _setup(tmp_path: Path, component_text: str) -> tuple[Path, Path, Path, Path]:
    comp = tmp_path / "Input.tsx"
    comp.write_text(component_text)
    tokens = tmp_path / "tokens.css"
    tokens.write_text(":root { --color-primary: #4f46e5; --radius-md: 8px; }")
    motion_css = tmp_path / "motion-tokens.css"
    motion_css.write_text(":root { --motion-duration-responsive-default: 150ms; --motion-ease-responsive-standard: cubic-bezier(0.25, 1, 0.5, 1); }")
    motion_ts = tmp_path / "motion-tokens.ts"
    motion_ts.write_text("export const motionPillars = { responsive: { durations: { default: 150 }, easings: { standard: [0.25, 1, 0.5, 1] }, springs: {} } } as const;")
    return comp, tokens, motion_css, motion_ts


def test_replaces_hardcoded_hex_colors(tmp_path: Path) -> None:
    comp, tokens, motion_css, motion_ts = _setup(tmp_path, '<button className="bg-blue-500 text-white">Hi</button>')
    cmd = [sys.executable, str(SCRIPT), "--component", str(comp), "--tokens", str(tokens), "--motion-css", str(motion_css), "--motion-ts", str(motion_ts)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0, f"stderr: {result.stderr}"
    out = comp.read_text()
    assert "bg-blue-500" not in out, f"Hardcoded color not replaced: {out}"
    assert "var(--color-primary)" in out or "var(--color-" in out


def test_replaces_default_transition_with_motion_token(tmp_path: Path) -> None:
    comp, tokens, motion_css, motion_ts = _setup(tmp_path, '<div className="transition-colors duration-200 ease-out">Hi</div>')
    cmd = [sys.executable, str(SCRIPT), "--component", str(comp), "--tokens", str(tokens), "--motion-css", str(motion_css), "--motion-ts", str(motion_ts)]
    subprocess.run(cmd, check=True)
    out = comp.read_text()
    assert "var(--motion-duration-responsive-default)" in out
    assert "var(--motion-ease-responsive-standard)" in out


def test_preserves_use_client_directive(tmp_path: Path) -> None:
    comp, tokens, motion_css, motion_ts = _setup(tmp_path, '"use client";\n\nexport const X = () => <div className="bg-blue-500">x</div>;')
    cmd = [sys.executable, str(SCRIPT), "--component", str(comp), "--tokens", str(tokens), "--motion-css", str(motion_css), "--motion-ts", str(motion_ts)]
    subprocess.run(cmd, check=True)
    out = comp.read_text()
    assert out.startswith('"use client"')


def test_missing_component_file_returns_usage_error(tmp_path: Path) -> None:
    cmd = [sys.executable, str(SCRIPT), "--component", str(tmp_path / "nope.tsx"), "--tokens", str(tmp_path / "tokens.css"), "--motion-css", str(tmp_path / "m.css"), "--motion-ts", str(tmp_path / "m.ts")]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 2
