# Startup Check

Run this before discovery when possible:

```bash
python3 .agents/skills/brand-designer/scripts/check-brand-tooling.py
```

If something required for the requested deliverables is missing, ask the user before installing and provide exact commands.

When export tooling is missing, offer numbered choices:

1. Continue discovery/strategy now and install export tools later.
2. Temporarily install Python export libraries into `.brand-tools/venv` now.
3. Install full system export tools now.

Only run an install command after the user chooses an option.

## Required Atomic Skills

These should exist in `.agents/skills/`:

- `brand-discovery-interviewer`
- `brand-workspace-manager`
- `brand-guideline-researcher`
- `brand-typography-researcher`
- `brand-strategy-director`
- `brand-asset-producer`
- `brand-ui-kit-producer`
- `brand-frontend-app-designer`
- `brand-quality-reviewer`
- `brand-exporter`
- `brand-guidelines-writer`

If missing, tell the user to restore this repository's `.agents/skills/brand-*` folders or rerun the skill installation/scaffold step that created them.

## Export Tool Commands

Temporary local Python install for PNG/PDF/ICO fallback:

```bash
python3 .agents/skills/brand-designer/scripts/install-brand-tooling.py --mode temp
```

Print system install commands for this OS:

```bash
python3 .agents/skills/brand-designer/scripts/install-brand-tooling.py --mode system --print-only
```

Supported OS command generation:

1. Linux/WSL: `apt-get`.
2. macOS: `brew`.
3. Windows: `winget`.

Ubuntu/Debian/WSL:

```bash
sudo apt-get update
sudo apt-get install -y inkscape imagemagick python3-pip
python3 -m pip install --user pillow cairosvg
```

macOS with Homebrew:

```bash
brew install --cask inkscape
brew install imagemagick
python3 -m pip install --user pillow cairosvg
```

Node optional, only for Sharp/WebP pipelines:

```bash
npm install --save-dev sharp
```

## Env Setup

For OpenRouter image alternatives:

```bash
cp .agents/skills/brand-asset-producer/assets/.env.example .env
```

Then fill `OPENROUTER_API_KEY`, `OPENROUTER_IMAGE_MODELS`, and `OPENROUTER_IMAGE_ALTERNATIVES`.

## Frontend Skill

If `frontend-design` is unavailable, continue without it unless the user specifically requests polished UI screens/component demos. Ask the user to install the Anthropic/frontend-design skill in their agent environment using their normal skill/plugin installer.

## Trusted Frontend MCPs

For interactive app/screen design, ask the user whether to install trusted MCPs:

1. Figma MCP: official Figma remote MCP server, preferred.
2. Storybook MCP: official Storybook addon, for real coded components.
3. Chromatic MCP: trusted hosted Storybook MCP from Chromatic for team/remote use.

Use `brand-frontend-app-designer/references/trusted-mcps.md` for commands and JSON.
