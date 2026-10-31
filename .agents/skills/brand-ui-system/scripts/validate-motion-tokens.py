#!/usr/bin/env python3
"""Validate motion-tokens.css and motion-tokens.ts against the pillar schema.

Exit codes:
  0 = both files valid
  1 = one or more validation rules failed
  2 = usage error (missing file, wrong arguments)
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

DURATION_RE = re.compile(r"--motion-duration-([a-z0-9-]+)-([a-z0-9-]+):\s*([0-9]+)ms\s*;")
DURATION_ANY_RE = re.compile(r"--motion-duration-[a-z0-9-]+-[a-z0-9-]+:[^;\n}]*;?")
EASE_RE = re.compile(r"--motion-ease-([a-z0-9-]+)-([a-z0-9-]+):\s*([^;]+);")
SPRING_RE = re.compile(r"--motion-spring-([a-z0-9-]+)-([a-z0-9-]+)-(stiffness|damping):\s*([0-9.]+)\s*;")
NAMED_EASINGS = {"linear", "ease", "ease-in", "ease-out", "ease-in-out", "step-start", "step-end"}
CUBIC_BEZIER_RE = re.compile(r"cubic-bezier\(\s*(-?[0-9.]+)\s*,\s*(-?[0-9.]+)\s*,\s*(-?[0-9.]+)\s*,\s*(-?[0-9.]+)\s*\)")
TS_EXPORT_RE = re.compile(r"export\s+const\s+motionPillars\s*=", re.MULTILINE)
TS_PILLAR_KEYS_RE = re.compile(r"motionPillars\s*=\s*\{([^}]+(?:\{[^}]*\}[^}]*)*)\}", re.MULTILINE)


def parse_css(css_text: str) -> tuple[set[str], set[str], dict[tuple[str, str, str], float], list[str]]:
    """Returns (duration_pillars, ease_pillars, springs_by_pillar_variant, errors)."""
    errors: list[str] = []
    duration_pillars: set[str] = set()
    ease_pillars: set[str] = set()
    springs: dict[tuple[str, str, str], float] = {}

    if css_text.count("{") != css_text.count("}"):
        errors.append("CSS has unbalanced braces")

    for m in DURATION_RE.finditer(css_text):
        pillar, variant, ms_str = m.group(1), m.group(2), m.group(3)
        ms = int(ms_str)
        if ms <= 0:
            errors.append(f"--motion-duration-{pillar}-{variant}: non-positive value {ms}ms")
        duration_pillars.add(pillar)

    # Detect malformed duration declarations (missing semicolon, wrong unit, etc.)
    for m in DURATION_ANY_RE.finditer(css_text):
        decl = m.group(0).strip()
        if not DURATION_RE.search(decl):
            errors.append(f"malformed duration declaration: '{decl}'")

    for m in EASE_RE.finditer(css_text):
        pillar, variant, value = m.group(1), m.group(2), m.group(3).strip()
        is_named = value in NAMED_EASINGS
        is_bezier = bool(CUBIC_BEZIER_RE.fullmatch(value))
        if not (is_named or is_bezier):
            errors.append(f"--motion-ease-{pillar}-{variant}: invalid value '{value}'")
        ease_pillars.add(pillar)

    for m in SPRING_RE.finditer(css_text):
        pillar, variant, prop, val_str = m.group(1), m.group(2), m.group(3), m.group(4)
        val = float(val_str)
        if val <= 0:
            errors.append(f"--motion-spring-{pillar}-{variant}-{prop}: non-positive value {val}")
        springs[(pillar, variant, prop)] = val

    # Check spring stiffness/damping pairs
    stiffness_keys = {k for k in springs if k[2] == "stiffness"}
    damping_keys = {k for k in springs if k[2] == "damping"}
    for k in stiffness_keys:
        pair = (k[0], k[1], "damping")
        if pair not in damping_keys:
            errors.append(f"--motion-spring-{k[0]}-{k[1]}-stiffness has no matching -damping")
    for k in damping_keys:
        pair = (k[0], k[1], "stiffness")
        if pair not in stiffness_keys:
            errors.append(f"--motion-spring-{k[0]}-{k[1]}-damping has no matching -stiffness")

    return duration_pillars | ease_pillars | {k[0] for k in springs}, ease_pillars, springs, errors


def parse_ts(ts_text: str) -> tuple[set[str], list[str]]:
    """Returns (pillar_names, errors)."""
    errors: list[str] = []
    if not TS_EXPORT_RE.search(ts_text):
        errors.append("TS file missing 'export const motionPillars' declaration")
        return set(), errors
    if ts_text.count("{") != ts_text.count("}"):
        errors.append("TS file has unbalanced braces")
    # Extract top-level pillar keys (those at depth 1 inside motionPillars = { ... })
    # Simplified: find the first { after motionPillars = and walk depth.
    start = ts_text.find("motionPillars")
    if start == -1:
        return set(), errors
    brace_start = ts_text.find("{", start)
    if brace_start == -1:
        errors.append("TS motionPillars has no opening brace")
        return set(), errors
    depth = 0
    pillars: set[str] = set()
    i = brace_start
    key_re = re.compile(r"([a-zA-Z_][a-zA-Z0-9_]*)\s*:")

    def _try_key_at(idx: int) -> None:
        j = idx
        while j < len(ts_text) and ts_text[j] in " \t\n":
            j += 1
        m = key_re.match(ts_text[j:j + 80])
        if m:
            pillars.add(m.group(1))

    while i < len(ts_text):
        c = ts_text[i]
        if c == "{":
            depth += 1
            if depth == 1:
                _try_key_at(i + 1)
        elif c == "}":
            depth -= 1
            if depth == 0:
                break
        elif depth == 1 and c == ",":
            _try_key_at(i + 1)
        elif depth == 1 and c == "\n":
            _try_key_at(i + 1)
        i += 1
    return pillars, errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--css", required=True, type=Path)
    parser.add_argument("--ts", required=True, type=Path)
    args = parser.parse_args(argv)

    if not args.css.exists():
        print(f"CSS file not found: {args.css}", file=sys.stderr)
        return 2
    if not args.ts.exists():
        print(f"TS file not found: {args.ts}", file=sys.stderr)
        return 2

    css_text = args.css.read_text()
    ts_text = args.ts.read_text()

    css_pillars, _, _, css_errors = parse_css(css_text)
    ts_pillars, ts_errors = parse_ts(ts_text)

    all_errors = css_errors + ts_errors

    if css_pillars != ts_pillars:
        only_css = css_pillars - ts_pillars
        only_ts = ts_pillars - css_pillars
        if only_css:
            all_errors.append(f"Pillars in CSS but not TS: {sorted(only_css)}")
        if only_ts:
            all_errors.append(f"Pillars in TS but not CSS: {sorted(only_ts)}")

    if all_errors:
        for err in all_errors:
            print(f"VALIDATION ERROR: {err}", file=sys.stderr)
        return 1

    print(f"OK: {len(css_pillars)} pillar(s) validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
