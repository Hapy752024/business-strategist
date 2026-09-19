# Runtime routing boundary

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

## Versioned cases

For a known case add `case` to the checked route envelope and use `--case <id>` in CLI dispatch. The packet includes the registered output root, reviewed assessment revision, source bindings and selected execution binding where required. `case-appraisal` is the bounded opportunity-risk-designer mode; its bare skill alias is now ambiguous. Initial segment/journey/pain research is required, but no passed pain gate or execution selection. Full startup/GTM/pilot and explicitly business-linked design retain their own prerequisites. Standalone design requires no research or migration. See [subprojects.md](subprojects.md) for new paths and optional handoffs.

Case evidence overrides require `override_stages: ["problem_validation", ...]` in the envelope or repeated `--override-stage` flags, alongside the explicit override. They are recorded against the current case revision and selection generation. They cannot waive source freshness, missing selection, an old generation, unknown IDs or pending publication. Changing scope requires a fresh user decision.
