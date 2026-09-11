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

Use `"standalone": true` instead of `project` for genuinely independent work. Exactly one is required. This declaration is supplied by the calling agent using the user's scope; do not ask the user for technical JSON. Resolve missing venture/standalone context in normal conversation before dispatch. A business workspace detected from the current directory cannot be silently reclassified as standalone. Unknown route IDs, mismatched skills, malformed metadata and blocked gates deny dispatch. Skill-tool calls receive `input` as their ordinary arguments after checking; metadata is kept out of the specialist task.

Direct repository slash invocations currently need the same envelope; if absent they stop with a routing explanation. Users can use the `business-strategist` entrypoint with natural language to have the agent prepare the envelope. Foreign plugin slash commands are unaffected.

`override_gate: true` is only for an explicit user override already given in the conversation. It uses the existing manifest audit writer. Session/call identity makes redelivery of an override idempotent. An audit record is not proof of user authorization or that the specialist subsequently executed.

The host wrapper turns script/import errors into blocking exit 2. Hook output tests and configured-command subprocess tests cover both invocation paths. This is **skill-dispatch enforcement**, not complete tool mediation: shell commands, direct file reads/writes, disabled hooks, other hosts and foreign skills remain outside this boundary. Do not claim it prevents a hostile agent with filesystem access from bypassing policy. Specialist prerequisites and paid-provider permissions remain separately applicable.

Codex/OpenCode and ordinary shell callers retain the portable `route_workflow.py --check-skill` contract. No cross-host runtime enforcement is claimed.

Hook contract source: [Claude Code hooks reference](https://code.claude.com/docs/en/hooks), checked 2026-09-11. Local CLI version checked: 2.1.233. Live model dispatch has not been benchmarked.
