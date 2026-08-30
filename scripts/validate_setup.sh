#!/usr/bin/env bash
# Validate project infrastructure — not skill content.
# Run: bash scripts/validate_setup.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

errors=0
warnings=0

red()   { printf '\033[31m%s\033[0m\n' "$*"; }
green() { printf '\033[32m%s\033[0m\n' "$*"; }
yellow(){ printf '\033[33m%s\033[0m\n' "$*"; }

check() {
    local msg="$1"; shift
    if "$@"; then
        green "  PASS  $msg"
    else
        red "  FAIL  $msg"
        ((errors += 1))
    fi
}

warn() {
    yellow "  WARN  $1"
    ((warnings += 1))
}

echo "=== Validate Setup: $(date) ==="
echo ""

# ── .gitignore ────────────────────────────────────────────
echo "--- .gitignore ---"
check ".gitignore exists" test -f .gitignore

required_patterns=("__pycache__" "*.pyc" ".venv" "node_modules" ".env" "*.sqlite" "*.local.json" ".claude/plans" ".codex/artifacts" ".firecrawl/")
for pat in "${required_patterns[@]}"; do
    check ".gitignore covers '$pat'" grep -qF "$pat" .gitignore
done

# ── .env.example ──────────────────────────────────────────
echo ""
echo "--- .env.example ---"
check ".env.example exists" test -f .env.example

# Extract ${VAR} references from .mcp.json and check .env.example covers them
if [ -f .mcp.json ]; then
    while IFS= read -r var; do
        check ".env.example covers $var" grep -qF "${var}" .env.example
    done < <(grep -oP '\$\{[A-Z_]+\}' .mcp.json | sed 's/[${}]//g' | sort -u)
fi

# ── Git functional ─────────────────────────────────────────
echo ""
echo "--- Git ---"
if [ -d .git ] && [ -f .git/HEAD ]; then
    green "  PASS  Git is functional"
else
    red "  FAIL  Git is not functional — version control is required for this project"
    ((errors += 1))
fi

# ── Committed junk ────────────────────────────────────────
echo ""
echo "--- Committed junk ---"
if [ -d .git ] && [ -f .git/HEAD ]; then
    for pattern in "__pycache__" "*.pyc" "*.sqlite" "*.local.json"; do
        files=$(git ls-files "$pattern" 2>/dev/null) || true
        if [ -n "$files" ]; then
            red "  FAIL  Committed junk: $pattern — $files"
            ((errors += 1))
        else
            green "  PASS  No committed junk matching '$pattern'"
        fi
    done
else
    red "  FAIL  Git not functional — cannot check committed junk"
    ((errors += 1))
fi

# ── Settings files ────────────────────────────────────────
echo ""
echo "--- Settings ---"
check ".claude/settings.json exists" test -f .claude/settings.json
check ".claude/settings.local.json exists" test -f .claude/settings.local.json
check ".claude/settings.json is valid JSON" python3 -c "import json; json.load(open('.claude/settings.json'))"
check "AGENTS.md excludes generated memory blocks" sh -c "! grep -q '<claude-mem-context>' AGENTS.md"

# ── Dependency declarations ───────────────────────────────
echo ""
echo "--- Dependencies ---"
check "requirements.txt exists" test -f requirements.txt

# ── Source capability catalog ─────────────────────────────
echo ""
echo "--- Source Capabilities ---"
check "config/source-capabilities.json exists" test -f config/source-capabilities.json
check "source capability catalog is valid" python3 scripts/capability_lookup.py --validate
check "source capability lookup runs" python3 scripts/capability_lookup.py --question "customer pain evidence" --max 2 --compact

# ── Registries ────────────────────────────────────────────
echo ""
echo "--- Registries ---"
check "registry files are valid and consistent" python3 scripts/validate_registries.py

# ── Skills ────────────────────────────────────────────────
echo ""
echo "--- Skills ---"
# .claude/skills must be a symlink to ../.agents/skills (single source of truth).
# A real directory here means a Windows-side checkout materialized the link as
# copies; that silently drifts from .agents/skills.
if [ -L .claude/skills ]; then
    green "  PASS  .claude/skills is a symlink"
elif [ -d .claude/skills ]; then
    red "  FAIL  .claude/skills is a real directory, not a symlink to ../.agents/skills (drift risk). Restore with: rm -rf .claude/skills && ln -s ../.agents/skills .claude/skills"
    ((errors += 1))
else
    red "  FAIL  .claude/skills is missing"
    ((errors += 1))
fi
if [ -d .agents/skills ]; then
    skill_count=$(find .agents/skills -name "SKILL.md" | wc -l)
    echo "  INFO  Found $skill_count skill(s)"
    while IFS= read -r skill_file; do
        skill_name=$(basename "$(dirname "$skill_file")")
        # Check frontmatter
        if head -1 "$skill_file" | grep -q '^---$'; then
            green "  PASS  $skill_name has frontmatter"
        else
            red "  FAIL  $skill_name missing YAML frontmatter"
            ((errors += 1))
        fi
        line_count=$(wc -l < "$skill_file")
        if [ "$line_count" -le 30 ]; then
            green "  PASS  $skill_name entry is within 30-line budget"
        else
            red "  FAIL  $skill_name entry exceeds 30-line budget ($line_count)"
            ((errors += 1))
        fi
        workflow_file="$(dirname "$skill_file")/references/workflow.md"
        if grep -q 'references/workflow.md' "$skill_file"; then
            check "$skill_name progressive-disclosure workflow exists" test -f "$workflow_file"
        fi
        # Detailed procedure and quality checks may live in the referenced workflow.
        for section in "Procedure" "Output" "Quality Checklist"; do
            if grep -q "^## $section" "$skill_file" "$workflow_file" 2>/dev/null; then
                green "  PASS  $skill_name has '$section' guidance"
            elif [ "$section" = "Procedure" ] && grep -q "^## Workflow" "$skill_file" "$workflow_file" 2>/dev/null; then
                green "  PASS  $skill_name uses 'Workflow' as procedure guidance"
            else
                warn "$skill_name missing '$section' guidance"
            fi
        done
    done < <(find .agents/skills -name "SKILL.md")
else
    red "  FAIL  .agents/skills directory not found"
    ((errors += 1))
fi

# ── Symlinks ──────────────────────────────────────────────
echo ""
echo "--- Symlinks ---"
check ".claude/skills -> .agents/skills" test -L .claude/skills

# ── Agent modes ───────────────────────────────────────────
echo ""
echo "--- Agent Modes ---"
for mode in research source-audit coding; do
    check "agent-modes/$mode.md exists" test -f "agent-modes/$mode.md"
done

echo ""
echo "--- Workspace Tests ---"
check "topic workspace and Firecrawl routing tests pass" python3 scripts/evidence_scout/test_workspace.py
check "market-problem discovery tests pass" python3 scripts/evidence_scout/test_market_discovery.py
check "archetype GTM skill tests pass" python3 scripts/evidence_scout/test_gtm_skill.py
check "service customer-perspective skill tests pass" python3 scripts/evidence_scout/test_customer_perspective_skill.py
check "interview-bridge kit tests pass" python3 scripts/evidence_scout/test_interview_bridge.py
check "whitespace matrix tests pass" python3 scripts/evidence_scout/test_whitespace_matrix.py
check "imported brand skill tests pass" python3 -m pytest -q tests/brand_designer --disable-warnings
check "business-brand-website foundation tests pass" python3 -m pytest -q tests/integration --disable-warnings
check "eval structure is valid" python3 scripts/run_evals.py

# ── Schemas ───────────────────────────────────────────────
echo ""
echo "--- Schemas ---"
for schema in evidence-record ads-record competitor stage-checkpoint research-topic-manifest project-manifest business-to-brand brand-manifest website-preferences website-manifest claim-record; do
    check "schemas/$schema.schema.json exists" test -f "schemas/$schema.schema.json"
    check "schemas/$schema.schema.json is valid JSON" python3 -c "import json; json.load(open('schemas/$schema.schema.json'))" 2>/dev/null
done
check "skill catalog is valid JSON" python3 -c "import json; json.load(open('config/skill-catalog.json'))" 2>/dev/null
check "workflow routes are valid JSON" python3 -c "import json; json.load(open('config/workflow-routes.json'))" 2>/dev/null
check "website route smoke test passes" python3 -c "import subprocess,sys; out=subprocess.check_output(['python3','scripts/route_workflow.py','Build a distinctive Next.js landing page'], text=True); sys.exit(0 if 'brand-website-designer-builder' in out else 1)"

# ── Summary ───────────────────────────────────────────────
echo ""
echo "=================================="
if [ "$errors" -eq 0 ] && [ "$warnings" -eq 0 ]; then
    green "All checks passed."
elif [ "$errors" -eq 0 ]; then
    yellow "$warnings warning(s), 0 errors — acceptable."
else
    red "$errors error(s), $warnings warning(s) — fix errors before proceeding."
fi
exit "$errors"
