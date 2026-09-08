# Setup and repair workflow

Use the existing entry scripts. They dispatch to trusted bundled `scripts/setup_core.py` using isolated Python, without importing or executing code from the target project. Requires Bash and Python 3.10+; native Windows users need an appropriate shell. Live harness compatibility is separate from local script tests.

## Target and scope

- `--target <existing-directory>` selects the project. Without it, use the caller's current directory, never the installed skill's location. Print the resolved target and reject root/home/missing targets.
- Start with `--dry-run`. Dry-run and audit inspect destination files as data only; they do not execute the target sync script, load its Python modules, start MCP servers, or modify the target.
- Default bootstrap creates **only AGENTS.md**, preserving an existing nonempty file. No stack, review agents, harnesses, MCP configs, sync script or skill directories are compulsory.
- `--harness claude`, `--harness codex` and `--harness opencode` are independent, repeatable opt-ins. Claude adds its shim and canonical skills link; Codex adds its config directory; OpenCode adds an empty config if absent.
- `--mcp` separately enables MCP data/config rendering for selected harnesses. It does not install/start servers, copy a sync script, or enable unselected harnesses. Claude uses canonical `.mcp.json`; Codex/OpenCode receive derived settings.

## Safety rules

Validate the entire known destination surface and all planned output types before any mutation. Refuse symlinked ancestors, linked files (including dangling links), and special files. The only accepted symlink is `.claude/skills -> ../.agents/skills`, resolving inside the target. Unsafe links require manual resolution; do not automatically delete or follow them.

Recheck destinations at write time and replace files atomically; never modify a different inode through a hard link. Work against a stable, owner-controlled directory: these preflight checks are not a sandbox against another process concurrently replacing or relocating directories. Do not run setup in an actively hostile/shared writable target.

The bundled renderer at `scripts/templates/sync-mcp-config.py` is the trusted rendering source. Read target MCP and existing configurations as data, never source or import target code. The renderer supports stdio command, args, and env only. Unsupported transports/fields or malformed inputs fail before writes instead of being silently discarded. Preserve unrelated OpenCode settings; refuse conflicting non-generated Codex settings for manual reconciliation. Never print configuration values or credentials in audit output.

## Modes

- No mode: bootstrap when AGENTS.md is missing/empty, otherwise optimize.
- `bootstrap`: minimal instructions plus explicitly selected integrations.
- `optimize` / `apply`: remove complete generated memory blocks and repair only explicitly selected integrations; never overwrite user-written instruction content or add unrequested integrations.
- `audit`: read-only checks for minimal instructions and integrations already present or explicitly selected. Missing optional integrations are not failures. Show mismatches against the bundled renderer without running destination code.

## Commands

```bash
# Minimal project; no integrations
bash .agents/skills/setup-multiharness-project/scripts/setup.sh bootstrap --target /path/to/project --dry-run
bash .agents/skills/setup-multiharness-project/scripts/setup.sh bootstrap --target /path/to/project

# Explicit additions only
bash .agents/skills/setup-multiharness-project/scripts/setup.sh bootstrap --target /path/to/project --harness claude
bash .agents/skills/setup-multiharness-project/scripts/setup.sh optimize --target /path/to/project --harness codex --harness opencode --mcp --dry-run

# Read-only drift inspection
bash .agents/skills/setup-multiharness-project/scripts/setup.sh audit --target /path/to/project
```

The bootstrap.sh, audit.sh and apply.sh entrypoints accept the same target/integration options and force their respective mode. Do not infer permission to publish, install dependencies, change personal/global configuration, or run destination scripts from a setup request.

## Delivery

Report exact additions/repairs and unresolved conflicts. Keep shared instructions short and move only conditional detail to references. Test dry-run immutability, external/dangling symlinks, opt-in combinations, config preservation and repeat execution. Do not claim live host behavior or token savings from structural checks.
