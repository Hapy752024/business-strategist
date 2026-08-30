# Workspace Rules

## Default Structure

```text
brand-projects/<slug>/
  brief.md
  research.md
  strategy.md
  guidelines.md
  stages/
    logo/
    colors/
    typography/
    imagery/
    ui/
    marketing/
  old/
  tokens/
  logos/source/
  logos/export/
  icons/
  ui/
  marketing/
  manifest.json
```

## Stage Iterations

Before creating new outputs for a stage:

1. Identify the stage folder, for example `stages/logo/`.
2. If it contains generated files, move them to `old/logo/<timestamp>/`.
3. Generate the new 3 alternatives into the clean stage folder.
4. Keep approved files in the final destination only after approval.

## OS Detection

Use:

```bash
uname -s
```

If unavailable or on Windows, use:

```powershell
$PSVersionTable.Platform
```

## Shell Commands

Linux/macOS:

```bash
mkdir -p "brand-projects/my-brand/stages/logo" "brand-projects/my-brand/old"
mv "brand-projects/my-brand/stages/logo"/* "brand-projects/my-brand/old/logo/20260607-120000/"
```

PowerShell:

```powershell
New-Item -ItemType Directory -Force -Path "brand-projects/my-brand/stages/logo","brand-projects/my-brand/old"
Move-Item "brand-projects/my-brand/stages/logo/*" "brand-projects/my-brand/old/logo/20260607-120000/"
```

Prefer the Python helper for portability.
