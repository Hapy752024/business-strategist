#!/usr/bin/env python3
"""Scaffold final CSS/tokens and an agent-readable brand skill package."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


DEFAULT_TOKENS = {
    "color": {
        "primary": "#233233",
        "primary_hover": "#1c2929",
        "secondary": "#7a8c8d",
        "accent": "#d97757",
        "success": "#16803c",
        "warning": "#b7791f",
        "error": "#c53030",
        "info": "#2563eb",
        "background": "#ffffff",
        "surface": "#f7f7f4",
        "text": "#141413",
        "text_muted": "#64645f",
        "border": "#deded8",
        "focus": "#2563eb",
    },
    "font": {
        "heading": "\"Inter\", system-ui, sans-serif",
        "body": "\"Inter\", system-ui, sans-serif",
    },
    "radius": {"sm": "4px", "md": "8px", "lg": "12px"},
    "spacing": {"unit": "8px"},
}


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "brand"


# Semantic slot -> preferred CSS variable suffixes, in priority order.
# Used to map brand-specific token files (e.g. --surelius-deep-olive) onto the
# generic export slots (--brand-color-primary).
COLOR_SLOTS = [
    ("primary", ["black", "primary", "brand"]),
    ("primary_hover", ["graphite", "primary-hover", "primary-dark"]),
    ("secondary", ["deep-olive", "secondary", "olive"]),
    ("accent", ["muted-peach", "accent", "peach"]),
    ("success", ["success"]),
    ("warning", ["warning"]),
    ("error", ["error"]),
    ("info", ["info", "deep-olive"]),
    ("background", ["warm-ivory", "background", "ivory"]),
    ("surface", ["porcelain", "surface"]),
    ("text", ["black", "text"]),
    ("text_muted", ["graphite", "text-muted", "muted"]),
    ("border", ["mist-grey", "border", "grey"]),
    ("focus", ["focus", "deep-olive"]),
]


def parse_css_vars(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    return dict(re.findall(r"(--[\w-]+)\s*:\s*([^;{]+);", text))


def tokens_from_css(path: Path, font_heading: str | None, font_body: str | None) -> dict:
    """Map a brand token CSS file onto the export token structure.

    Prints the slot mapping so a human can verify the guesses. Slots with no
    match fall back to DEFAULT_TOKENS and are reported explicitly.
    """
    css_vars = parse_css_vars(path)
    if not css_vars:
        raise SystemExit(f"no CSS custom properties found in {path}")

    def resolve(value: str, seen: tuple[str, ...] = ()) -> str:
        match = re.fullmatch(r"var\((--[\w-]+)\)", value.strip())
        if match and match.group(1) in css_vars and match.group(1) not in seen:
            return resolve(css_vars[match.group(1)], seen + (match.group(1),))
        return value.strip()

    def find(suffixes: list[str]) -> str | None:
        for suffix in suffixes:
            for name, value in css_vars.items():
                if suffix in name:
                    return resolve(value)
        return None

    color: dict = {}
    guesses: list[str] = []
    for slot, suffixes in COLOR_SLOTS:
        value = find(suffixes)
        if value is None:
            value = DEFAULT_TOKENS["color"][slot]
            guesses.append(f"  {slot}: DEFAULT {value} (no match)")
        else:
            guesses.append(f"  {slot}: {value}")
        color[slot] = value
    font = {
        "heading": font_heading or css_vars.get("--font-brand", DEFAULT_TOKENS["font"]["heading"]),
        "body": font_body or css_vars.get("--font-ui", DEFAULT_TOKENS["font"]["body"]),
    }
    print(f"token mapping from {path}:", file=sys.stderr)
    print("\n".join(guesses), file=sys.stderr)
    return {
        "color": color,
        "font": font,
        "radius": dict(DEFAULT_TOKENS["radius"]),
        "spacing": dict(DEFAULT_TOKENS["spacing"]),
        "raw": css_vars,
    }


def load_tokens(path: Path | None, font_heading: str | None = None, font_body: str | None = None) -> dict:
    if path is None:
        return DEFAULT_TOKENS
    if not path.exists():
        raise SystemExit(f"tokens file not found: {path} (refusing to export default placeholders)")
    if path.suffix.lower() == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    if path.suffix.lower() == ".css":
        return tokens_from_css(path, font_heading, font_body)
    raise SystemExit(f"unsupported tokens file type: {path.suffix} (expected .json or .css)")


def get(tokens: dict, group: str, name: str, fallback: str) -> str:
    return str(tokens.get(group, {}).get(name, fallback))


def css(tokens: dict) -> str:
    color = tokens.get("color", {})
    font = tokens.get("font", {})
    radius = tokens.get("radius", {})
    spacing = tokens.get("spacing", {})
    lines = [":root {"]
    for key, value in color.items():
        lines.append(f"  --brand-color-{key.replace('_', '-')}: {value};")
    for key, value in font.items():
        lines.append(f"  --brand-font-{key.replace('_', '-')}: {value};")
    for key, value in radius.items():
        lines.append(f"  --brand-radius-{key.replace('_', '-')}: {value};")
    for key, value in spacing.items():
        lines.append(f"  --brand-spacing-{key.replace('_', '-')}: {value};")
    lines.extend([
        "  --color-primary: var(--brand-color-primary);",
        "  --color-background: var(--brand-color-background);",
        "  --color-surface: var(--brand-color-surface);",
        "  --color-text: var(--brand-color-text);",
        "  --font-heading: var(--brand-font-heading);",
        "  --font-body: var(--brand-font-body);",
        "}",
        "",
    ])
    return "\n".join(lines)


def skill_md(brand: str, slug: str) -> str:
    return f"""---
name: {slug}-brand-guidelines
description: Applies the approved {brand} brand identity, visual style, colors, typography, UI tokens, and design rules to agent-generated artifacts.
---

# {brand} Brand Guidelines

Use this skill whenever an artifact should follow the {brand} corporate identity or corporate design system.

Rules:
- Read `references/DESIGN.md` before creating visual/UI/marketing artifacts.
- Use `references/branding.css` and `references/brand-tokens.json` as implementation tokens.
- Preserve logo, color, typography, spacing, radius, and component-state rules.
- Do not invent off-brand colors, fonts, or component styles.
- If a requested output conflicts with the guidelines, ask before deviating.
"""


def design_md(brand: str, tokens: dict) -> str:
    return f"""# {brand} DESIGN.md

## Overview

This file is the agent-readable source of truth for the approved {brand} identity. Apply it when generating websites, UI, marketing assets, documents, and other visual artifacts.

## Colors

### Brand & Accent

- Primary: `{get(tokens, "color", "primary", "#233233")}`
- Secondary: `{get(tokens, "color", "secondary", "#7a8c8d")}`
- Accent: `{get(tokens, "color", "accent", "#d97757")}`

### Surface

- Background: `{get(tokens, "color", "background", "#ffffff")}`
- Surface: `{get(tokens, "color", "surface", "#f7f7f4")}`
- Border: `{get(tokens, "color", "border", "#deded8")}`

### Text

- Text: `{get(tokens, "color", "text", "#141413")}`
- Muted text: `{get(tokens, "color", "text_muted", "#64645f")}`

### Semantic

- Success: `{get(tokens, "color", "success", "#16803c")}`
- Warning: `{get(tokens, "color", "warning", "#b7791f")}`
- Error: `{get(tokens, "color", "error", "#c53030")}`
- Info: `{get(tokens, "color", "info", "#2563eb")}`
- Focus: `{get(tokens, "color", "focus", "#2563eb")}`

## Typography

- Heading: `{get(tokens, "font", "heading", '"Inter", system-ui, sans-serif')}`
- Body: `{get(tokens, "font", "body", '"Inter", system-ui, sans-serif')}`

## Layout

- Spacing unit: `{get(tokens, "spacing", "unit", "8px")}`
- Radius small: `{get(tokens, "radius", "sm", "4px")}`
- Radius medium: `{get(tokens, "radius", "md", "8px")}`
- Radius large: `{get(tokens, "radius", "lg", "12px")}`

## Components

Define buttons, inputs, cards, navigation, alerts, badges, and links from the approved tokens. Include default, hover, active, focus-visible, disabled, loading, and error states where relevant.

## Do's and Don'ts

### Do

- Use named tokens from `branding.css`.
- Preserve approved color roles and hierarchy.
- Check contrast before finalizing text/UI.
- Keep generated artifacts consistent with approved logo, colors, typography, and spacing.

### Don't

- Do not introduce unapproved colors or fonts.
- Do not use color alone to communicate state.
- Do not create full new visual directions without explicit approval.

## Responsive Behavior

Use mobile, tablet, desktop, and wide desktop checks. Prevent text clipping, overlap, and broken asset rendering.

## Agent Prompt Guide

When asked to create artifacts, first load this file, then apply the tokens and component rules consistently.
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--brand-name", required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--tokens", type=Path, help="Brand tokens file (.json or .css); .css files are mapped onto the export structure")
    parser.add_argument("--font-heading", help="Override heading font stack")
    parser.add_argument("--font-body", help="Override body font stack")
    args = parser.parse_args()

    slug = slugify(args.brand_name)
    tokens = load_tokens(args.tokens, args.font_heading, args.font_body)
    token_dir = args.workspace / "tokens"
    skill_dir = args.workspace / "agent-skill" / slug
    refs = skill_dir / "references"
    token_dir.mkdir(parents=True, exist_ok=True)
    refs.mkdir(parents=True, exist_ok=True)

    css_text = css(tokens)
    tokens_text = json.dumps(tokens, indent=2) + "\n"
    (token_dir / "branding.css").write_text(css_text, encoding="utf-8")
    (token_dir / "brand-tokens.json").write_text(tokens_text, encoding="utf-8")
    (skill_dir / "SKILL.md").write_text(skill_md(args.brand_name, slug), encoding="utf-8")
    (refs / "DESIGN.md").write_text(design_md(args.brand_name, tokens), encoding="utf-8")
    (refs / "branding.css").write_text(css_text, encoding="utf-8")
    (refs / "brand-tokens.json").write_text(tokens_text, encoding="utf-8")

    print(json.dumps({
        "css": str(token_dir / "branding.css"),
        "tokens": str(token_dir / "brand-tokens.json"),
        "agent_skill": str(skill_dir),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
