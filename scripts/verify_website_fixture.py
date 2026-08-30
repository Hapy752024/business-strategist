#!/usr/bin/env python3
"""Deterministic guardrails for the shipped website fixture.

This checks build-input contracts, not subjective visual quality. Visual review
remains a human release gate because static assertions cannot establish it.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REQUIRED_PREFERENCE_KEYS = {"profile_id", "version", "locale", "choices", "provenance"}
REQUIRED_MANIFEST_KEYS = {"schema_version", "website_id", "entry_mode", "stack", "preferences", "concept", "pages", "qa", "release"}
FORBIDDEN_PUBLIC_SECRETS = ("NEXT_PUBLIC_FAL", "NEXT_PUBLIC_API_KEY", "FAL_AI_API_KEY")


def verify(root: Path) -> list[str]:
    errors: list[str] = []
    package = root / "package.json"
    manifest = root / "website-manifest.json"
    preferences = root / "website-preferences.json"
    page = root / "app" / "page.tsx"
    experiment_component = root / "app" / "experiment-cta.tsx"
    layout = root / "app" / "layout.tsx"
    css = root / "app" / "globals.css"
    for path in (package, manifest, preferences, page, experiment_component, layout, css, root / "package-lock.json"):
        if not path.is_file():
            errors.append(f"missing required fixture file: {path.relative_to(root)}")
    if errors:
        return errors

    package_data = json.loads(package.read_text(encoding="utf-8"))
    if package_data.get("dependencies", {}).get("next") != "16.3.3":
        errors.append("fixture must pin the approved Next.js stable version (16.3.3)")
    if package_data.get("scripts", {}).get("build") != "next build":
        errors.append("fixture must expose npm run build")
    manifest_data = json.loads(manifest.read_text(encoding="utf-8"))
    preference_data = json.loads(preferences.read_text(encoding="utf-8"))
    errors.extend(f"website-manifest missing {key}" for key in sorted(REQUIRED_MANIFEST_KEYS - manifest_data.keys()))
    errors.extend(f"website-preferences missing {key}" for key in sorted(REQUIRED_PREFERENCE_KEYS - preference_data.keys()))
    if manifest_data.get("stack", {}).get("package_manager") != "npm":
        errors.append("fixture must use the locked npm workflow")
    if manifest_data.get("release", {}).get("status") != "local":
        errors.append("fixture must not imply an unverified external deployment")
    if manifest_data.get("qa", {}).get("visual_review") not in {"pending", "pass"}:
        errors.append("fixture must record a visual-review release gate")
    if not isinstance(manifest_data.get("experiment"), dict):
        errors.append("fixture must declare a bounded A/B experiment contract")

    source = "\n".join(path.read_text(encoding="utf-8") for path in (page, experiment_component, layout, css))
    errors.extend(f"forbidden client-side secret marker: {token}" for token in FORBIDDEN_PUBLIC_SECRETS if token in source)
    for required_copy in ("Confidence comes from specificity", "Demo interaction only", "Request a visit"):
        if required_copy not in source:
            errors.append(f"fixture is missing required content contract: {required_copy!r}")
    flag_source = (root / "lib" / "flags.ts").read_text(encoding="utf-8") if (root / "lib" / "flags.ts").is_file() else ""
    if 'data-experiment="primary_cta_label"' not in source or 'key: "primary_cta_label"' not in flag_source:
        errors.append("fixture must implement a server-evaluated, one-variable CTA experiment")
    for nondeterministic in ('"use client"', "Math.random", "localStorage"):
        if nondeterministic in experiment_component.read_text(encoding="utf-8"):
            errors.append(f"experiment assignment must not use client-side {nondeterministic}")
    if "FlagValues" not in page.read_text(encoding="utf-8"):
        errors.append("fixture must emit evaluated flag values for observability")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("fixtures/website/stellar-repair"))
    errors = verify(parser.parse_args().root)
    if errors:
        print("Website fixture validation failed:", file=sys.stderr)
        print("\n".join(f"- {error}" for error in errors), file=sys.stderr)
        return 1
    print("Website fixture validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
