---
name: setup-multiharness-project
description: Set up or repair a multi-harness agent project with shared skills, thin shims, MCP config, and safe symlinks. Use when starting a project or repairing agent wiring drift.
---

# Setup Multiharness Project

Read `references/workflow.md` for the complete procedure. Load only the additional references needed for the requested stage.

## Procedure

Bootstrap only minimal instructions by default. Use `--harness` and `--mcp` only for requested integrations. Audit/dry-run never execute target code; refuse unsafe destination links before any writes. Use the bundled implementation described in the workflow.

## Output

Return the requested artifacts, provenance, unresolved gaps, and next action.

## Quality Checklist

Run the relevant validators before delivery; never promote unapproved artifacts.
