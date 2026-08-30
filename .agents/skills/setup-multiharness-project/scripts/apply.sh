#!/usr/bin/env bash
# Apply safe repairs to a multi-harness agentic project. Idempotent.
# Does NOT overwrite user-written content in AGENTS.md or CLAUDE.md.
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

note() { printf '%s\n' "$1"; }

note "Applying safe repairs in $ROOT"

# 1. Restore .claude/skills symlink
if [ -e .claude/skills ] && [ ! -L .claude/skills ]; then
  note "ERROR .claude/skills exists and is not a symlink; move it manually before applying"
  exit 1
fi

if [ ! -L .claude/skills ] || [ "$(readlink .claude/skills 2>/dev/null || true)" != "../.agents/skills" ]; then
  run mkdir -p .claude .agents/skills
  run rm -f .claude/skills
  run ln -s ../.agents/skills .claude/skills
else
  note "OK .claude/skills already links to ../.agents/skills"
fi

# 2. Strip generated <claude-mem-context> blocks from AGENTS.md
if grep -q '<claude-mem-context>' AGENTS.md 2>/dev/null; then
  if [ "$dry_run" -eq 1 ]; then
    note "DRY remove <claude-mem-context> block from AGENTS.md"
  else
    python3 - <<'PY'
from pathlib import Path

path = Path("AGENTS.md")
text = path.read_text()
start = text.find("\n<claude-mem-context>")
if start == -1:
    start = text.find("<claude-mem-context>")
end = text.find("</claude-mem-context>", start)
if start != -1 and end != -1:
    end += len("</claude-mem-context>")
    new_text = text[:start].rstrip() + "\n" + text[end:].lstrip()
    path.write_text(new_text)
    print("WROTE AGENTS.md (stripped <claude-mem-context>)")
PY
  fi
else
  note "OK AGENTS.md has no generated memory block"
fi

# 3. Regenerate MCP-derived configs
if [ -f scripts/sync-mcp-config.py ]; then
  run python3 scripts/sync-mcp-config.py
else
  note "WARN scripts/sync-mcp-config.py missing; skipped MCP config regeneration"
fi

# 4. Ensure .gitignore has minimum patterns (append-only, never remove user patterns)
if [ -f .gitignore ]; then
  if [ "$dry_run" -eq 0 ]; then
    python3 - <<'PY'
from pathlib import Path

path = Path(".gitignore")
text = path.read_text() if path.exists() else ""
required = [".env", "__pycache__/", "node_modules/", ".codex/artifacts/"]
missing = [p for p in required if p not in text]
if missing:
    addition = "\n# auto-added by setup-multiharness-project\n" + "\n".join(missing) + "\n"
    path.write_text(text.rstrip() + "\n" + addition)
    print(f"WROTE .gitignore (added {len(missing)} pattern(s))")
else:
    print("OK .gitignore covers required patterns")
PY
  else
    note "DRY check .gitignore required patterns"
  fi
else
  if [ "$dry_run" -eq 1 ]; then
    note "DRY write .gitignore with required patterns"
  else
    printf '# Env / secrets\n.env\n.env.*\n*.local.json\n\n# Python\n__pycache__/\n*.pyc\n.venv/\n\n# Node\nnode_modules/\n\n# Local state\n*.sqlite\n\n# Harness artifacts\n.claude/plans/\n.codex/artifacts/\n' > .gitignore
    note "WROTE .gitignore"
  fi
fi

if [ "$dry_run" -eq 1 ]; then
  note "Dry run complete."
else
  note "Apply complete. Re-run audit to confirm."
fi
