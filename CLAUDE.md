@AGENTS.md

# Claude Code Harness Notes

- Primary shell: bash
- Scripts are under `scripts/` — prefer running them directly over MCP equivalents where both exist.
- Use `python3 scripts/capability_lookup.py --question "<research need>" --compact` before substantial research, enrichment, document ingestion, China coverage, app-store work, or paid fallback routing.
- Runtime provider truth comes from `python3 scripts/validate_apis/run_all.py`; `provider_doctor.py` routes source families after live validation and should not be treated as evidence that a provider produced usable records.
- Topic workspaces live under `research/topics/<topic-slug>/`; `manifest.json` is the active state.
- **Before any research workflow, check for existing workspaces:** `ls -d research/topics/*/manifest.json 2>/dev/null`. Present existing workspaces as numbered options and ask whether to continue or start new. See `references/workspace-lifecycle.md`.
- Firecrawl CLI/API calls must use `FIRECRAWL_API_KEY_HGINVESTOR`.
- Skills live in `.claude/skills/` (symlinked to `.agents/skills/`).
- MCP servers for web research: brave-search, firecrawl. Local storage: filesystem, sqlite.
