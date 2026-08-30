# Review Checklist

## Review Loop

1. Review artifacts against the brief, approved territory, and guidelines.
2. Review against `best-practices-guidelines.md` for brand strategy, human-centered design, color harmony, accessibility, typography, UI states, and guideline completeness.
3. Run visual inspection when artifacts are visual.
4. For final packages, run `scripts/audit-brand-package.py <project-dir>`.
5. List findings by severity.
6. Fix HIGH issues.
7. Rerun review.
8. Continue until no HIGH issues remain or the user explicitly accepts the risk.

## Severity

HIGH:

- Output contradicts the brief or approved territory.
- Output contradicts the target audience, primary country/region, cultural context, or buyer/user needs.
- Brand output fails to express the approved USP/differentiation.
- Brand looks generic for its category without a clear strategic reason.
- Work proceeds to a later stage without explicit approval of the previous stage.
- Full asset sets are produced before a direction is selected.
- Logo variants are inconsistent or unusable at required sizes.
- Normal text contrast fails WCAG AA 4.5:1.
- UI graphics, focus indicators, or large text fail expected 3:1 contrast where they communicate meaning.
- Color alone is used to communicate error, warning, success, selection, or status.
- UI states are missing for requested components.
- Visual output has obvious overlap, clipping, illegible text, broken layout, or missing assets.
- Design uses misleading or inappropriate trust cues for regulated/high-stakes industries.
- Required export formats are missing without explanation.
- Final package has missing canonical delivery folders or no package manifest.
- Export manifests point to missing files.
- Active root-level HTML has missing local assets.

MEDIUM:

- Guidelines are vague where implementation rules are needed.
- Color roles are incomplete.
- Palette harmony is weak, over-saturated, or lacks neutral/surface support.
- Typography lacks fallback/licensing notes.
- Typography scale is incomplete, too complex, or not tested with long real strings.
- Messaging hierarchy does not make clear what should be remembered first.
- Responsive behavior is under-specified.
- Marketing assets lack safe-area or usage guidance.
- Components lack clear default/hover/active/focus/disabled/loading/error behavior.
- Cultural/localization assumptions are not documented.
- Active docs still point to `stages/` or `old/` as implementation sources.
- Approved alternatives remain side-by-side in active docs after the user selected one.

LOW:

- Naming could be clearer.
- Minor polish improvements.
- Optional examples or mockups would improve usability.
- Additional do/don't examples would make the guide easier to apply.

## Review Output Format

```text
Findings
HIGH
1. ...

MEDIUM
1. ...

LOW
1. ...

Fix Plan
1. ...

Residual Risk
1. ...
```

## Independent Critic

When subagents are available, launch a critic with only:

- Brief.
- Approved territory.
- Final artifacts.
- Review checklist.

Do not include the creator's reasoning or expected answer.
