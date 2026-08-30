# Imported workflow

## Procedure

# Brand Workspace Manager

## Success Criteria

Quantitative:
- Triggers on >=90% of user requests that match the skill's trigger conditions in the description.
- Completes the workflow in a bounded number of tool calls (target <=15 for production skills, <=25 for research-heavy skills).
- Produces zero failed API/script calls per run.

Qualitative:
- User does not need to redirect mid-workflow.
- Output is structurally consistent across repeated runs.
- A new user can accomplish the task on the first try without guidance.

Use at the start of every brand project and before regenerating stage assets.

Rules:
- Create one project folder before asset work begins.
- Detect Windows, Linux, or macOS before giving shell commands.
- Prefer `scripts/workspace_cli.py` for manifest-aware operations; writes are atomic and revision checked.
- Before regenerating a stage, move previous files for that stage into `old/<stage>/<timestamp>/`.
- Never delete old iterations unless the user explicitly asks.
- Tell the user which folder/stage is active and what will happen before the next generation.

Default folder: `brand-projects/<slug>/`.

Use `references/workspace-rules.md` for structure and OS commands.

For manifest-aware operations use `scripts/workspace_cli.py`:

```bash
python3 scripts/workspace_cli.py create --name "My Brand"
python3 scripts/workspace_cli.py resume brand-projects/my-brand
python3 scripts/workspace_cli.py archive-stage brand-projects/my-brand --stage logo
python3 scripts/workspace_cli.py record-option brand-projects/my-brand --artifact-id logo-1 --artifact-type logo --stage logo --candidate stages/logo/mark.svg --destination logos/source/mark.svg
python3 scripts/workspace_cli.py approve-option brand-projects/my-brand --artifact-id logo-1 --approver "user" --notes "Explicitly selected option 1"
python3 scripts/workspace_cli.py promote brand-projects/my-brand --artifact-id logo-1
python3 scripts/workspace_cli.py promote brand-projects/my-brand --artifact-id logo-1 --confirm
```

`promote` is a dry run without `--confirm`. A different existing destination fails closed. Use `--replace-conflict --replacement-approver "<identity>"` only after separate explicit replacement approval; do not infer it from approval of the candidate. Record source artifact IDs for derivatives and supersede prior approvals explicitly.


## Output

Follow the output contract described by this skill and preserve provenance.

## Quality Checklist

Run the skill's existing checks and do not claim completion with unresolved blockers.
