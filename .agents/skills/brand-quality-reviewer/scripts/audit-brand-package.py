#!/usr/bin/env python3
"""Audit final brand package structure, manifests, and local HTML references."""

from __future__ import annotations

import argparse
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

REQUIRED_PATHS = [
    "BRAND-GUIDELINES.md",
    "DECISIONS.md",
    "PACKAGE-MANIFEST.md",
    "logos/source",
    "logos/export",
    "colors",
    "typography",
    "tokens",
    "ui",
    "imagery",
    "marketing",
    "qa",
]

STALE_PATTERNS = [
    "stages/imagery/IMAGERY-AND-VOICE.md",
    "../logo/",
    "../../tokens/",
    "Inkscape is not installed",
    "EPS exports are still missing",
]


class RefParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.refs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for key, value in attrs:
            if value and key in {"src", "href", "poster"}:
                self.refs.append(value)


def check_required(project: Path) -> list[str]:
    return [path for path in REQUIRED_PATHS if not (project / path).exists()]


def check_manifests(project: Path) -> list[str]:
    missing: list[str] = []
    for manifest in sorted((project / "logos" / "export").glob("*/export-manifest.json")):
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
        except Exception as exc:
            missing.append(f"{manifest}: invalid json: {exc}")
            continue
        for item in data:
            file = item.get("file")
            if file and not Path(file).exists():
                missing.append(f"{manifest}: missing {file}")
    return missing


def check_html_refs(project: Path) -> list[str]:
    missing: list[str] = []
    for html in sorted(project.glob("*/*.html")):
        parser = RefParser()
        parser.feed(html.read_text(encoding="utf-8"))
        for ref in parser.refs:
            if ref.startswith(("#", "http:", "https:", "mailto:", "tel:", "data:")):
                continue
            parsed = urlparse(ref)
            if parsed.scheme:
                continue
            if not (html.parent / parsed.path).resolve().exists():
                missing.append(f"{html}: {ref}")
    return missing


def check_stale_patterns(project: Path) -> list[str]:
    hits: list[str] = []
    paths = sorted(project.glob("*.md"))
    for subdir in ["qa", "ui", "logos/export"]:
        paths.extend(sorted((project / subdir).glob("*.md")))
        paths.extend(sorted((project / subdir).glob("*.html")))
    for path in paths:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in STALE_PATTERNS:
            if pattern in text:
                hits.append(f"{path}: {pattern}")
    return hits


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_dir", type=Path)
    args = parser.parse_args()
    project = args.project_dir

    result = {
        "missing_required": check_required(project),
        "missing_manifest_files": check_manifests(project),
        "missing_html_refs": check_html_refs(project),
        "stale_patterns": check_stale_patterns(project),
    }
    result["ok"] = not any(result.values())
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
