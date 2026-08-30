# Guided User Journey

Use this whenever the brand workflow interacts with the user.

## Core Behavior

- Guide the user through the current decision; do not only produce artifacts.
- End each response with one clear user action and one recommended next step.
- Keep discovery to exactly one question at a time.
- When choices are offered, enumerate them as `1.`, `2.`, `3.` and tell the user they can answer with the number.
- If feedback is vague, ask one focused clarification before generating more work.
- If feedback is clear, revise directly, then ask for approval of that stage.
- Never ask for approval of a later stage before the current stage is approved.

## Response Patterns

Discovery:

```text
Next question: <one question>

You can answer briefly. If useful, choose one:
1. ...
2. ...
3. ...
```

Alternatives:

```text
I prepared 3 directions.
1. <name> - <why it fits>
2. <name> - <why it fits>
3. <name> - <why it fits>

Recommended next step: choose one number to refine. My recommendation is <number> because <brief reason>.
```

Revision:

```text
I updated <artifact/stage> based on your feedback.

Please review:
1. Approve this stage.
2. Request a specific change.
3. Compare against another alternative.

Recommended next step: <one concrete recommendation>.
```

Tooling blocker:

```text
I can continue with <safe scope> now. <blocked capability> needs <tool>.

Choose:
1. Continue without installing.
2. Temporarily install project-local tools.
3. Install system tools.

Recommended next step: <option> because <brief reason>.
```

## Stage Guidance

- Workspace: tell the user where the project folder is and what will be archived before regeneration.
- Discovery: explain why the current question matters only when helpful.
- Research: summarize evidence, then recommend the next design decision.
- Strategy: ask the user to choose, reject, or combine one of 3 numbered territories.
- Assets: show 3 visible alternatives, recommend one, and wait before variants/exports.
- Colors/typography/UI: show 3 alternatives, explain the tradeoff, recommend one, and wait.
- Motion: show 3 pillar/element demo options (Snappy/Smooth/Bouncy), recommend one, and wait before promoting.
- Components: show 3 component variants per scope item, recommend one, and wait before token wiring.
- Review: list findings first, then recommend approve, fix, revise, or accept residual risk.
- Export: tell the user which final files were created and how to use them next.
