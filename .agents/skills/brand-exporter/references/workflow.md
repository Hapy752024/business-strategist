# Imported workflow

## Procedure

# Brand Exporter

## Success Criteria

Quantitative:
- Triggers on >=90% of user requests that match the skill's trigger conditions in the description.
- Completes the workflow in a bounded number of tool calls (target <=15 for production skills, <=25 for research-heavy skills).
- Produces zero failed API/script calls per run.

Qualitative:
- User does not need to redirect mid-workflow.
- Output is structurally consistent across repeated runs.
- A new user can accomplish the task on the first try without guidance.

Run only after all requested stages are approved and HIGH review issues are resolved.
Before export, ask the user to confirm finalization if approval is not explicit.
After export, tell the user which files to use next for CSS, agents, and documentation.
Before export, ensure the brand-designer finalization gate has passed or list the residual risks.

Create:
- `tokens/branding.css` with CSS custom properties.
- `tokens/brand-tokens.json` with structured values.
- `PACKAGE-MANIFEST.md` if it does not already exist.
- `agent-skill/<brand-slug>/SKILL.md` for agents.
- `agent-skill/<brand-slug>/references/DESIGN.md` with rich guidelines.
- Copy `motion/motion-tokens.css`, `motion/motion-tokens.ts`, and `motion/motion-guidelines.md` into the delivery package under `motion/`.
- Copy the approved `components/` library (including `components/README.md`) into the delivery package under `components/`.
- Update `PACKAGE-MANIFEST.md` with two new sections: `## Motion` (token files + guidelines) and `## Components` (library path + install instructions).

Use `references/export-format.md` for file contents.
Use `scripts/create-brand-agent-skill.py` to scaffold final files.


## Output

Follow the output contract described by this skill and preserve provenance.

## Quality Checklist

Run the skill's existing checks and do not claim completion with unresolved blockers.
