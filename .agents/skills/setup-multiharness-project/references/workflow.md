# Setup Multi-Harness Project Workflow

Use this reference only when the shell scripts fail or the user asks for the rationale.

## What This Skill Does

One skill, two modes, auto-detected:

- **Bootstrap** (greenfield): create `AGENTS.md`, `CLAUDE.md`, `.mcp.json`, `.agents/skills/`, `.claude/skills` symlink, `.codex/`, `opencode.json`, and a `scripts/sync-mcp-config.py` stub.
- **Optimize** (existing): audit line budgets, symlink health, generated memory blocks, MCP config drift, and AGENTS.md section structure; apply safe repairs without overwriting user content.

## Multi-Harness Layout

The canonical, harness-neutral layout this skill produces:

```
<repo>/
  AGENTS.md                     # canonical context, 150-250 lines
  CLAUDE.md                     # thin: @AGENTS.md + Claude-specific notes
  .mcp.json                     # canonical MCP server list
  .agents/
    skills/<name>/SKILL.md      # canonical skills (harness-neutral)
  .claude/
    settings.json               # Claude permissions + hooks
    agents/<name>.md            # Claude-specific subagent wrappers
    rules/                      # Claude path-scoped rules
    skills -> ../.agents/skills # relative symlink
  .codex/
    config.toml                 # Codex CLI profile config (generated)
  opencode.json                 # OpenCode config (generated)
  .gemini/
    settings.json               # Gemini CLI (generated/linked)
  scripts/
    sync-mcp-config.py          # regenerates .codex/config.toml + opencode.json from .mcp.json
    install-codex-profile.py    # installs the codex profile for `codex -p <project>`
```

## Why One Skill Instead Of Two

The bootstrap and optimize modes share the same layout, the same root-detection, the same dry-run pattern, and the same guardrails. Splitting them forces the user to know which to call. Auto-detection (no `AGENTS.md` → bootstrap, `AGENTS.md` present → optimize) removes that decision. Forced modes are still available for CI and re-runs.

## Bootstrap Defaults

- Create `AGENTS.md` with the 10-section structure: Header & harness file map, Project, Setup, Core Rules, Context Loading, Skills, Review Loops, Subagents, MCP And Harnesses, Code Graph (optional).
- Create `CLAUDE.md` as a thin shim: `Read AGENTS.md first.` plus Claude-specific runtime notes.
- Create `.mcp.json` with an empty `mcpServers` block.
- Create `.agents/skills/` and symlink `.claude/skills` to `../.agents/skills`.
- Create `scripts/sync-mcp-config.py` stub that regenerates `.codex/config.toml` and `opencode.json` from `.mcp.json` (so adding MCP servers later is one command).
- Refuse to overwrite any non-empty instruction file.

## Optimize Defaults

- Audit:
  - `AGENTS.md` and `CLAUDE.md` exist and are under 250 lines.
  - `.claude/skills` is a relative symlink to `../.agents/skills`.
  - `AGENTS.md` has no generated `<claude-mem-context>` block.
  - `.codex/config.toml` and `opencode.json` match what `sync-mcp-config.py` would produce from `.mcp.json`.
  - `AGENTS.md` contains the required section markers (## Project, ## Setup, ## Core Rules, ## Context Loading, ## Skills).
- Apply safe repairs only:
  - Restore the `.claude/skills` symlink if missing or wrong.
  - Strip `<claude-mem-context>` blocks from `AGENTS.md`.
  - Re-run `scripts/sync-mcp-config.py` to regenerate harness configs.
- Never overwrite user-written content in `AGENTS.md` or `CLAUDE.md`.
- Manual judgment: if `AGENTS.md` is still too long after safe repairs, move procedures into skills or `references/` files. Keep only stable project facts, commands, conventions, and pointers in always-loaded docs.

## Commands

```bash
# auto-detect
bash .agents/skills/setup-multiharness-project/scripts/setup.sh --dry-run
bash .agents/skills/setup-multiharness-project/scripts/setup.sh

# force modes
bash .agents/skills/setup-multiharness-project/scripts/setup.sh bootstrap
bash .agents/skills/setup-multiharness-project/scripts/setup.sh optimize
bash .agents/skills/setup-multiharness-project/scripts/setup.sh audit
```

## What Belongs Where

- **Always-loaded docs (`AGENTS.md`, `CLAUDE.md`):** stable facts, commands, conventions, and pointers. Under 250 lines.
- **Skills (`.agents/skills/<name>/SKILL.md`):** repeatable procedures, checklists, detailed workflows, and helper scripts.
- **References (`<skill>/references/*.md`):** long-form detail loaded only when the skill body points to them.
- **Scripts (`<skill>/scripts/*` and `scripts/*`):** deterministic retrieval, validation, syncing, and reporting.
- **Claude rules/agents (`.claude/rules/`, `.claude/agents/`):** Claude-only behavior, path-scoped rules, and specialist subagents. Never duplicate skill bodies here.
- **Harness configs (`.codex/config.toml`, `opencode.json`):** generated from `.mcp.json`; never hand-edited.

## Launching Each Harness

From the WSL repo root after setup:

```bash
claude --mcp-config .mcp.json
codex -p <project-name>
opencode .
```

Do not mix Windows and WSL toolchains in one session.

## When The Scripts Fail

The scripts are designed to be re-runnable and idempotent. If one fails:

1. Read the FAIL line — it names the file or check that failed.
2. If root detection is wrong, set `ROOT` explicitly: `ROOT=/path/to/repo bash .../setup.sh`.
3. If a generated config is out of sync, run `python3 scripts/sync-mcp-config.py` manually and re-audit.
4. If `AGENTS.md` is over the line budget, move procedures to skills or `references/` rather than trimming facts.
