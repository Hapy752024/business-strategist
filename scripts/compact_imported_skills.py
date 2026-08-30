#!/usr/bin/env python3
"""Move imported brand skill procedures behind compact entry files."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ("brand-asset-producer", "brand-designer", "brand-discovery-interviewer", "brand-exporter", "brand-frontend-app-designer", "brand-guideline-researcher", "brand-guidelines-writer", "brand-motion-designer", "brand-quality-reviewer", "brand-strategy-director", "brand-typography-researcher", "brand-ui-component-producer", "brand-ui-kit-producer", "brand-workspace-manager", "setup-multiharness-project")


def split_frontmatter(text: str) -> tuple[str, str]:
    if not text.startswith("---\n"):
        raise ValueError("missing frontmatter")
    boundary = text.find("\n---\n", 4)
    if boundary < 0:
        raise ValueError("unterminated frontmatter")
    return text[: boundary + 5], text[boundary + 5 :].lstrip()


def compact(name: str) -> None:
    directory = ROOT / ".agents" / "skills" / name
    entry = directory / "SKILL.md"
    frontmatter, body = split_frontmatter(entry.read_text(encoding="utf-8"))
    workflow = directory / "references" / "workflow.md"
    workflow.parent.mkdir(parents=True, exist_ok=True)
    if not workflow.exists():
        workflow.write_text(
            "# Imported workflow\n\n## Procedure\n\n" + body + "\n\n## Output\n\nFollow the output contract described by this skill and preserve provenance.\n\n## Quality Checklist\n\nRun the skill's existing checks and do not claim completion with unresolved blockers.\n",
            encoding="utf-8",
        )
    title = name.replace("-", " ").title()
    entry.write_text(
        frontmatter
        + f"\n# {title}\n\nRead `references/workflow.md` for the complete procedure. Load only the additional references needed for the requested stage.\n\n## Procedure\n\nUse the imported workflow and keep state in the active manifest.\n\n## Output\n\nReturn the requested artifacts, provenance, unresolved gaps, and next action.\n\n## Quality Checklist\n\nRun the relevant validators before delivery; never promote unapproved artifacts.\n",
        encoding="utf-8",
    )


def main() -> int:
    for skill in SKILLS:
        compact(skill)
    print(f"compacted {len(SKILLS)} imported skill entries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
