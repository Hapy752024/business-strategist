# Workspace mode (route `brand-workspace-manager`)

Create, resume or revise a brand workspace at the start of every brand project and before regenerating stage assets. Apply repo-root `references/subprojects.md`: new work belongs to umbrella `branding/`, independent of Business research; use business-linked entry only when consuming a selected Business handoff. Current outputs stay separate from dated decisions and archived versions.

## Rules

1. Create one project folder before asset work begins.
2. Before regenerating a stage, move that stage's files into `old/<stage>/<timestamp>/`; generate the new 3 alternatives into the clean stage folder; keep approved files in their final destination only after approval.
3. Never delete old iterations unless the user explicitly asks.
4. Tell the user which folder/stage is active and what will happen before the next generation.
5. Detect the OS (`uname -s`, or `$PSVersionTable.Platform` on Windows) before giving shell commands; prefer the Python helpers for portability.

Default base dir: `projects/`. `.agents/skills/brand-identity/scripts/manage-brand-workspace.py` and `workspace_cli.py create` accept `--project <slug>`, placing the workspace at `projects/<slug>/branding` (brand_id = slug); `workspace_cli.py create` also links the brand track into `projects/<slug>/project-manifest.json` when that controller exists. The old `projects/brand-projects/` root is rejected by a relocation guard.

## Manifest-aware commands (atomic, revision-checked writes)

```bash
python3 .agents/skills/brand-identity/scripts/workspace_cli.py create --name "My Brand" --project my-brand
python3 .agents/skills/brand-identity/scripts/workspace_cli.py resume projects/my-brand/branding
python3 .agents/skills/brand-identity/scripts/workspace_cli.py archive-stage projects/my-brand/branding --stage logo
python3 .agents/skills/brand-identity/scripts/workspace_cli.py record-option projects/my-brand/branding --artifact-id logo-1 --artifact-type logo --stage logo --candidate stages/logo/mark.svg --destination logos/source/mark.svg
python3 .agents/skills/brand-identity/scripts/workspace_cli.py approve-option projects/my-brand/branding --artifact-id logo-1 --approver "user" --notes "Explicitly selected option 1"
python3 .agents/skills/brand-identity/scripts/workspace_cli.py promote projects/my-brand/branding --artifact-id logo-1
python3 .agents/skills/brand-identity/scripts/workspace_cli.py promote projects/my-brand/branding --artifact-id logo-1 --confirm
```

`promote` is a dry run without `--confirm`. A different existing destination fails closed. Use `--replace-conflict --replacement-approver "<identity>"` only after separate explicit replacement approval; never infer it from approval of the candidate. Record source artifact IDs for derivatives and supersede prior approvals explicitly.

## Default structure

```text
projects/<slug>/branding/
  brief.md  research.md  strategy.md  guidelines.md  manifest.json
  stages/{logo,colors,typography,imagery,ui,marketing}/
  old/
  tokens/  logos/source/  logos/export/  icons/  ui/  marketing/
```

The final handoff layout is in [package structure](package-structure.md).
