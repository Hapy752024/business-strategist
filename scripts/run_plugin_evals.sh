#!/usr/bin/env bash
# Skill-trigger evals via `claude plugin eval`. Spends model tokens; run on demand.
# Extra args pass through (e.g. --case 'no-skill-*' --runs 1). --ablation none: score trigger
# rate directly instead of a with/without-plugin comparison (halves cost).
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
mkdir -p evals/live-results
exec claude plugin eval . --eval-dir evals/plugin-triggers --threshold 0.8 \
  --trust-plugin --ablation none --concurrency 4 --no-publish \
  --json "evals/live-results/$(date +%F)-plugin-triggers.json" \
  --output-dir "${EVAL_OUTPUT_DIR:-${TMPDIR:-/tmp}/plugin-triggers-results}" "$@"
