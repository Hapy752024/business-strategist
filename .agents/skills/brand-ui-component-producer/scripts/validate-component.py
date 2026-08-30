#!/usr/bin/env python3
"""Validate a components/ tree against the scope and per-component rules.

Rules per component folder:
  1. <PascalName>.tsx exists
  2. <PascalName>.test.tsx exists
  3. <PascalName>.stories.tsx exists
  4. The .tsx file references at least one var(--color-*) or var(--motion-*) token
  5. The .tsx file contains no hardcoded hex colors (regex #[0-9a-fA-F]{3,8})

Scope rules:
  6. Every component listed in scope.json (core, extended, domains, custom) has a matching folder.

Exit codes:
  0 = all valid
  1 = one or more validation failures
  2 = usage error
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HEX_COLOR_RE = re.compile(r"#[0-9a-fA-F]{3,8}\b")
TOKEN_REF_RE = re.compile(r"var\(--(?:color|motion)-")


def pascal_to_kebab(name: str) -> str:
    out = []
    for i, c in enumerate(name):
        if c.isupper() and i > 0:
            out.append("-")
        out.append(c.lower())
    return "".join(out)


def validate_component_folder(folder: Path) -> list[str]:
    """Return a list of error strings (empty if valid)."""
    errors: list[str] = []
    # Find the .tsx file that is not .test.tsx or .stories.tsx
    tsx_files = [p for p in folder.glob("*.tsx") if not p.name.endswith((".test.tsx", ".stories.tsx"))]
    if not tsx_files:
        errors.append(f"{folder}: no component .tsx file found")
        return errors
    comp = tsx_files[0]
    pascal = comp.stem

    if not (folder / f"{pascal}.test.tsx").exists():
        errors.append(f"{folder}: missing {pascal}.test.tsx")
    if not (folder / f"{pascal}.stories.tsx").exists():
        errors.append(f"{folder}: missing {pascal}.stories.tsx")

    text = comp.read_text()
    if HEX_COLOR_RE.search(text):
        errors.append(f"{comp}: contains hardcoded hex color(s)")
    if not TOKEN_REF_RE.search(text):
        errors.append(f"{comp}: does not reference any var(--color-*) or var(--motion-*) token")
    return errors


def find_component_folder(components_dir: Path, tier: str, component_kebab: str) -> Path:
    return components_dir / tier / component_kebab


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--components-dir", required=True, type=Path)
    parser.add_argument("--scope", required=True, type=Path)
    args = parser.parse_args(argv)

    if not args.components_dir.exists():
        print(f"Components dir not found: {args.components_dir}", file=sys.stderr)
        return 2
    if not args.scope.exists():
        print(f"Scope file not found: {args.scope}", file=sys.stderr)
        return 2

    scope = json.loads(args.scope.read_text())
    errors: list[str] = []

    core_items = scope.get("core", [])
    if core_items is True:
        # core: true means all Core items; check known list
        core_items = [
            "input", "textarea", "radio-group", "checkbox", "toggle", "select", "combobox",
            "card", "badge", "avatar", "alert", "tooltip", "progress", "spinner", "skeleton", "empty-state",
            "tabs", "breadcrumb", "pagination", "menu", "sidebar", "navbar",
            "modal", "drawer", "popover", "accordion",
        ]
    elif core_items is False:
        core_items = []

    for kebab in core_items:
        folder = find_component_folder(args.components_dir, "core", kebab)
        if not folder.exists():
            errors.append(f"Missing core component folder: {folder}")
            continue
        errors.extend(validate_component_folder(folder))

    for kebab in scope.get("extended", []):
        folder = find_component_folder(args.components_dir, "extended", kebab)
        if not folder.exists():
            errors.append(f"Missing extended component folder: {folder}")
            continue
        errors.extend(validate_component_folder(folder))

    for domain_pack in scope.get("domains", []):
        pack_dir = args.components_dir / "domains" / domain_pack
        if not pack_dir.exists():
            errors.append(f"Missing domain pack folder: {pack_dir}")
            continue
        for folder in pack_dir.iterdir():
            if folder.is_dir():
                errors.extend(validate_component_folder(folder))

    for custom in scope.get("custom", []):
        folder = find_component_folder(args.components_dir, "custom", custom)
        if not folder.exists():
            errors.append(f"Missing custom component folder: {folder}")
            continue
        errors.extend(validate_component_folder(folder))

    if errors:
        for err in errors:
            print(f"VALIDATION ERROR: {err}", file=sys.stderr)
        return 1

    print(f"OK: all components in scope validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
