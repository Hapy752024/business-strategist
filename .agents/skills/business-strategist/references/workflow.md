# Business Strategist Workflow

1. Normalize the request and inspect only the relevant active manifest.
2. Read repo-root `references/task-scope.md` and run `python3 scripts/route_workflow.py "<request>" --intent <route-id> --task-scope <focused|execution|strategy> --check-skill <selected-skill>` when intent is understood — add `--project <slug>` whenever the request targets a venture with a business track. Respect exclusions, preserved decisions and new-project boundaries. Use `--continue-workspace` only for an actual continuation. Consult `references/routing.md` for ownership; phrase matches are a fallback, not semantic understanding.
3. Require exit 0 before dispatch; exit 2 means a blocked gate or invalid selection. Skill-name route IDs cover specialists without automatic phrase matching. An override requires an existing readable manifest and a successful audit write; it does not prove evidence quality or user authorization. Pain-first gate check: if the packet has `gate_blocked: true`, do not dispatch the downstream specialist. Establish the foundation first — customer segment, customer journey, and pain points with web-searched evidence via `idea-grill`/evidence collection under `market_research/{customer_segments,customer_journey,pain_points}` — until `problem_validation` passes, or the user explicitly overrides (`--override-gate`, recorded in the manifest's events).
4. If the result is `business-strategist`, ask one routing question; otherwise dispatch the selected specialist.
5. Pass only the selected specialist's required inputs. Do not preload unrelated research or brand references.
6. Record the route, approvals, artifacts, and next action in the controller manifest. Specialist workers write disjoint artifacts and return result packets.

For business-position selection or a coherence review, conditionally use `references/strategic-positioning.md` at repo root. Reuse supplied founder decision context before asking a question; ask one focused question only when a missing objective, role, means, downside, time horizon, or channel constraint would change the comparison. GTM owns position selection; operations derives delivery requirements; marketing and branding consume the selected decision. Reuse the active strategy record and do not reopen strategy for narrow execution requests.

## Output

```json
{
  "skill": "<selected skill>",
  "mode": "<default or specialist mode>",
  "matched": [],
  "forbidden_skills": [],
  "prerequisites": [],
  "expected_artifacts": [],
  "estimated_cost": "low",
  "approval_required": false,
  "next_action": "<concrete next step>"
}
```

For any strategic recommendation, coach directly: make the first decision explicit as `insufficient_evidence`, `investigate`, `test`, `commit`, `pivot`, `park`, or `stop`; challenge unsupported claims; name the decisive uncertainty and cheapest next test. Do not manufacture encouragement or turn a source summary into a business verdict.

Apply the entrant-success assessment in `references/strategic-positioning.md` at repo root whenever competition influences a recommendation. Before handoff check: served versus saturated; founder-scale customer/economic requirements; concrete acquisition and relationship path; audited evidence; explicit explanation of any ranking change. Confirm requested coverage against completed artifacts. Report partial research when a material requested comparison, source audit, channel review or operator analysis remains unfinished. Test execution and evaluation-fixture validation do not prove strategic quality or live agent behavior.

For a clear idea needing strategy or launch advice, dispatch `business-archetype-playbook-researcher` for a bounded web/social search of comparable founders and operators before recommending tactics. Reuse existing checked cases where applicable; bring the useful patterns, to-dos and not-to-dos into the executive README and link supporting detail. Do not trigger this study for narrow factual or fixed-scope execution requests.

Treat this operator study as a prerequisite owned by that specialist, then resume the selected strategy specialist with its result; it does not authorize unrelated parallel workflows. At a consequential research handoff, record the source-audit result. If a claim ledger is used, run `validate_synthesis.py --require-source-review` and report its result. Without a claim ledger, provide the equivalent per-source accepted/rejected/unresolved review and reasons in the existing evidence audit. Missing review leaves affected conclusions provisional and synthesis incomplete. The validator checks review records, not the truth of the analyst's judgment.
