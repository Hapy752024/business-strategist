#!/usr/bin/env bash
# setup-multiharness-project dispatcher: auto-detects bootstrap vs optimize.
# Usage:
#   setup.sh [--dry-run]          # auto-detect: bootstrap if no AGENTS.md, else optimize
#   setup.sh bootstrap [--dry-run]
#   setup.sh optimize [--dry-run]
#   setup.sh audit
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

mode=""
dry_run=0
for arg in "$@"; do
  case "$arg" in
    --dry-run) dry_run=1 ;;
    bootstrap|optimize|audit) mode="$arg" ;;
    *) printf 'unknown arg: %s\n' "$arg" >&2; exit 2 ;;
  esac
done

if [ -z "$mode" ]; then
  if [ -s AGENTS.md ]; then
    mode=optimize
  else
    mode=bootstrap
  fi
  printf 'AUTO mode=%s (detected from AGENTS.md presence)\n' "$mode"
fi

case "$mode" in
  bootstrap)
    if [ "$dry_run" -eq 1 ]; then
      bash "$SCRIPT_DIR/bootstrap.sh" --dry-run
    else
      bash "$SCRIPT_DIR/bootstrap.sh"
    fi
    ;;
  optimize)
    if [ "$dry_run" -eq 1 ]; then
      bash "$SCRIPT_DIR/audit.sh"
      printf '\n--- proposed repairs (dry run) ---\n'
      bash "$SCRIPT_DIR/apply.sh" --dry-run
    else
      bash "$SCRIPT_DIR/audit.sh" || true
      bash "$SCRIPT_DIR/apply.sh"
      printf '\n--- re-audit after apply ---\n'
      bash "$SCRIPT_DIR/audit.sh"
    fi
    ;;
  audit)
    bash "$SCRIPT_DIR/audit.sh"
    ;;
esac
