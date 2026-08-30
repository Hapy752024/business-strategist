#!/usr/bin/env python3
"""Generate 2-3 standalone HTML demo files for motion exploration.

Modes:
  pillar  --pillar <name> --tokens <json> --output-dir <path>
  element --category <name> --element <name> --pillar <name> --tokens <json> --output-dir <path>

The script always emits exactly 3 demo files (option-1.html, option-2.html, option-3.html),
each a standalone HTML+CSS+JS file demonstrating the pillar/element with different starting tokens.

Exit codes:
  0 = success
  2 = usage error
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

OPTION_LABELS = ["Snappy", "Smooth", "Bouncy"]


def build_css_vars(pillar: str, tokens: dict) -> str:
    lines = [":root {"]
    for d in tokens.get("durations", []):
        lines.append(f"  --motion-duration-{pillar}-{d['variant']}: {d['ms']}ms;")
    for e in tokens.get("easings", []):
        lines.append(f"  --motion-ease-{pillar}-{e['variant']}: {e['cssBezier']};")
    for s in tokens.get("springs", []):
        lines.append(f"  --motion-spring-{pillar}-{s['variant']}-stiffness: {s['stiffness']};")
        lines.append(f"  --motion-spring-{pillar}-{s['variant']}-damping: {s['damping']};")
    lines.append("}")
    return "\n".join(lines)


def pillar_demo_html(pillar: str, tokens: dict, variant_index: int, label: str) -> str:
    # Variant 1 = fast, 2 = default, 3 = slow (or first/second/third duration if available)
    durations = tokens.get("durations", [])
    if not durations:
        duration_css = f"  --motion-duration-{pillar}-demo: 200ms;"
        easing_css = f"  --motion-ease-{pillar}-demo: ease-out;"
    else:
        d = durations[min(variant_index, len(durations) - 1)]
        duration_css = f"  --motion-duration-{pillar}-demo: {d['ms']}ms;"
        easings = tokens.get("easings", [])
        if easings:
            e = easings[min(variant_index, len(easings) - 1)]
            easing_css = f"  --motion-ease-{pillar}-demo: {e['cssBezier']};"
        else:
            easing_css = f"  --motion-ease-{pillar}-demo: ease-out;"

    css_vars = build_css_vars(pillar, tokens)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{pillar} pillar — {label}</title>
<style>
{css_vars}
{duration_css}
{easing_css}
.demo-box {{
  width: 200px; height: 200px; background: #4f46e5; border-radius: 12px;
  margin: 80px auto;
  transition: transform var(--motion-duration-{pillar}-demo) var(--motion-ease-{pillar}-demo),
              box-shadow var(--motion-duration-{pillar}-demo) var(--motion-ease-{pillar}-demo);
}}
.demo-box:hover {{
  transform: scale(1.05);
  box-shadow: 0 12px 32px rgba(0,0,0,0.18);
}}
</style>
</head>
<body>
<div class="demo-box"></div>
<p style="text-align:center; font-family: system-ui;">Variant: {label} — hover the box.</p>
</body>
</html>
"""


def element_demo_html(category: str, element: str, pillar: str, tokens: dict, variant_index: int, label: str) -> str:
    durations = tokens.get("durations", [])
    easings = tokens.get("easings", [])
    if not durations:
        duration_ref = f"var(--motion-duration-{pillar}-default, 150ms)"
    else:
        d = durations[min(variant_index, len(durations) - 1)]
        duration_ref = f"var(--motion-duration-{pillar}-{d['variant']}, {d['ms']}ms)"
    if not easings:
        easing_ref = "ease-out"
    else:
        e = easings[min(variant_index, len(easings) - 1)]
        easing_ref = f"var(--motion-ease-{pillar}-{e['variant']}, {e['cssBezier']})"

    css_vars = build_css_vars(pillar, tokens)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{category}/{element} — {label}</title>
<style>
{css_vars}
.btn {{
  display: inline-block; padding: 12px 24px; background: #4f46e5; color: white;
  border: none; border-radius: 8px; cursor: pointer;
  transition: transform {duration_ref} {easing_ref};
}}
.btn:active {{ transform: scale(0.95); }}
</style>
</head>
<body style="text-align:center; padding: 80px; font-family: system-ui;">
<button class="btn">Press me</button>
<p>Variant: {label} — click the button.</p>
</body>
</html>
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)

    p_pillar = sub.add_parser("pillar")
    p_pillar.add_argument("--pillar", required=True)
    p_pillar.add_argument("--tokens", required=True, type=Path)
    p_pillar.add_argument("--output-dir", required=True, type=Path)

    p_elem = sub.add_parser("element")
    p_elem.add_argument("--category", required=True)
    p_elem.add_argument("--element", required=True)
    p_elem.add_argument("--pillar", required=True)
    p_elem.add_argument("--tokens", required=True, type=Path)
    p_elem.add_argument("--output-dir", required=True, type=Path)

    args = parser.parse_args(argv)
    tokens = json.loads(args.tokens.read_text())
    args.output_dir.mkdir(parents=True, exist_ok=True)

    for i, label in enumerate(OPTION_LABELS):
        if args.mode == "pillar":
            html = pillar_demo_html(args.pillar, tokens, i, label)
        else:
            html = element_demo_html(args.category, args.element, args.pillar, tokens, i, label)
        (args.output_dir / f"option-{i+1}.html").write_text(html)

    print(f"Wrote 3 demos to {args.output_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
