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

Supply a `project` destination or `"standalone": true`; Brand/Website `entry_mode` defaults to `standalone` (set `business_linked` only for explicitly requested selected-business consumption). The calling agent fills this from the user's scope; never ask the user for technical JSON. Independent Branding/Website work inside a project needs no Business research; this does not let Business/GTM tasks bypass their gates. Unknown route IDs, mismatched skills, malformed metadata and blocked gates deny dispatch.

Direct repository slash invocations follow the same plain-text rule below; when no route can be inferred they stop with a routing explanation. Users can use the `business-strategist` entrypoint with natural language to have the agent prepare the envelope. Foreign plugin slash commands are unaffected.

`override_gate: true` is only for an explicit user override already given in the conversation and is refused without a nonempty `override_reason` quoting the user's words; the manifest audit records it. An audit record is not proof of user authorization.

Script/import errors block with exit 2. This is **skill-dispatch enforcement**, not complete tool mediation: shell commands, direct file reads/writes, disabled hooks, other hosts and foreign skills remain outside this boundary. Do not claim it prevents a hostile agent with filesystem access from bypassing policy. Specialist prerequisites and paid-provider permissions remain separately applicable.

Codex/OpenCode and ordinary shell callers retain the portable `route_workflow.py --check-skill` contract. No cross-host runtime enforcement is claimed.

Catalog-bound `required_references` appear in route packets and the Claude hook's checked context. The router and setup route validator reject missing, empty or out-of-repository reference files. Callers must read applicable references; neither emitting their paths nor a successful dispatch proves that they were read or that customer evidence was interpreted correctly. Customer-voice analysis is a shared method in `references/customer-voice.md`, not an additional automatic stage pass.

Hook contract source: [Claude Code hooks reference](https://code.claude.com/docs/en/hooks), checked 2026-09-11.

## Bare dispatch

The JSON envelope is optional for every skill. Plain-text `args` work when the hook can pick the route: the skill's only route (`"single_mode": true` in `config/workflow-routes.json`, checked against the route count by `validate_skill_routes.py`), or for a multi-mode skill the one route whose `match` phrases score highest in the text (`route_workflow.infer_mode`; a tie or no match lists candidate route IDs in the error). The hook synthesizes a focused route (standalone, or the current business workspace from `cwd`) and the pain-first gate applies as usual. The envelope is still needed to choose a mode explicitly, to override the gate, and for pain-gated routes or routes with strategy prerequisites outside a business workspace (inside one, the project comes from `cwd`). Malformed JSON is rejected, never treated as plain text.

## Versioned cases

For a known case add `case` to the envelope and `--case <id>` to CLI dispatch. `case-appraisal` is the bounded opportunity-risk-designer mode: initial segment/journey/pain research is required, but no passed pain gate or execution selection. `--project` takes the top-level directory name under `projects/` (never a path). `--case` requires a registered case; GTM and other execution routes also require the case to be selected from an explicit founder choice ([case-assessment.md](case-assessment.md)). A blocked pain-first gate is overridden only through `route_workflow.py --override-gate` with each missing stage named by `--override-stage`, so the block and the override stay observable. Overrides cannot waive source freshness, missing selection, an old generation or pending publication; changing scope requires a fresh user decision. See [subprojects.md](subprojects.md) for paths and handoffs.

## Case status

`python3 scripts/route_workflow.py status --project <slug> --case <id> [--json]` reports `runnable`, `blocked`, `stale` or `not_adopted` routes. It is read-only; gates and authorization stay with the normal route call.

## Routing boundaries

- Market discovery finds problems and segments; idea validation pressure-tests a named idea.
- Brand requests remain independent. Use `brand-identity` (route `standalone-brand`) for identity orchestration and `brand-website-designer-builder` for marketing/corporate sites.
- Use `brand-ui-system` (route `app-ui`) for product dashboards and application screens.
- Former skill names merged into a family skill (for example `brand-designer`) still work as `--intent`; the packet's `alias_note` names the skill and route that now serve them (`route_workflow.SKILL_ALIASES`).
- Use `competitor-research` (route `competitor-analysis`) for competitor pages, not for building a new site.
- Use the website skill's experiment mode for a simple control/treatment test; do not redesign when the user only asks for an experiment.
- Business-position selection/repositioning belongs to `archetype-gtm-strategist` (`--intent business-positioning`, focused positioning mode); a delivery-model request with a selected position belongs to `company-operating-system` (`--intent company-operations`). For compound requests, select the position first and continue only to requested implications. Use explicit intent when context/paraphrases would mislead phrase matching. Marketing-message positioning stays with marketing; standalone branding stays independent.

## Router procedure

1. Normalize the request and inspect only the relevant active manifest.
2. Read repo-root `references/task-scope.md` and run the route command (see Route selection) when intent is understood; add `--project <slug>` whenever the request targets a venture with a business track. Respect exclusions, preserved decisions and new-project boundaries. Use `--continue-workspace` only for an actual continuation. Consult Routing boundaries for ownership; phrase matches are a fallback, not semantic understanding.
3. Require exit 0 before dispatch. If the packet has `gate_blocked: true`, establish segment, journey and pain evidence first (`idea-grill`/evidence collection) or record the user's explicit override.
4. If the result is `business-strategist`, ask one routing question; otherwise dispatch the selected specialist.
5. Pass only the selected specialist's required inputs. Do not preload unrelated research or brand references.
   Load only the additional references the requested stage needs.
   Never promote unapproved artifacts.
6. Record the route, approvals, artifacts, and next action in the controller manifest. Specialist workers write disjoint artifacts and return result packets.

For business-position selection or a coherence review, conditionally use `references/strategic-positioning.md` at repo root. Reuse supplied founder decision context before asking a question; ask one focused question only when a missing objective, role, means, downside, time horizon, or channel constraint would change the comparison. GTM owns position selection; operations derives delivery requirements; marketing and branding consume the selected decision. Reuse the active strategy record and do not reopen strategy for narrow execution requests.

### Router output

Fields: `skill`, `mode`, `matched`, `forbidden_skills`, `prerequisites`, `expected_artifacts`, `estimated_cost`, `approval_required`, `next_action`.

For any strategic recommendation, coach directly: make the first decision explicit as `insufficient_evidence`, `investigate`, `test`, `commit`, `pivot`, `park`, or `stop`; challenge unsupported claims; name the decisive uncertainty and cheapest next test. Do not manufacture encouragement or turn a source summary into a business verdict.

Apply the entrant-success assessment in `references/strategic-positioning.md` at repo root whenever competition influences a recommendation. Before handoff check: served versus saturated; founder-scale customer/economic requirements; concrete acquisition and relationship path; audited evidence; explicit explanation of any ranking change. Confirm requested coverage against completed artifacts. Report partial research when a material requested comparison, source audit, channel review or operator analysis remains unfinished. Test execution and evaluation-fixture validation do not prove strategic quality or live agent behavior.

For a clear idea needing strategy or launch advice, dispatch `precedent-research` (route `business-archetype-playbook-researcher`) for a bounded web/social search of comparable founders and operators before recommending tactics. Reuse existing checked cases where applicable; bring the useful patterns, to-dos and not-to-dos into the selected case's `case_insights.md` and link supporting detail. Do not trigger this study for narrow factual or fixed-scope execution requests.

At a consequential research handoff record the source-audit result (`validate_synthesis.py --require-source-review` with a claim ledger, otherwise a per-source accepted/rejected/unresolved review). Missing review leaves affected conclusions provisional.
