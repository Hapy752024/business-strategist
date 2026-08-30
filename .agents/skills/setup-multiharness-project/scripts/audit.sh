#!/usr/bin/env bash
# Audit a multi-harness agentic project for drift. Read-only.
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

failures=0
warnings=0

fail() { printf 'FAIL %s\n' "$1"; failures=$((failures + 1)); }
pass() { printf 'PASS %s\n' "$1"; }
warn() { printf 'WARN %s\n' "$1"; warnings=$((warnings + 1)); }

printf 'Agentic setup audit: %s\n' "$ROOT"

# 1. Required files and line budgets
for file in AGENTS.md CLAUDE.md; do
  if [ ! -f "$file" ]; then
    fail "$file missing"
    continue
  fi
  lines="$(wc -l < "$file" | tr -d ' ')"
  if [ "$lines" -gt 250 ]; then
    fail "$file has $lines lines; limit is 250"
  else
    pass "$file has $lines lines"
  fi
done

# 2. AGENTS.md required sections
if [ -f AGENTS.md ]; then
  for section in "## Project" "## Setup" "## Core Rules" "## Context Loading" "## Skills"; do
    if grep -q "^$section" AGENTS.md; then
      pass "AGENTS.md has $section"
    else
      fail "AGENTS.md missing $section"
    fi
  done
fi

# 3. CLAUDE.md should point at AGENTS.md (not duplicate it)
if [ -f CLAUDE.md ]; then
  if grep -qi "AGENTS.md" CLAUDE.md; then
    pass "CLAUDE.md references AGENTS.md"
  else
    fail "CLAUDE.md does not reference AGENTS.md (should be a thin shim)"
  fi
fi

# 4. Skill symlink
if [ -L .claude/skills ]; then
  target="$(readlink .claude/skills)"
  if [ "$target" = "../.agents/skills" ]; then
    pass ".claude/skills -> ../.agents/skills"
  else
    fail ".claude/skills -> $target, expected ../.agents/skills"
  fi
elif [ -e .claude/skills ]; then
  fail ".claude/skills exists but is not a symlink"
else
  fail ".claude/skills symlink missing"
fi

# 5. Generated memory block
if grep -q '<claude-mem-context>' AGENTS.md 2>/dev/null; then
  fail "AGENTS.md contains generated <claude-mem-context> block"
else
  pass "AGENTS.md has no generated memory block"
fi

# 6. MCP config drift (if sync script exists)
if [ -f scripts/sync-mcp-config.py ]; then
  python3 - <<'PY' || failures=$((failures + 1))
import json
import pathlib
import sys

root = pathlib.Path.cwd()
sync = root / "scripts" / "sync-mcp-config.py"
ns = {"__file__": str(sync)}
exec(sync.read_text(), ns)

servers = json.loads((root / ".mcp.json").read_text()).get("mcpServers", {})
gen_codex = ns.get("generate_codex")
gen_opencode = ns.get("generate_opencode")
if not gen_codex or not gen_opencode:
    print("FAIL scripts/sync-mcp-config.py does not define generate_codex/generate_opencode")
    sys.exit(1)

expected = {
    root / ".codex" / "config.toml": gen_codex(servers),
    root / "opencode.json": gen_opencode(servers),
}
bad = False
for path, content in expected.items():
    rel = path.relative_to(root)
    if not path.exists():
        print(f"FAIL {rel} missing (run scripts/sync-mcp-config.py)")
        bad = True
    elif path.read_text() != content:
        print(f"FAIL {rel} is out of sync with .mcp.json")
        bad = True
    else:
        print(f"PASS {rel} matches .mcp.json")
sys.exit(1 if bad else 0)
PY
else
  warn "scripts/sync-mcp-config.py missing; skipping MCP drift check"
fi

# 7. .mcp.json exists and is valid JSON
if [ -f .mcp.json ]; then
  if python3 -c "import json,sys; json.load(open('.mcp.json'))" 2>/dev/null; then
    pass ".mcp.json is valid JSON"
  else
    fail ".mcp.json is not valid JSON"
  fi
else
  fail ".mcp.json missing"
fi

# 8. Harness config files
for cfg in .codex/config.toml opencode.json; do
  if [ -f "$cfg" ]; then
    pass "$cfg exists"
  else
    warn "$cfg missing (run scripts/sync-mcp-config.py)"
  fi
done

# 9. .gitignore hygiene
if [ -f .gitignore ]; then
  for pattern in ".env" "__pycache__/" "node_modules/" ".codex/artifacts/"; do
    if grep -qF "$pattern" .gitignore; then
      pass ".gitignore covers $pattern"
    else
      warn ".gitignore missing pattern: $pattern"
    fi
  done
else
  fail ".gitignore missing"
fi

# 10. This skill's own SKILL.md budget
self_skill=".agents/skills/setup-multiharness-project/SKILL.md"
if [ -f "$self_skill" ]; then
  lines="$(wc -l < "$self_skill" | tr -d ' ')"
  if [ "$lines" -gt 35 ]; then
    fail "$self_skill has $lines lines; limit is 35"
  else
    pass "$self_skill has $lines lines"
  fi
fi

printf '\nAudit: %s failure(s), %s warning(s).\n' "$failures" "$warnings"
if [ "$failures" -gt 0 ]; then
  exit 1
fi
exit 0
