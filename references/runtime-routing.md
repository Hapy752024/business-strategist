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

`override_gate: true` is only for an explicit user override already given in the conversation. It uses the existing manifest audit writer. Session/call identity makes redelivery of an override idempotent. An audit record is not proof of user authorization or that the specialist subsequently executed.

The host wrapper turns script/import errors into blocking exit 2. Hook output tests and configured-command subprocess tests cover both invocation paths. This is **skill-dispatch enforcement**, not complete tool mediation: shell commands, direct file reads/writes, disabled hooks, other hosts and foreign skills remain outside this boundary. Do not claim it prevents a hostile agent with filesystem access from bypassing policy. Specialist prerequisites and paid-provider permissions remain separately applicable.

Codex/OpenCode and ordinary shell callers retain the portable `route_workflow.py --check-skill` contract. No cross-host runtime enforcement is claimed.

Catalog-bound `required_references` appear in route packets and the Claude hook's checked context. The router and setup route validator reject missing, empty or out-of-repository reference files. Callers must read applicable references; neither emitting their paths nor a successful dispatch proves that they were read or that customer evidence was interpreted correctly. Customer-voice analysis is a shared method in `references/customer-voice.md`, not an additional automatic stage pass.

Hook contract source: [Claude Code hooks reference](https://code.claude.com/docs/en/hooks), checked 2026-09-11. Local CLI version checked: 2.1.233. Live model dispatch has not been benchmarked.

## Bare dispatch

A skill that exactly one route targets (`"single_mode": true` in `config/workflow-routes.json`, checked against the route count by `validate_skill_routes.py`) accepts plain-text `args`: the hook synthesizes a focused route (the skill's route ID; standalone, or the current business workspace from `cwd`) and the pain-first gate applies as usual. Routes that are pain-gated or have strategy prerequisites accept bare text only when `cwd` is inside a business workspace (the project then comes from `cwd`); elsewhere they need an explicit envelope. Multi-mode skills always need the JSON envelope with an explicit route ID. Malformed JSON is rejected, never treated as plain text.

## Versioned cases

For a known case add `case` to the checked route envelope and use `--case <id>` in CLI dispatch. The packet includes the registered output root, reviewed assessment revision, source bindings and selected execution binding where required. `case-appraisal` is the bounded opportunity-risk-designer mode; its bare skill alias is now ambiguous. Initial segment/journey/pain research is required, but no passed pain gate or execution selection. Full startup/GTM/pilot and explicitly business-linked design retain their own prerequisites. Standalone design requires no research or migration. See [subprojects.md](subprojects.md) for new paths and optional handoffs.

Case evidence overrides require `override_stages: ["problem_validation", ...]` in the envelope or repeated `--override-stage` flags, alongside the explicit override. They are recorded against the current case revision and selection generation. They cannot waive source freshness, missing selection, an old generation, unknown IDs or pending publication. Changing scope requires a fresh user decision.


## Case status

`python3 scripts/route_workflow.py status (--project <slug> | --workspace <business-root>) --case <id> [--json]` lists routes whose skill or mode declares `consumes` in `config/skill-catalog.json`. States: `runnable`, `blocked` (a consumed artifact is missing), `stale` (a consumed file's digest differs from the case manifest's source binding, or case insights are update-pending), `not_adopted` (the route consumes the assumption register and the case has none). Interview-bridge notes list smoke-test responder ledgers with bookings. A pending publication exits 2 with the recovery message. Status is read-only and never records runs; gates and authorization stay with the normal route call.
