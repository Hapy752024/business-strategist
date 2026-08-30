"""Tests for generate-demo.py."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "generate-demo.py"


def test_pillar_mode_generates_three_html_files(tmp_path: Path) -> None:
    tokens = {
        "durations": [{"variant": "fast", "ms": 100}, {"variant": "default", "ms": 200}],
        "easings": [{"variant": "standard", "cssBezier": "cubic-bezier(0.25, 1, 0.5, 1)"}],
        "springs": []
    }
    tokens_path = tmp_path / "tokens.json"
    tokens_path.write_text(json.dumps(tokens))
    out_dir = tmp_path / "out"
    cmd = [sys.executable, str(SCRIPT), "pillar", "--pillar", "responsive", "--tokens", str(tokens_path), "--output-dir", str(out_dir)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0, f"stderr: {result.stderr}"
    htmls = list(out_dir.glob("option-*.html"))
    assert len(htmls) == 3, f"Expected 3 demos, found {len(htmls)}: {[p.name for p in htmls]}"
    for h in htmls:
        text = h.read_text()
        assert "<html" in text.lower()
        assert "var(--motion-duration-responsive-" in text or "cubic-bezier" in text


def test_element_mode_generates_three_html_files_referencing_pillar(tmp_path: Path) -> None:
    tokens = {
        "durations": [{"variant": "default", "ms": 150}],
        "easings": [{"variant": "standard", "cssBezier": "cubic-bezier(0.25, 1, 0.5, 1)"}],
        "springs": []
    }
    tokens_path = tmp_path / "tokens.json"
    tokens_path.write_text(json.dumps(tokens))
    out_dir = tmp_path / "out"
    cmd = [sys.executable, str(SCRIPT), "element", "--category", "press-feedback", "--element", "button", "--pillar", "responsive", "--tokens", str(tokens_path), "--output-dir", str(out_dir)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0, f"stderr: {result.stderr}"
    htmls = list(out_dir.glob("option-*.html"))
    assert len(htmls) == 3
    for h in htmls:
        text = h.read_text()
        assert "var(--motion-duration-responsive-" in text, f"Demo {h.name} does not reference pillar tokens"


def test_invalid_mode_returns_usage_error(tmp_path: Path) -> None:
    cmd = [sys.executable, str(SCRIPT), "bogus", "--output-dir", str(tmp_path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 2
