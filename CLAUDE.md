@AGENTS.md

# Claude Code Harness Notes

- Primary shell: bash
- Scripts are under `scripts/` — prefer running them directly over MCP equivalents where both exist.
- Skills live in `.claude/skills/` (symlinked to `.agents/skills/`).
- MCP servers configured in this project for web research: brave-search and firecrawl. Check `.mcp.json` for the current authoritative list.
