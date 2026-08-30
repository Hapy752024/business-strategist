#!/usr/bin/env bash
# Bootstrap a multi-harness agentic project. Idempotent; refuses to overwrite non-empty files.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
if ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null)"; then
  :
elif [[ "$SCRIPT_DIR" == */.agents/skills/*/scripts ]]; then
  ROOT="${SCRIPT_DIR%%/.agents/skills/*}"
elif [[ "$SCRIPT_DIR" == */skills/*/scripts ]]; then
  ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd -P)"
else
  ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd -P)"
fi
cd "$ROOT"

dry_run=0
if [ "${1:-}" = "--dry-run" ]; then
  dry_run=1
fi

run() {
  if [ "$dry_run" -eq 1 ]; then
    printf 'DRY %s\n' "$*"
  else
    "$@"
  fi
}

write_if_missing() {
  local path="$1"
  local content="$2"
  if [ -s "$path" ]; then
    printf 'KEEP %s already exists and is non-empty\n' "$path"
    return
  fi
  if [ "$dry_run" -eq 1 ]; then
    printf 'DRY write %s\n' "$path"
  else
    mkdir -p "$(dirname "$path")"
    printf '%s\n' "$content" > "$path"
    printf 'WROTE %s\n' "$path"
  fi
}

project_name="$(basename "$ROOT")"

run mkdir -p .agents/skills .claude .codex scripts

write_if_missing "AGENTS.md" "# AGENTS.md - Shared Project Instructions

Canonical context for Claude Code, Codex CLI, OpenCode, Gemini CLI, and compatible harnesses. Keep this file short and stable (under 250 lines); load referenced docs only when needed.

Tool-specific files:
- Claude Code: \`CLAUDE.md\`, \`.claude/settings.json\`, \`.claude/agents/\`, \`.claude/rules/\`
- Codex CLI: \`.codex/config.toml\`
- OpenCode: \`opencode.json\`
- Gemini CLI: \`.gemini/settings.json\`

Do not commit generated memory blocks, session transcripts, or secrets here.

## Project

${project_name} project. Replace this section with 2-5 sentences on what the product is, plus a Stack block listing frontend, backend, database, auth, deployment, and package managers.

## Setup

Frontend:

\`\`\`bash
cd frontend && npm install && npm run dev
\`\`\`

Backend:

\`\`\`bash
cd backend && uv venv && source .venv/bin/activate && uv pip install -e '.[dev]' && uvicorn app.main:app --reload
\`\`\`

Tests:

\`\`\`bash
npm test
cd backend && uv run pytest
\`\`\`

## Core Rules

- Branches: \`feature/[ticket-id]-description\` or \`fix/[ticket-id]-description\`
- Commits: Conventional commits (\`feat:\`, \`fix:\`, \`chore:\`)
- Coverage: maintain over 80%
- No emojis in code; Markdown docs and commit messages are okay
- Do not commit secrets. Use environment variables in MCP and app config
- Use WSL toolchains consistently; do not mix Windows and WSL toolchains
- Put repeated procedures in \`.agents/skills\` instead of this file
- Never edit existing Alembic migrations; create new migrations

## Context Loading

Load details only when relevant:
- Architecture decisions: \`ARCHITECTURE-DECISIONS.md\`
- Frontend specifics: \`frontend/AGENTS.md\` (or \`apps/frontend/AGENTS.md\`)
- Backend specifics: \`backend/AGENTS.md\` (or \`apps/backend/AGENTS.md\`)
- Skill details: \`.agents/skills/*/SKILL.md\`, then targeted \`references/\` files

## Skills

Use skills to avoid repeating large procedures. List only skills this project actually uses, written in user-language trigger form:
- \`setup-multiharness-project\`: repair or re-bootstrap agent wiring
- (add project skills here as they are created)

## Review Loops

Spawn review subagents at two gates:
- **Pre-implementation** — \`plan-reviewer\` subagent: architecture fit, security surface, data flow.
- **Post-implementation** — \`ui-reviewer\` subagent (when UI changed): Playwright screenshots at 375/768/1280, visual breakage assessment.

## Subagents

Use subagents to preserve main-context budget whenever work is broad, review-heavy, or parallelizable. Project subagents live in \`.claude/agents/\`. Keep subagent prompts narrow: ask for file paths, concise findings, risks, and recommended edits, not narratives.

## MCP And Harnesses

\`.mcp.json\` is the canonical MCP source. After editing it:

\`\`\`bash
python3 scripts/sync-mcp-config.py
python3 scripts/install-codex-profile.py
\`\`\`

Start from WSL repo root:

\`\`\`bash
claude --mcp-config .mcp.json
codex -p ${project_name}
opencode .
\`\`\`

## Code Graph

If \`code-review-graph\` MCP is available, use it before broad grep/glob/read exploration: \`get_minimal_context\`, \`semantic_search_nodes\`, \`query_graph\`, \`get_impact_radius\`, \`detect_changes\`, \`get_review_context\`. Fallback to file search only when the graph does not cover the task."

write_if_missing "CLAUDE.md" "# CLAUDE.md - Claude Code Instructions

Read \`AGENTS.md\` first. It is the canonical shared project context.

This file only contains Claude Code-specific guidance.

## Runtime

Start from the WSL repo root:

\`\`\`bash
claude --mcp-config .mcp.json
\`\`\`

Claude-specific settings live in \`.claude/settings.json\`, \`.claude/rules/\`, and \`.claude/agents/\`.

Do not paste generated memory blocks into \`AGENTS.md\` or \`CLAUDE.md\`."

write_if_missing ".mcp.json" '{
  "mcpServers": {}
}'

# Copy the sync-mcp-config.py template into the project (idempotent)
if [ -s scripts/sync-mcp-config.py ]; then
  printf 'KEEP scripts/sync-mcp-config.py already exists and is non-empty\n'
else
  if [ "$dry_run" -eq 1 ]; then
    printf 'DRY copy scripts/sync-mcp-config.py from template\n'
  else
    mkdir -p scripts
    cp "$SCRIPT_DIR/templates/sync-mcp-config.py" scripts/sync-mcp-config.py
    chmod +x scripts/sync-mcp-config.py
    printf 'WROTE scripts/sync-mcp-config.py\n'
  fi
fi

# .claude/skills symlink
if [ -e .claude/skills ] && [ ! -L .claude/skills ]; then
  printf 'ERROR .claude/skills exists and is not a symlink; move it manually before bootstrapping\n'
  exit 1
fi

if [ ! -L .claude/skills ] || [ "$(readlink .claude/skills 2>/dev/null || true)" != "../.agents/skills" ]; then
  run rm -f .claude/skills
  run ln -s ../.agents/skills .claude/skills
else
  printf 'OK .claude/skills already links to ../.agents/skills\n'
fi

# .gitignore hygiene
write_if_missing ".gitignore" "# Env / secrets
.env
.env.*
*.local.json

# Python
__pycache__/
*.pyc
.venv/

# Node
node_modules/

# Local state
*.sqlite

# Harness artifacts
.claude/plans/
.codex/artifacts/
"

# Initial MCP sync if the script is now present
if [ "$dry_run" -eq 0 ] && [ -f scripts/sync-mcp-config.py ]; then
  if python3 scripts/sync-mcp-config.py 2>/dev/null; then
    :
  else
    printf 'NOTE scripts/sync-mcp-config.py ran but produced no servers (empty .mcp.json is fine)\n'
  fi
else
  printf 'NOTE run scripts/sync-mcp-config.py after adding MCP servers\n'
fi

printf 'Bootstrap complete%s.\n' "$([ "$dry_run" -eq 1 ] && printf ' dry run' || true)"
printf 'Next: edit AGENTS.md to fill in Project, Setup, Core Rules, and Skills for your stack.\n'
