# Owner-action contract

Use when a deliverable surfaces work only the owner can do or decide. Apply with references/task-scope.md: include only decisions and actions relevant to the requested deliverable; never append recurring programs to narrow copy or execution work.

States: `proposed` (agent suggestion, not adopted), `accepted` (owner agreed), `deferred` (explicitly postponed), `completed`. Only `accepted` actions and genuine blockers persist; a `proposed` action never recurs on resume as if adopted.

Persistence: write accepted actions and blockers into the project manifest's existing `next_action` and `open_blockers` fields — these are what the workspace-lifecycle resume flow reads, and they are the source of truth. A human-readable `owner-actions.md` inside the project may render the same rows but never replaces manifest updates. `next_action` is a single string in schemas/project-manifest.schema.json and schemas/research-manifest.schema.json, so write the accepted next steps into it as one concise ordered set, highest-priority first, and render the full per-action rows — each keeping its `proposed`/`accepted`/`deferred` state visible — in the project's `owner-actions.md`. Acceptance alone does not make work a blocker or a dependency: reserve `open_blockers` for actual dependencies and genuine blockers only, preserve any unrelated blockers already recorded there, and never carry an optional accepted follow-up as an `owner action: `-prefixed entry, because references/workspace-lifecycle.md and AGENTS.md both surface a non-empty `open_blockers` on resume as work standing in the way.

Each row: action, layer or area it feeds, cadence (one-off/weekly/monthly/quarterly), rough effort, expected evidence payoff, state. Cadence is a proposal until `accepted`.

Owner-only vs agent-verifiable: ask the owner only for unavailable firsthand facts, changed commercial commitments (prices, policies, guarantees) and actual decisions (publishes, sends, platform applications, spend). Facts verifiable against current authoritative sources or an approved source record are rechecked by the agent without asking.

Preserve publication/send authorization already granted in the session; do not re-ask. Identity-gated approvals (merchant programs, business-profile verification) are always owner actions.

Example rows (illustrative, not defaults):
- Publish one founder post per week from the listening-driven topic queue | SMO→GEO corroboration | weekly | 1h | earned-mention growth | proposed
- Provide real return-window terms for policy markup | DEO trust inputs | one-off | 15min | accurate Offer/Policy encoding | accepted
- Fact-check 12 drafted answer capsules on /pricing and /compare | AEO accuracy | one-off | 45min | safe publication | proposed
