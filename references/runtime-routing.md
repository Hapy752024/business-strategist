# Runtime routing boundary

## Route selection

Before specialist dispatch, run `scripts/route_workflow.py` with the understood `--intent`, `--task-scope`, and `--check-skill <selected-skill>`; include `--project <slug>` and the investigated `--case <id>` for a versioned venture.
Exit 2 means stop dispatch (blocked gate or invalid selection).
Research focus never selects execution.
For explicit specialist requests, use the configured route ID; an unambiguous skill name is accepted as an alias.
Multi-mode specialists require the specific route ID (for example `case-appraisal` for provisional feasibility/economics, because `opportunity-risk-designer` has several modes).
Empty `match` lists are intentional internal-stage routes, not orphan skills.
Routing does not waive specialist prerequisites or authorize side effects.
`scripts/validate_skill_routes.py` checks catalog/disk parity, route reachability and typed `consumes`/`produces` contracts in CI.
For a registered case, the read-only `status` subcommand (see Case status below) reports runnable, blocked, stale or not-adopted routes; it does not authorize dispatch.

## Claude dispatch hooks

Claude Code binds `scripts/enforce_skill_route.py` to `PreToolUse` (`Skill`) and `UserPromptExpansion` (direct slash commands). The adapter checks repository-owned skills only and leaves foreign plugin skills and the `business-strategist` routing entrypoint alone. It recomputes the route and current pain gate rather than trusting a previous pass. It never returns `permissionDecision: allow`, so normal permissions still apply.

For agent-driven specialist invocation, pass routing metadata in the skill's args:

```json
{
  "route": {
    "request": "Build a landing page from the approved brief",
    "intent": "website-build",
    "task_scope": "execution",
    "project": "example-venture"
  },
  "input": "The actual specialist brief and artifact pointers"
}
```

Supply a `project` destination or `"standalone": true` when there is no project destination. Independent design may also carry both. Brand/Website `entry_mode` defaults to `standalone`; set `business_linked` only for explicitly requested selected-business consumption. `subproject` may resolve `branding`, `website` or `others`. This declaration is supplied by the calling agent using the user's scope; do not ask the user for technical JSON. Resolve missing venture/standalone context in normal conversation before dispatch. A detected project still owns its output paths. Independent Branding/Website work inside it needs no Business research; this does not allow Business/GTM tasks to bypass their gates. Unknown route IDs, mismatched skills, malformed metadata and blocked gates deny dispatch. Skill-tool calls receive `input` as their ordinary arguments after checking; metadata is kept out of the specialist task.

Direct repository slash invocations currently need the same envelope; if absent they stop with a routing explanation. Users can use the `business-strategist` entrypoint with natural language to have the agent prepare the envelope. Foreign plugin slash commands are unaffected.

`override_gate: true` is only for an explicit user override already given in the conversation and is refused without a nonempty `override_reason` quoting the user's words. It uses the existing manifest audit writer; the event records `source: "agent_envelope"` and the reason, while a founder's CLI `--override-gate` records `source: "cli"`. Session/call identity makes redelivery of an override idempotent. An audit record is not proof of user authorization or that the specialist subsequently executed.

The host wrapper turns script/import errors into blocking exit 2. Hook output tests and configured-command subprocess tests cover both invocation paths. This is **skill-dispatch enforcement**, not complete tool mediation: shell commands, direct file reads/writes, disabled hooks, other hosts and foreign skills remain outside this boundary. Do not claim it prevents a hostile agent with filesystem access from bypassing policy. Specialist prerequisites and paid-provider permissions remain separately applicable.

Codex/OpenCode and ordinary shell callers retain the portable `route_workflow.py --check-skill` contract. No cross-host runtime enforcement is claimed.

Catalog-bound `required_references` appear in route packets and the Claude hook's checked context. The router and setup route validator reject missing, empty or out-of-repository reference files. Callers must read applicable references; neither emitting their paths nor a successful dispatch proves that they were read or that customer evidence was interpreted correctly. Customer-voice analysis is a shared method in `references/customer-voice.md`, not an additional automatic stage pass.

Hook contract source: [Claude Code hooks reference](https://code.claude.com/docs/en/hooks), checked 2026-09-11. Local CLI version checked: 2.1.233. Live model dispatch has not been benchmarked.

## Bare dispatch

A skill that exactly one route targets (`"single_mode": true` in `config/workflow-routes.json`, checked against the route count by `validate_skill_routes.py`) accepts plain-text `args`: the hook synthesizes a focused route (the skill's route ID; standalone, or the current business workspace from `cwd`) and the pain-first gate applies as usual. Routes that are pain-gated or have strategy prerequisites accept bare text only when `cwd` is inside a business workspace (the project then comes from `cwd`); elsewhere they need an explicit envelope. Multi-mode skills always need the JSON envelope with an explicit route ID. Malformed JSON is rejected, never treated as plain text.

## Versioned cases

For a known case add `case` to the checked route envelope and use `--case <id>` in CLI dispatch. The packet includes the registered output root, reviewed assessment revision, source bindings and selected execution binding where required. `case-appraisal` is the bounded opportunity-risk-designer mode; its bare skill alias is now ambiguous. Initial segment/journey/pain research is required, but no passed pain gate or execution selection. Full startup/GTM/pilot and explicitly business-linked design retain their own prerequisites. Standalone design requires no research or migration. `--project` takes the top-level directory name under `projects/` (never a path), for real and acceptance-eval projects alike. `--case` requires a versioned project with that case registered (`scripts/evidence_scout/init_project.py --project "<name>" --workspace projects/<slug> --case <id>`); GTM and other execution routes also require the case to be selected from an explicit founder choice (`scripts/case_workspace.py select ...`, see [case-assessment.md](case-assessment.md)). A blocked pain-first gate is overridden only through `route_workflow.py --override-gate` with each missing stage named by `--override-stage`, so the block and the override stay observable. See [subprojects.md](subprojects.md) for new paths and optional handoffs.

Case evidence overrides require `override_stages: ["problem_validation", ...]` in the envelope or repeated `--override-stage` flags, alongside the explicit override. They are recorded against the current case revision and selection generation. They cannot waive source freshness, missing selection, an old generation, unknown IDs or pending publication. Changing scope requires a fresh user decision.


## Case status

`python3 scripts/route_workflow.py status (--project <slug> | --workspace <business-root>) --case <id> [--json]` lists routes whose skill or mode declares `consumes` in `config/skill-catalog.json`. States: `runnable`, `blocked` (a consumed artifact is missing), `stale` (a consumed file's digest differs from the case manifest's source binding, or case insights are update-pending), `not_adopted` (the route consumes the assumption register and the case has none). Interview-bridge notes list smoke-test responder ledgers with bookings. A pending publication exits 2 with the recovery message. Status is read-only and never records runs; gates and authorization stay with the normal route call.

## Routing boundaries

- Market discovery finds problems and segments; idea validation pressure-tests a named idea.
- Brand requests remain independent. Use `brand-designer` for identity orchestration and `brand-website-designer-builder` for marketing/corporate sites.
- Use `brand-frontend-app-designer` for product dashboards and application screens.
- Use `competitor-marketing-analyzer` for competitor pages, not for building a new site.
- Use the website skill's experiment mode for a simple control/treatment test; do not redesign when the user only asks for an experiment.
- Business-position selection/repositioning belongs to `archetype-gtm-strategist` (`--intent business-positioning`, focused positioning mode); a delivery-model request with a selected position belongs to `company-operating-system` (`--intent company-operations`). For compound requests, select the position first and continue only to requested implications. Use explicit intent when context/paraphrases would mislead phrase matching. Marketing-message positioning stays with marketing; standalone branding stays independent.

## Router procedure

1. Normalize the request and inspect only the relevant active manifest.
2. Read repo-root `references/task-scope.md` and run the route command (see Route selection) when intent is understood; add `--project <slug>` whenever the request targets a venture with a business track. Respect exclusions, preserved decisions and new-project boundaries. Use `--continue-workspace` only for an actual continuation. Consult Routing boundaries for ownership; phrase matches are a fallback, not semantic understanding.
3. Require exit 0 before dispatch. Skill-name route IDs cover specialists without automatic phrase matching. An override requires an existing readable manifest and a successful audit write; it does not prove evidence quality or user authorization. Pain-first gate check: if the packet has `gate_blocked: true`, do not dispatch the downstream specialist. Establish the foundation first (customer segment, customer journey, and pain points with web-searched evidence via `idea-grill`/evidence collection under `market_research/{customer_segments,customer_journey,pain_points}`) until `problem_validation` passes, or the user explicitly overrides (`--override-gate`, recorded in the manifest's events).
4. If the result is `business-strategist`, ask one routing question; otherwise dispatch the selected specialist.
5. Pass only the selected specialist's required inputs. Do not preload unrelated research or brand references.
6. Record the route, approvals, artifacts, and next action in the controller manifest. Specialist workers write disjoint artifacts and return result packets.

For business-position selection or a coherence review, conditionally use `references/strategic-positioning.md` at repo root. Reuse supplied founder decision context before asking a question; ask one focused question only when a missing objective, role, means, downside, time horizon, or channel constraint would change the comparison. GTM owns position selection; operations derives delivery requirements; marketing and branding consume the selected decision. Reuse the active strategy record and do not reopen strategy for narrow execution requests.

### Router output

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

For a clear idea needing strategy or launch advice, dispatch `business-archetype-playbook-researcher` for a bounded web/social search of comparable founders and operators before recommending tactics. Reuse existing checked cases where applicable; bring the useful patterns, to-dos and not-to-dos into the selected case's `case_insights.md` and link supporting detail. Do not trigger this study for narrow factual or fixed-scope execution requests.

Treat this operator study as a prerequisite owned by that specialist, then resume the selected strategy specialist with its result; it does not authorize unrelated parallel workflows. At a consequential research handoff, record the source-audit result. If a claim ledger is used, run `validate_synthesis.py --require-source-review` and report its result. Without a claim ledger, provide the equivalent per-source accepted/rejected/unresolved review and reasons in the existing evidence audit. Missing review leaves affected conclusions provisional and synthesis incomplete. The validator checks review records, not the truth of the analyst's judgment.
