# Independent subprojects

New projects have one navigation/controller root and four independently startable destinations:

```text
projects/<slug>/
  README.md
  project-manifest.json          # layout 3, controller_kind: umbrella
  business-analysis/                     # existing case controller, layout 2
    README.md                   # current case comparison
    cases/<case-id>/             # current findings, feasibility, economics
    market_research/            # shared research; case-specific research in cases/
    strategy/                   # single selected business plan and GTM
    history/                    # Business decisions and earlier versions
  branding/                     # brief, brand manifest, current assets
  digital-assets/
    website/                    # brief, website manifest, source and QA
    others/                     # other requested digital deliverables
  history/                      # design/digital decisions and earlier versions
```

Create only the requested subproject's contents. `digital-assets/` is a grouping folder, without its own stage machine or gate. Marketing campaigns/content and company operations remain optional Business workstreams. Do not create empty departments or duplicate strategy documents.

Use `python3 scripts/subprojects.py --workspace projects/<slug> --start business-analysis|branding|website|others --title "<title>" [--brief "<scope>"]`. Research initialization through `init_project.py` starts Business and returns its root. Project initialization through `project_workspace.py create` creates only umbrella navigation. Existing legacy and version-2 projects retain their paths; these commands never silently migrate existing research.

## Independent entry and optional sequence

Any destination can begin with its own user brief. Branding needs no Business research. Website needs neither Business nor Branding completion. Other digital assets need only their requested scope and applicable asset approvals. A sequence is available when requested: Business → Branding → Website/other assets, or any useful subset. Completion never starts the next subproject automatically.

Route Brand/Website work with `--entry-mode standalone` (the default), even inside an existing business project. `--subproject others` directs applicable asset/component specialists to other digital deliverables. `--project` identifies the destination; it does not imply a business handoff. An explicit `--entry-mode business_linked` consumes the selected Business plan and retains its evidence/selection checks. An explicit case selection is required for Business execution/GTM; researching alternatives never selects a winner.

Reuse approved branding assets through the existing `brand_refs`, artifact hashes and requested deliverables. Business handoffs use `build_business_to_brand_handoff.py`; the source is the current Business plan and the destination is umbrella `branding/`. Imported sources retain their owner, path/hash and binding. Refresh a stale handoff explicitly; never relabel a blocked business-linked task as standalone just to continue it. Starting a separate standalone task is allowed when that is the user's actual scope.

## Current output and history

Each subproject's current documents show the latest reviewed findings or a visible review-required state. Put dated decisions, evolution and superseded concepts in history, not at the bottom of the current recommendation. After follow-ups, revise the affected current sections instead of appending a chronological update. Retain source dates, evidence limits, assumptions and unresolved conflicts; preserve withdrawn claims only in their historical context. Newer timestamps alone do not resolve conflicting evidence. Business has one canonical evolution timeline with per-decision details and snapshots. Branding and digital publications share the umbrella timeline with named destinations and snapshots; local navigation links there instead of duplicating logs. Existing brand iteration folders remain compatible.

Root navigation links the authoritative subprojects; it does not copy their stage machines. Business publication cannot modify umbrella state. Umbrella publication cannot modify `business-analysis/**`. A pending publication blocks consumers of that owner. Recover that owner's journal with `case_workspace.py recover --workspace <owner-root>`.

The existing CLI publication adapter stages local output changes, checks destination ownership and conflicting revisions, and records final paths rather than temporary staging paths. It leaves external-service authorization and asset/release approvals in their existing workflows. These checks govern supported commands, not arbitrary filesystem access. Paid generation and deployment still require their existing explicit authorization.

The user-facing folder and start command are `business-analysis`. The internal `business` track/registry key and `--start business` alias remain compatible. Existing umbrella manifests registered to `business/` continue to resolve there until an explicit migration; no second analysis folder is created. See [the existing-project migration plan](../docs/agent-improvements/existing-project-migration-plan.md).
