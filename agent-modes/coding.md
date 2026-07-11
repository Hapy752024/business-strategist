# Coding Mode

Editing scripts, skills, configuration, and project infrastructure.

## Allowed Tools

- Edit, Write, Bash (standard), Python3
- MCP: filesystem

## Required Output Checks

- Scripts must run without syntax errors (`python3 -m py_compile`).
- Changes to shared scripts (e.g., `scripts/validate_apis/common.py`) must be tested against all importers.
- Skill changes must preserve frontmatter (name, description) and required sections.

## Stop Conditions

- Do not edit `settings.json` or `settings.local.json` without explicit user approval.
- Do not delete files without user confirmation.
- Do not commit secrets or credentials.

## Forbidden

- `rm -rf`, `git reset --hard`, `git push --force`
- Writing to `~/.secrets`, `.env`, or any credential file
- Editing harness config during a research run
