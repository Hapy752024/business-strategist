# Owner-action contract

Use when a deliverable surfaces work only the owner can do or decide. Apply with references/task-scope.md: include only decisions and actions relevant to the requested deliverable; never append recurring programs to narrow copy or execution work.

States: `proposed` (agent suggestion, not adopted), `accepted` (owner agreed), `deferred` (explicitly postponed), `completed`. Only `accepted` actions and genuine blockers persist; a `proposed` action never recurs on resume as if adopted.

Persistence: resolve the active track's manifest (website work uses its website-manifest.json, Branding its brand manifest, Business its current case/research manifest); do not overwrite the umbrella or unrelated next steps. Accepted actions are losslessly encoded as one `Owner action: {JSON}` line each in the existing `next_action` string. Each object contains `id`, `state: accepted`, `action`, `reason_owner`, `cadence`, `effort`, `review_at`, `completion`, `outcome`, `stop_rule`, and `details` (relative path/anchor to the human row). Stable IDs permit updates without duplication. All fields are nonempty strings. Keep unrelated text and owner rows byte-for-byte where possible. `scripts/monitoring/owner_actions.py` provides `update_action` and `accepted_actions` without writing files or granting acceptance; stage its returned manifest through the active owner's normal publication flow. Advance manifest revision/timestamp with that publication.

Render full rows in the active track's owner-actions.md. Proposed, deferred and completed rows can remain there as history, but are not active commitments. Acceptance must come from the user or an existing explicit authorization. Transition to completed/deferred removes only that ID from the active manifest; record the result/reason in its human row. Never silently replace accepted work with a new proposal. For recurring work record the next review/due point, customer outcome and stop/change rule; completing one occurrence does not authorize a new cadence.

On resume read the active manifest, parse accepted rows and open their detail links; reconcile state before recommending action. Do not resurrect completed/deferred/proposed rows from the rendering. Legacy free-text tasks stay intact until their acceptance and details are established. Reserve `open_blockers` for actual dependencies and preserve unrelated blockers. Optional accepted work is never a blocker merely because it is accepted.

Each row: stable ID, action, layer/area, why only the owner can supply it, cadence, rough effort, needed-by/review point, expected customer outcome/evidence payoff, definition of completion, stop/change rule, state. Cadence remains proposed until accepted.

Owner-only vs agent-verifiable: ask the owner only for unavailable firsthand facts, changed commercial commitments (prices, policies, guarantees) and actual decisions (publishes, sends, platform applications, spend). Facts verifiable against current authoritative sources or an approved source record are rechecked by the agent without asking.

Preserve publication/send authorization already granted in the session; do not re-ask. Identity-gated approvals (merchant programs, business-profile verification) are always owner actions.

Example rows (illustrative, not defaults):
- Publish one founder post per week from the listening-driven topic queue | SMO→GEO corroboration | weekly | 1h | earned-mention growth | proposed
- Provide real return-window terms for policy markup | DEO trust inputs | one-off | 15min | accurate Offer/Policy encoding | accepted
- Fact-check 12 drafted answer capsules on /pricing and /compare | AEO accuracy | one-off | 45min | safe publication | proposed
