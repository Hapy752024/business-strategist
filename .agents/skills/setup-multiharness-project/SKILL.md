---
name: setup-multiharness-project
description: Set up or repair a multi-harness agentic project (Claude Code, Codex CLI, OpenCode, Gemini CLI) with AGENTS.md, thin per-harness shims, shared skills, MCP config, and WSL-safe symlinks. Auto-detects new vs existing and runs bootstrap or optimize accordingly. Use when starting a new project, adding agent wiring to an existing repo, or repairing config drift.
user_invocable: true
---

# Setup Multiharness Project

Read `references/workflow.md` for the complete procedure. Load only the additional references needed for the requested stage.

## Procedure

Use the imported workflow and keep state in the active manifest.

## Output

Return the requested artifacts, provenance, unresolved gaps, and next action.

## Quality Checklist

Run the relevant validators before delivery; never promote unapproved artifacts.
