#!/usr/bin/env python3
"""Apply brand + motion tokens to a component .tsx file in place.

Replaces:
  - Tailwind hardcoded color classes (bg-blue-500, text-red-600, etc.) -> var(--color-*)
  - transition-colors + duration-<N> + ease-<name> -> motion token CSS vars

This is a conservative regex-based pass. It does not try to fully parse TSX.
The intent is to remove the most common hardcoded-value patterns; the skill
reviews the result before saving.

Exit codes:
  0 = success (file may or may not have been modified)
  2 = usage error
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Map common Tailwind color classes to brand semantic tokens.
# This is a starting point; the skill refines per-component.
COLOR_CLASS_MAP = {
    r"\bbg-(?:blue|indigo|violet|purple)-(?:500|600)\b": "bg-[var(--color-primary)]",
    r"\btext-(?:blue|indigo|violet|purple)-(?:500|600)\b": "text-[var(--color-primary)]",
    r"\bbg-(?:red|rose)-(?:500|600)\b": "bg-[var(--color-destructive)]",
    r"\btext-(?:red|rose)-(?:500|600)\b": "text-[var(--color-destructive)]",
    r"\bbg-white\b": "bg-[var(--color-background)]",
    r"\btext-(?:gray|slate)-(?:700|900)\b": "text-[var(--color-foreground)]",
    r"\btext-(?:gray|slate)-(?:400|500)\b": "text-[var(--color-muted-foreground)]",
    r"\bplaceholder:(?:gray|slate)-(?:400|500)\b": "placeholder:text-[var(--color-muted-foreground)]",
}

# Transition classes -> motion tokens
TRANSITION_RE = re.compile(
    r"\btransition-(?:colors|all|opacity|transform)\b\s+duration-(\d+)\s+ease-(?:out|in|in-out|linear)\b"
)


def apply_color_replacements(text: str) -> str:
    for pattern, replacement in COLOR_CLASS_MAP.items():
        text = re.sub(pattern, replacement, text)
    return text


def apply_transition_replacements(text: str) -> str:
    def swap(_m: re.Match) -> str:
        return (
            "transition-[border-color,box-shadow,transform] "
            "duration-[var(--motion-duration-responsive-default)] "
            "ease-[var(--motion-ease-responsive-standard)]"
        )
    return TRANSITION_RE.sub(swap, text)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--component", required=True, type=Path)
    parser.add_argument("--tokens", required=True, type=Path)
    parser.add_argument("--motion-css", required=True, type=Path)
    parser.add_argument("--motion-ts", required=True, type=Path)
    args = parser.parse_args(argv)

    if not args.component.exists():
        print(f"Component file not found: {args.component}", file=sys.stderr)
        return 2
    for label, p in [("tokens", args.tokens), ("motion-css", args.motion_css), ("motion-ts", args.motion_ts)]:
        if not p.exists():
            print(f"{label} file not found: {p}", file=sys.stderr)
            return 2

    text = args.component.read_text()
    new_text = apply_transition_replacements(apply_color_replacements(text))

    if new_text != text:
        args.component.write_text(new_text)
        print(f"Applied tokens to {args.component}")
    else:
        print(f"No changes needed in {args.component}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
