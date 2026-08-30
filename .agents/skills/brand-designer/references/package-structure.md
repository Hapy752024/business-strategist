# Brand Package Structure

Use this structure for final handoff. `stages/` is working history; root-level folders are canonical delivery.

```text
brand-projects/<slug>/
  EXECUTIVE-SUMMARY.md
  BRAND-GUIDELINES.md
  DECISIONS.md
  PACKAGE-MANIFEST.md
  logos/
    source/
    export/
      small/
      wordmark/
      pdf/
      eps/
  colors/
  typography/
  tokens/
  ui/
  imagery/
  marketing/
  qa/
  stages/
  old/
```

Rules:

- `logos/source/` contains approved SVG masters and is the source of truth.
- `logos/export/` contains generated assets only.
- `colors/`, `typography/`, `tokens/`, `ui/`, `imagery/`, and `marketing/` contain implementation/handoff artifacts.
- `qa/` contains QA reports, screenshots, and audit evidence.
- `stages/` contains exploration and approved-stage working files.
- `old/` contains historical archives only.
- Active docs should point to root-level canonical folders, not `stages/` or `old/`, unless explicitly discussing history.
- After a stage artifact is approved, promote or copy it into the relevant root-level delivery folder.

Required `PACKAGE-MANIFEST.md` sections:

- Canonical Delivery Folders.
- Working History.
- Implementation Rule.
- Source-of-truth rule for logo geometry and regenerated exports.
