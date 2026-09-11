# Deferred maintenance

- [x] Fix the `PreCompact` hook so it resolves from the business-strategist
  repository root instead of Claude's current working directory. The current
  relative command in `.claude/settings.json` fails for nested sessions such as
  `projects/us-retirees-italy/web-site` because it looks for
  `website/.claude/hooks/precompact.py` rather than the repository hook. Fixed
  2026-09-05 by anchoring all lifecycle hooks to `$CLAUDE_PROJECT_DIR`.
  Preserve the existing manifest/plan-saving behavior. Verify it from both the
  repository root and a nested brand-project directory before enabling it.
