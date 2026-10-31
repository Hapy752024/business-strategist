"""Tests for validate-motion-tokens.py."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "validate-motion-tokens.py"


def run_validator(css: str | None, ts: str | None, tmp_path: Path) -> subprocess.CompletedProcess[str]:
    css_path = tmp_path / "motion-tokens.css"
    ts_path = tmp_path / "motion-tokens.ts"
    css_path.write_text(css or "")
    ts_path.write_text(ts or "")
    cmd = [sys.executable, str(SCRIPT), "--css", str(css_path), "--ts", str(ts_path)]
    return subprocess.run(cmd, capture_output=True, text=True)


def test_valid_css_and_ts_passes(tmp_path: Path) -> None:
    css = """
    :root {
      --motion-duration-responsive-fast: 100ms;
      --motion-duration-responsive-default: 150ms;
      --motion-ease-responsive-standard: cubic-bezier(0.25, 1, 0.5, 1);
      --motion-spring-expressive-default-stiffness: 300;
      --motion-spring-expressive-default-damping: 30;
    }
    """
    ts = """
    export const motionPillars = {
      responsive: {
        durations: { fast: 100, default: 150 },
        easings: { standard: [0.25, 1, 0.5, 1] },
        springs: {}
      },
      expressive: {
        durations: {},
        easings: {},
        springs: { default: { stiffness: 300, damping: 30 } }
      }
    } as const;
    """
    result = run_validator(css, ts, tmp_path)
    assert result.returncode == 0, f"Expected pass, got stderr: {result.stderr}"


def test_css_missing_semicolon_fails(tmp_path: Path) -> None:
    css = ":root { --motion-duration-responsive-fast: 100ms }"  # missing semicolon
    ts = "export const motionPillars = { responsive: { durations: { fast: 100 }, easings: {}, springs: {} } } as const;"
    result = run_validator(css, ts, tmp_path)
    assert result.returncode == 1, f"Expected fail, got stdout: {result.stdout}"


def test_css_non_ms_duration_fails(tmp_path: Path) -> None:
    css = ":root { --motion-duration-responsive-fast: 0.1s; }"
    ts = "export const motionPillars = { responsive: { durations: { fast: 100 }, easings: {}, springs: {} } } as const;"
    result = run_validator(css, ts, tmp_path)
    assert result.returncode == 1


def test_css_non_positive_duration_fails(tmp_path: Path) -> None:
    css = ":root { --motion-duration-responsive-fast: 0ms; }"
    ts = "export const motionPillars = { responsive: { durations: { fast: 100 }, easings: {}, springs: {} } } as const;"
    result = run_validator(css, ts, tmp_path)
    assert result.returncode == 1


def test_spring_missing_damping_fails(tmp_path: Path) -> None:
    css = ":root { --motion-spring-expressive-default-stiffness: 300; }"  # no damping
    ts = "export const motionPillars = { expressive: { durations: {}, easings: {}, springs: { default: { stiffness: 300, damping: 30 } } } } as const;"
    result = run_validator(css, ts, tmp_path)
    assert result.returncode == 1


def test_ts_missing_motion_pillars_export_fails(tmp_path: Path) -> None:
    css = ":root { --motion-duration-responsive-fast: 100ms; }"
    ts = "export const somethingElse = {} as const;"
    result = run_validator(css, ts, tmp_path)
    assert result.returncode == 1


def test_pillar_mismatch_between_css_and_ts_fails(tmp_path: Path) -> None:
    css = ":root { --motion-duration-responsive-fast: 100ms; }"  # responsive
    ts = "export const motionPillars = { expressive: { durations: {}, easings: {}, springs: {} } } as const;"  # expressive, not responsive
    result = run_validator(css, ts, tmp_path)
    assert result.returncode == 1


def test_missing_file_returns_usage_error(tmp_path: Path) -> None:
    cmd = [sys.executable, str(SCRIPT), "--css", str(tmp_path / "nope.css"), "--ts", str(tmp_path / "nope.ts")]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 2
