# Agent infrastructure audit — 2026-09-11

Scope: agent instructions, skill discovery/routing, stage-policy enforcement, tests, and applicable external implementations. Existing venture projects were excluded. The checkout already contained substantial changes; this review extends that work without claiming authorship of the pre-existing migration or pain-first policy.

## Decision

Keep the skill-and-script architecture. Its most useful improvements are stricter executable boundaries and regression tests, rather than replacing it with a multi-agent framework. This is an engineering judgment based on the local failures below and the primary sources reviewed. No live research-quality or token-efficiency benchmark was run.

## Findings and changes

| Finding | Change | Boundary |
| --- | --- | --- |
| 39 installed skills, 38 catalog entries; the town curator was missing | Register `town-db-curator`; provide explicit routes for every specialist; preserve the orchestrator's clarification fallback | Direct reachability does not prove natural-language recognition for every paraphrase |
| Several specialists only reachable through prose workflows | Skill-name route IDs for explicit selection; internal brand stages have empty phrase lists to avoid hijacking broad requests | Existing specialist prerequisites still apply |
| No systematic orphan detection | `scripts/validate_skill_routes.py` checks installed/catalog parity, route coverage, missing targets, duplicate IDs and contradictory forbidden lists; required by setup validation | Test fixtures also remove/add skills to demonstrate failures |
| Router could return success for a blocked gate | CLI exits 2 on blocked dispatch; `--check-skill` rejects mismatched or unresolved dispatch | Host must invoke the CLI |
| Some commitment routes omitted the pain gate | Add flags for venture-linked branding, social planning, app/assets, and newly explicit commitment routes | Standalone requests without a business project remain independent |
| A blocked/in-progress conditional gate could unlock work | Gate readers require `status=passed` as well as a passing result; pain-stage transitions enforce this | In-progress conditional competitor analysis remains supported |
| Substring matching accepted misleading evidence paths | Require an existing nonempty file resolving inside the selected workspace's `market_research/pain_points/` directory | This checks placement, not evidence truth, source provenance, or completeness of segment/journey research |
| Overrides could claim success without an audit event | Require an existing readable manifest with an events list; lock and atomically write the override; increment revision before returning success | The caller remains responsible for authentic user authorization |
| Project path traversal/symlinks could redirect override writes | Restrict gate lookup to project slugs and reject symlinked gate components | Not a general filesystem sandbox against hostile concurrent changes |
| Dispatcher instructions contradicted venture-linked gating | Clarify the standalone exception and require dispatch checks | Instructions alone cannot force a host to invoke tools |

## Is routing enforced?

**At the router and configured Claude skill-dispatch boundaries, yes; universally across all tools, no.** The checked dispatcher rejects skill mismatches and gated requests, and CI rejects route/catalog drift. The follow-up now binds `scripts/enforce_skill_route.py` to Claude `PreToolUse` (Skill) and `UserPromptExpansion` (direct slash invocation). An agent with arbitrary shell/file access can still skip these boundaries. No claim of complete runtime mediation is justified.

The mandatory workflow now calls:

```bash
python3 scripts/route_workflow.py "<request>" \
  --intent <route-id> --task-scope <focused|execution|strategy> \
  --check-skill <skill-name> --project <business-project-slug>
```

Omit `--project` for genuinely standalone work. A gate override requires explicit user direction and a successfully recorded event. Route selection is not authorization to spend, publish, contact people, or skip a specialist's prerequisites.

The runtime adapter rejects missing/malformed route metadata, rechecks live gate state, and requires a project or standalone declaration. It preserves normal tool permissions; hook-launch failures exit 2. Identical session/call override deliveries do not duplicate audit events. See [runtime-routing.md](../references/runtime-routing.md) for the invocation contract and direct-slash limitation. Arbitrary shell/file activity, disabled hooks and other hosts remain outside this enforcement boundary. `.claude/settings.json` was updated in the authorized follow-up; existing permission rules were preserved.

## External comparison and adaptation decisions

Primary pages/code reviewed on **2026-09-11**. README claims are treated as described capabilities, not independently reproduced performance.

| Repository/source | Relevant overlap and inspected evidence | Adaptation decision |
| --- | --- | --- |
| [GPT Researcher](https://github.com/assafelovic/gpt-researcher) | General web/local research; inspected [research conductor](https://raw.githubusercontent.com/assafelovic/gpt-researcher/master/gpt_researcher/skills/researcher.py): query planning, task-level visited URLs, MCP caching and research logging | Useful reference for source reuse and per-run accounting. Local collectors already deduplicate queries; do not add another cache without measuring redundant fetches and defining freshness/invalidation |
| [Open Deep Research](https://github.com/langchain-ai/open_deep_research) | General research; inspected [configuration](https://raw.githubusercontent.com/langchain-ai/open_deep_research/main/src/open_deep_research/configuration.py): bounded structured-output retries, research iterations, tool iterations and concurrency | Adapt bounded-loop design when extending autonomous research. No framework migration. GitHub marks this repository archived on 2026-08-21, so treat it as a reference rather than an actively maintained dependency |
| [CompetitiveAnalysisGPT](https://github.com/rohankshir/CompetitiveAnalysisGPT) | Closest narrow competitor-analysis overlap. [README](https://raw.githubusercontent.com/rohankshir/CompetitiveAnalysisGPT/main/README.md) describes company comparison CSVs, source prioritization, maximum turns, and a remaining-information task list | Borrow explicit unresolved-field/task reporting and bounded iterations. Keep this repo's separation of market competitors, analogs and references. README's GPT-4-32k setup indicates an older integration; do not copy its model configuration or quoted costs |
| [CrewAI examples](https://github.com/crewAIInc/crewAI-examples) | [Index](https://raw.githubusercontent.com/crewAIInc/crewAI-examples/main/README.md) includes marketing strategy, landing pages, research/content flows, lead qualification with human review and self-evaluation loops | Useful examples of task/output decomposition; index reviewed, individual flows not executed or deeply audited. No reason established to add CrewAI or additional agents here |
| [younis-ali/market-research-agent](https://github.com/younis-ali/market-research-agent) | README describes generating competitor suggestions from company sector/address and stored seed companies | Reject as an evidence-policy reference: the inspected description does not establish retrieval-backed validation. Functional overlap is insufficient reason to import it |

No third-party code or packages were imported. GPT Researcher presents Apache-2.0 licensing; Open Deep Research and the two narrow market/competitor repositories present MIT licensing. CrewAI's example index directs readers to individual examples for licensing. Any future copied code needs a pinned revision and license/notice review for the exact files.

## Best practices applied or retained

- [Anthropic: Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents), published 2024-12-19, reviewed 2026-09-11: favor simple, composable workflows and explicit checks. Applied through the existing router and stage functions rather than a new orchestration framework.
- [Anthropic: Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents), published 2026-01-09, reviewed 2026-09-11: grade outcomes and trajectories with appropriate deterministic, model and human checks. Applied adversarial tests for actual routing/state mutations; structural checks remain explicitly separate from live agent quality.
- [LangGraph interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts), reviewed 2026-09-11: persistent pause/resume and replay-safe side effects matter. Applied the durable-boundary principle to override recording by using the existing lock and atomic writer. This is a conceptual adaptation, not an implementation of LangGraph interrupts or replay idempotency.

## Follow-up adaptations implemented

- **Bounded collection:** `collect.py --max-http-requests` defaults to 100 shared-helper calls per run. A limit hit preserves completed evidence, stops later providers, marks stage/run state blocked, emits remaining tasks, and returns exit 2. Tests prove the transport is not called beyond the cap. SDK/CLI traffic and implicit redirects are outside this count; it is not a global execution-time or dollar limit.
- **Source reuse:** in-run reuse of identical successful GETs follows explicit positive HTTP max-age, capped at 60 seconds and adjusted for Age. Request headers/credential identity are part of the cache key. The in-memory cache is bounded, cleared after the run, and never persisted. POSTs, errors and non-cacheable responses are not reused. `--fresh-http` disables reuse. Tests demonstrate one avoided call for an eligible repeat; no production savings claim is made.
- **Unresolved work:** collection summaries now carry `remaining_tasks` and `collection_complete`; human reports include the same provider/quality gaps. Credit failures prescribe user resolution rather than automatic retries. These fields are workflow signals, not source-truth grading.
- **Dispatch adapter:** tests execute both configured hook commands from a nested directory, test direct slash invocation, malformed inputs, route mismatch, changed gate state, standalone conflicts and replayed overrides. No framework or third-party package was added.

These are selective implementations of the bounded-loop, source-reuse, unresolved-task and durable-boundary ideas above. No external code was copied. The hook API was checked against the [official Claude Code hook reference](https://code.claude.com/docs/en/hooks) on 2026-09-11; installed CLI version was 2.1.233.

## Validation and remaining limits

- Full Python suite: **269 passed**.
- `bash scripts/validate_setup.sh`: **0 errors**; includes full Python suite, repeated offline route scenarios, process-comparison checks, eval structure and fixture contract.
- Skill-route coverage validator: passed; all **39 installed skills** covered through explicit routes or the orchestrator fallback.
- Dispatcher skill quick validation: structurally valid; `git diff --check`: clean.
- Existing town-curator warnings remain: missing Quality Checklist guidance and no skill-local `evals.json`. Its routing now has executable regression coverage; domain workflow quality was outside this infrastructure pass.
- Configured hook subprocess behavior is tested. Live model-driven Claude dispatch and Codex/OpenCode runtime enforcement, research quality, source truth and production token savings remain unverified. Setup tests are not evidence that every runtime path is mediated or every research claim is supported.
