# Review Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the findings of the 2026-09-24 setup and content review: green CI, a leaner and consistent harness, a smoke-test-to-interview validation path, an explicit viability verdict, verbal identity and legal checks in branding, and concrete paid/organic marketing outputs with real cross-module handoffs.

**Architecture:** The repository stays a Claude Code skill set with a Python router and JSON catalog. Fixes are grouped in five phases: (0) stabilize the red suite and commit the working tree, (1) harness hygiene (hooks, dispatch errors, instruction size, subagents, permissions, evals), (2) business validation content (smoke-test mode, validation page, responder intake, viability criterion, scorecard), (3) branding content (verbal identity, naming and legal checks, lean default), (4) marketing and handoffs (asset briefs, paid planning, keyword research, handoff contract). Every task ends with the repo validators green.

**Tech Stack:** Python 3 (stdlib only for new scripts), pytest, JSON Schema draft 2020-12, Claude Code hooks/skills/subagents, Markdown references.

**Spec:** The review delivered in chat on 2026-09-24 (this plan restates each finding at the top of the task that fixes it). Paid customer-evidence API spend is pre-authorized by the founder; advertising spend, deployments, external connections and FAL generation still need explicit approval.

## Global Constraints

- `bash scripts/validate_setup.sh`, `python3 scripts/validate_skill_routes.py`, `python3 scripts/run_evals.py` and `python3 -m pytest -q -p no:cacheprovider` must pass at the end of every task.
- Every installed skill under `.agents/skills/` must stay in `config/skill-catalog.json` and be reachable via `config/workflow-routes.json` (enforced by `tests/test_skill_route_coverage.py`).
- SKILL.md descriptions stay under 240 characters and contain only what the skill does and when to use it.
- New scripts use the Python standard library only; no new pip dependencies.
- New references use forward-slash relative paths and are linked directly from the owning SKILL.md.
- Do not touch anything under `projects/`.
- Commit after every task with a conventional-commit message ending in `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`.
- Never weaken the pain-first gate, the no-participant-payment rule, or the ad-spend/deployment authorization requirements.

---

## Phase 0 — Stabilize

### Task 1: Keep module references out of `required_references`

**Finding:** Six tests in `tests/test_customer_voice_routing.py` fail because the uncommitted router change appends the module reference (`references/modules/research.md`) to `required_references`. The packet already carries it separately as `module_reference`.

**Files:**
- Modify: `scripts/route_workflow.py:320-327`
- Test: `tests/test_customer_voice_routing.py` (existing, should pass unchanged)
- Test: `tests/test_runtime_routing.py` (add one assertion)

**Interfaces:**
- Produces: route packet keys `module`, `module_reference`, `quality_reference` unchanged; `required_references` now contains only skill/mode references.

- [ ] **Step 1: Run the failing tests to confirm the symptom**

Run: `python3 -m pytest -q -p no:cacheprovider tests/test_customer_voice_routing.py`
Expected: 6 FAIL with `assert ['references/customer-voice.md', 'references/modules/research.md'] == ['references/customer-voice.md']`

- [ ] **Step 2: Add a regression test that the module reference stays separate**

Append to `tests/test_runtime_routing.py`:

```python
def test_module_reference_is_separate_from_required_references():
    from scripts import route_workflow
    packet = route_workflow.route_request('collect customer voice', intent='evidence-scout',
                                         task_scope='focused', check_skill='evidence-scout')
    assert packet['module'] == 'research'
    assert packet['module_reference'] == 'references/modules/research.md'
    assert 'references/modules/research.md' not in packet['required_references']
```

- [ ] **Step 3: Remove the append in the router**

In `scripts/route_workflow.py` replace:

```python
        packet['quality_reference'] = modules[module_name].get('quality_reference')
        packet['required_references'] = list(dict.fromkeys(packet['required_references'] +
            checked_references({'required_references': [module_reference]}, CATALOG_PATH.parent.parent)))
```

with:

```python
        packet['quality_reference'] = modules[module_name].get('quality_reference')
        # Module references travel in their own key; required_references stays skill/mode scoped.
        checked_references({'required_references': [module_reference]}, CATALOG_PATH.parent.parent)
```

(The call keeps the fail-closed check that the module file exists and is non-empty.)

- [ ] **Step 4: Run the suite and grep for other tests that expected the old behaviour**

Run: `grep -rn "modules/research.md\|modules/branding.md\|modules/marketing.md\|modules/website.md" tests/ | grep -v module_reference`
Then: `python3 -m pytest -q -p no:cacheprovider`
Expected: all pass. If a test asserts the module path inside `required_references`, change that assertion to read `packet['module_reference']` instead.

- [ ] **Step 5: Commit**

```bash
git add scripts/route_workflow.py tests/test_runtime_routing.py tests/
git commit -m "fix(router): keep module references out of required_references"
```

### Task 2: Make the marketing-workstream test order-independent

**Finding:** `tests/test_gap_closure.py::test_marketing_workstream_publishes_bound_outputs_and_blocks_changed_import` fails in the full run but passes alone, so it leaks or depends on state.

**Files:**
- Modify: `tests/test_gap_closure.py:71-110`
- Possibly modify: `scripts/subprojects.py` (only if a module-level cache is found)

- [ ] **Step 1: Reproduce the order dependence**

Run: `python3 -m pytest -q -p no:cacheprovider tests/test_customer_voice_routing.py tests/test_gap_closure.py -k "marketing_workstream or customer_voice"`
Expected: FAIL. Then run with `-p no:randomly --tb=long` and read the first assertion that differs from the isolated run.

- [ ] **Step 2: Move the `monkeypatch.setattr(routing, 'ROOT', tmp_path)` to the top of the test**

The test writes the workspace under `tmp_path` before patching `routing.ROOT`, so any helper that consulted `routing.ROOT` during publish saw the real repo root. Move line 95 (`monkeypatch.setattr(routing, 'ROOT', tmp_path)`) to directly after line 72 (`root = tmp_path / 'projects/marketing-lifecycle'`).

- [ ] **Step 3: Look for module-level caches**

Run: `grep -n "^_[a-z_]* *= *{}\|lru_cache\|^[A-Z_]* *= *json.loads" scripts/subprojects.py scripts/route_workflow.py scripts/case_workspace.py`
If a cache keyed by path exists, add an autouse fixture in `tests/conftest.py` that clears it:

```python
import pytest
from scripts import route_workflow

@pytest.fixture(autouse=True)
def _reset_router_caches():
    for name in ('_ROUTES_CACHE', '_CATALOG_CACHE'):
        if hasattr(route_workflow, name):
            getattr(route_workflow, name).clear()
    yield
```

(Use the actual cache names found by the grep; delete this fixture if the grep finds none.)

- [ ] **Step 4: Run the full suite three times**

Run: `for i in 1 2 3; do python3 -m pytest -q -p no:cacheprovider || break; done`
Expected: 3 green runs.

- [ ] **Step 5: Commit**

```bash
git add tests/test_gap_closure.py tests/conftest.py
git commit -m "test: make marketing workstream lifecycle test order-independent"
```

### Task 3: Commit the outstanding working tree in logical slices

**Finding:** 108 uncommitted changes including a deleted skill; CI cannot be trusted until this lands.

**Files:**
- All currently modified/deleted paths reported by `git status --short`.

- [ ] **Step 1: Confirm green**

Run: `bash scripts/validate_setup.sh && python3 scripts/validate_skill_routes.py && python3 scripts/run_evals.py`
Expected: `0 error(s)`, `"passed": true`, `All eval structure checks passed`.

- [ ] **Step 2: Commit the town-db removal on its own**

```bash
git add -A .agents/skills/town-db-curator scripts/town_db .gitignore
git commit -m "chore: remove town-db curator skill and scripts from the shared skill set"
```

- [ ] **Step 3: Commit the research-quality work**

```bash
git add .agents/skills/evidence-scout .agents/skills/idea-grill .agents/skills/market-problem-discovery \
  scripts/evidence_scout schemas references/subprojects.md templates/project/market-discovery-report.md \
  config/skill-catalog.json config/workflow-routes.json scripts/route_workflow.py scripts/enforce_skill_route.py \
  scripts/validate_skill_routes.py scripts/subprojects.py scripts/validate_apis/common.py AGENTS.md
git commit -m "feat(research): module contracts, pain-query calibration and route validation updates"
```

- [ ] **Step 4: Commit hooks, settings and tests**

```bash
git add .claude tests docs
git commit -m "chore: hook, settings, test and doc updates from the research-quality round"
```

- [ ] **Step 5: Verify a clean tree**

Run: `git status --short | wc -l`
Expected: `0`

---

## Phase 1 — Harness hygiene

### Task 4: Hook timeouts in seconds

**Finding:** Claude Code hook `timeout` is in seconds. Four lifecycle hooks are set to `5000` (83 minutes); intended value was milliseconds.

**Files:**
- Modify: `.claude/settings.json` (four `"timeout": 5000` entries)
- Test: `tests/test_claude_hooks.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_claude_hooks.py`:

```python
def test_hook_timeouts_are_seconds_and_bounded():
    settings = json.loads((ROOT / ".claude/settings.json").read_text())
    for event, entries in settings["hooks"].items():
        for entry in entries:
            for hook in entry["hooks"]:
                assert 1 <= hook["timeout"] <= 60, f"{event}: timeout {hook['timeout']} is not a sane number of seconds"
```

- [ ] **Step 2: Run it to see it fail**

Run: `python3 -m pytest -q -p no:cacheprovider tests/test_claude_hooks.py::test_hook_timeouts_are_seconds_and_bounded`
Expected: FAIL on `PreCompact: timeout 5000`

- [ ] **Step 3: Fix the values**

Run: `sed -i 's/"timeout": 5000/"timeout": 15/g' .claude/settings.json`
Then confirm: `grep -c '"timeout": 15' .claude/settings.json` prints `4`.

- [ ] **Step 4: Run the hook tests**

Run: `python3 -m pytest -q -p no:cacheprovider tests/test_claude_hooks.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add .claude/settings.json tests/test_claude_hooks.py
git commit -m "fix(hooks): express lifecycle hook timeouts in seconds"
```

### Task 5: Actionable skill-dispatch denial

**Finding:** Plain-text args to a repo skill are denied with `JSONDecodeError: Expecting value...` and no hint of the envelope. Logged unfixed since 2026-09-11 in `docs/to_be_improved.md`.

**Files:**
- Modify: `scripts/enforce_skill_route.py:33-37`
- Modify: `docs/to_be_improved.md` (mark the entry resolved)
- Test: `tests/test_runtime_routing.py`

**Interfaces:**
- Produces: denial reason string starting with `Repository skill dispatch requires a JSON route envelope` and containing the literal template `{"route": {"request": ..., "intent": "<skill>", "task_scope": "focused|execution|strategy", "project": "<slug>" | "standalone": true}, "input": ...}`.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_runtime_routing.py`:

```python
import subprocess, json as _json
from pathlib import Path as _Path

def test_plain_text_args_get_an_actionable_envelope_hint():
    hook = _Path(__file__).resolve().parents[1] / 'scripts/enforce_skill_route.py'
    event = {"hook_event_name": "PreToolUse", "tool_name": "Skill",
             "tool_input": {"skill": "idea-grill", "args": "validate my dog grooming idea"}}
    out = subprocess.run(["python3", str(hook)], input=_json.dumps(event), text=True, capture_output=True, check=True)
    decision = _json.loads(out.stdout)["hookSpecificOutput"]
    assert decision["permissionDecision"] == "deny"
    reason = decision["permissionDecisionReason"]
    assert "JSON route envelope" in reason
    assert '"intent": "idea-grill"' in reason
    assert "references/runtime-routing.md" in reason
    assert "JSONDecodeError" not in reason
```

- [ ] **Step 2: Run it to see it fail**

Run: `python3 -m pytest -q -p no:cacheprovider tests/test_runtime_routing.py::test_plain_text_args_get_an_actionable_envelope_hint`
Expected: FAIL (`"JSON route envelope" in reason` is false)

- [ ] **Step 3: Implement the hint**

In `scripts/enforce_skill_route.py` replace:

```python
    args = event.get('command_args', '') if expansion else tool_input.get('args', '')
    envelope = json.loads(args)
    if not isinstance(envelope, dict) or not isinstance(envelope.get('route'), dict):
        raise ValueError('Repository skill dispatch requires a route envelope; see references/runtime-routing.md')
```

with:

```python
    args = event.get('command_args', '') if expansion else tool_input.get('args', '')
    try:
        envelope = json.loads(args) if isinstance(args, str) and args.strip() else None
    except json.JSONDecodeError:
        envelope = None
    if not isinstance(envelope, dict) or not isinstance(envelope.get('route'), dict):
        raise ValueError(envelope_hint(name, args if isinstance(args, str) else ''))
```

and add above `check_dispatch`:

```python
def envelope_hint(skill: str, raw_args: str) -> str:
    request = raw_args.strip().replace('"', "'")[:160] or '<one-sentence request>'
    template = ('{"route": {"request": "%s", "intent": "%s", "task_scope": "focused|execution|strategy", '
                '"project": "<slug>" | "standalone": true}, "input": "<specialist brief>"}') % (request, skill)
    return ('Repository skill dispatch requires a JSON route envelope in args. Re-invoke the skill with: '
            + template + ' . See references/runtime-routing.md. Plain text was received.')
```

- [ ] **Step 4: Run the routing tests**

Run: `python3 -m pytest -q -p no:cacheprovider tests/test_runtime_routing.py tests/test_claude_hooks.py`
Expected: PASS

- [ ] **Step 5: Close the to-be-improved entry**

In `docs/to_be_improved.md`, under the `2026-09-11 - Skill-Dispatch Error Message Not Actionable` heading, prepend the line: `Resolved 2026-09-24: enforce_skill_route.py now returns the envelope template with the skill name pre-filled.`

- [ ] **Step 6: Commit**

```bash
git add scripts/enforce_skill_route.py tests/test_runtime_routing.py docs/to_be_improved.md
git commit -m "fix(dispatch): return the route-envelope template when skill args are not JSON"
```

### Task 6: Simplify the SubagentStop hook

**Finding:** The hook blocks only on fewer than 20 characters and warns on words like "definitely". The word heuristics add noise and never block.

**Files:**
- Modify: `.claude/hooks/subagent_stop.py:25-75`
- Test: `tests/test_claude_hooks.py:80-95` (existing contract test must still pass)

- [ ] **Step 1: Add a test that warnings do not appear for confident but sourced output**

Append to `tests/test_claude_hooks.py`:

```python
def test_subagent_stop_does_not_flag_word_choice():
    hook = ROOT / ".claude/hooks/subagent_stop.py"
    out = subprocess.run(["python3", str(hook)],
        input=json.dumps({"agent_type": "researcher",
                          "last_assistant_message": "This is definitely sourced: https://example.com/a and artifacts/evidence.jsonl"}),
        text=True, capture_output=True, check=True)
    assert json.loads(out.stdout) == {}
```

- [ ] **Step 2: Run to confirm it already passes (the hook prints `{}` on accept) and then simplify**

Replace `validate_subagent_output` with:

```python
def validate_subagent_output(output_text: str) -> dict:
    """Block only empty output; everything else is the coordinator's job to judge."""
    if not output_text or len(output_text.strip()) < 20:
        return {"valid": False, "reason": "Subagent output is empty or too short.", "findings": []}
    return {"valid": True, "reason": "Output present.", "findings": []}
```

Delete the `hallucination_markers`, `confidence_markers`, `has_citation`, `has_file_path`, `has_evidence_separation` blocks and the unused `detail` variable in `main()`.

- [ ] **Step 3: Run the hook tests**

Run: `python3 -m pytest -q -p no:cacheprovider tests/test_claude_hooks.py`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add .claude/hooks/subagent_stop.py tests/test_claude_hooks.py
git commit -m "refactor(hooks): SubagentStop blocks only empty output"
```

### Task 7: Remove duplicate frontmatter and copy-pasted success criteria

**Finding:** 12 `references/workflow.md` files start with a second, older `name:/description:` frontmatter that contradicts the SKILL.md description. 11 brand workflow files contain the identical "Triggers on >=90%... <=15 tool calls" block and nested `# Imported workflow / ## Procedure / # Brand X` headings.

**Files:**
- Modify: `.agents/skills/{competitor-marketing-analyzer,competitor-monitoring,competitor-scout,evidence-scout,growth-case-analyzer,idea-grill,interview-bridge,market-problem-discovery,marketing-strategy-builder,saas-fintech-pilot-designer,social-digital-marketing-planner,startup-business-builder}/references/workflow.md`
- Modify: `.agents/skills/brand-{asset-producer,discovery-interviewer,exporter,frontend-app-designer,guideline-researcher,guidelines-writer,quality-reviewer,strategy-director,typography-researcher,ui-kit-producer,workspace-manager}/references/workflow.md`
- Create: `tests/test_skill_hygiene.py`

- [ ] **Step 1: Write the failing hygiene test**

Create `tests/test_skill_hygiene.py`:

```python
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / '.agents/skills'


def test_reference_files_have_no_frontmatter():
    offenders = [p for p in SKILLS.glob('*/references/*.md') if p.read_text().lstrip().startswith('---\nname:')]
    assert offenders == [], f'reference files must not carry skill frontmatter: {offenders}'


def test_no_copy_pasted_success_criteria_boilerplate():
    offenders = [p for p in SKILLS.rglob('*.md') if 'Triggers on >=90%' in p.read_text()]
    assert offenders == [], offenders


def test_no_nested_imported_workflow_headings():
    offenders = [p for p in SKILLS.glob('*/references/workflow.md') if '# Imported workflow' in p.read_text()]
    assert offenders == [], offenders


def test_skill_descriptions_are_compact():
    for skill in SKILLS.glob('*/SKILL.md'):
        text = skill.read_text()
        desc = re.search(r'^description:\s*(.+)$', text, re.M).group(1)
        assert len(desc) <= 240, f'{skill.parent.name}: description is {len(desc)} chars'
```

- [ ] **Step 2: Run it to see the three failures**

Run: `python3 -m pytest -q -p no:cacheprovider tests/test_skill_hygiene.py`
Expected: 3 FAIL (frontmatter, boilerplate, nested headings); descriptions pass.

- [ ] **Step 3: Strip the frontmatter blocks**

Run:

```bash
for s in competitor-marketing-analyzer competitor-monitoring competitor-scout evidence-scout growth-case-analyzer idea-grill interview-bridge market-problem-discovery marketing-strategy-builder saas-fintech-pilot-designer social-digital-marketing-planner startup-business-builder; do
  f=.agents/skills/$s/references/workflow.md
  python3 - "$f" <<'EOF'
import sys, re
p = sys.argv[1]; t = open(p).read()
t2 = re.sub(r'\A---\n.*?\n---\n\n?', '', t, count=1, flags=re.S)
open(p, 'w').write(t2)
EOF
done
```

Then open each file and confirm it starts with its `# ... Workflow` heading.

- [ ] **Step 4: Remove the boilerplate and nested headings from the brand workflows**

For each of the 11 brand files, delete the `## Success Criteria` section (from that heading up to but not including the first rule line, e.g. `Ask exactly one question at a time.` or `Use SVG/vector masters first.`), and replace the three opening lines

```
# Imported workflow

## Procedure

# Brand Exporter
```

with the single heading `# Brand Exporter Workflow` (use each skill's own title). Keep the trailing `## Output` and `## Quality Checklist` sections only if they contain a rule specific to that skill; delete them when they are the generic "Follow the output contract described by this skill and preserve provenance." / "Run the skill's existing checks..." text, because SKILL.md already says this.

- [ ] **Step 5: Run hygiene, route validation and the full suite**

Run: `python3 -m pytest -q -p no:cacheprovider tests/test_skill_hygiene.py && python3 scripts/validate_skill_routes.py && python3 -m pytest -q -p no:cacheprovider`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add .agents/skills tests/test_skill_hygiene.py
git commit -m "chore(skills): remove duplicate frontmatter and copy-pasted boilerplate from workflow references"
```

### Task 8: Resolve the paid-spend contradiction

**Finding:** AGENTS.md pre-authorizes paid customer-evidence API spend; `.agents/skills/business-strategist/SKILL.md:16` requires approval before paid providers. The founder confirms customer-evidence APIs are pre-authorized.

**Files:**
- Modify: `.agents/skills/business-strategist/SKILL.md:16`
- Test: `tests/test_skill_hygiene.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_skill_hygiene.py`:

```python
def test_no_skill_requires_approval_for_pre_authorized_customer_evidence_apis():
    offenders = [p for p in SKILLS.rglob('*.md')
                 if re.search(r'approval before paid providers|approve.{0,40}paid (evidence|customer)', p.read_text(), re.I)]
    assert offenders == [], offenders
```

- [ ] **Step 2: Run it to see it fail**

Run: `python3 -m pytest -q -p no:cacheprovider tests/test_skill_hygiene.py -k pre_authorized`
Expected: FAIL listing `business-strategist/SKILL.md`

- [ ] **Step 3: Rewrite the rule**

In `.agents/skills/business-strategist/SKILL.md` replace

```
- Require explicit approval before paid providers, external connections, analytics, experiments, commits to another repository, or deployment.
```

with

```
- Paid customer-evidence API spend is pre-authorized (see AGENTS.md Provider Policy). Require explicit approval before advertising or recruitment spend, paid asset generation, external connections, analytics activation, live experiments, commits to another repository, or deployment.
```

- [ ] **Step 4: Grep the rest of the repo for the same contradiction**

Run: `grep -rn -i "approval before paid\|approve paid provider" references/ .agents/skills/ AGENTS.md`
Expected: no output. Fix any hit the same way.

- [ ] **Step 5: Run tests and commit**

```bash
python3 -m pytest -q -p no:cacheprovider tests/test_skill_hygiene.py
git add .agents/skills/business-strategist/SKILL.md tests/test_skill_hygiene.py
git commit -m "docs(router): align paid-provider rule with pre-authorized customer-evidence spend"
```

### Task 9: Slim AGENTS.md to always-true rules

**Finding:** AGENTS.md is about 2,700 words; Claude Code docs target under 200 lines per instruction file and say longer files reduce adherence. Commands, provider mechanics, output layouts and infrastructure belong in references.

**Files:**
- Modify: `AGENTS.md`
- Create: `references/operating-guide.md` (moved sections)
- Modify: `CLAUDE.md` (add pointer)
- Test: `tests/test_skill_hygiene.py`

**Interfaces:**
- Produces: `references/operating-guide.md` with headings `## Commands`, `## Provider Policy`, `## Outputs`, `## Infrastructure`, `## Community discovery and promotion`; AGENTS.md links to it.

- [ ] **Step 1: Write the failing size test**

Append to `tests/test_skill_hygiene.py`:

```python
def test_agents_md_stays_within_instruction_budget():
    lines = (ROOT / 'AGENTS.md').read_text().splitlines()
    assert len(lines) <= 200, f'AGENTS.md has {len(lines)} lines; move procedures to references/operating-guide.md'
    assert 'references/operating-guide.md' in (ROOT / 'AGENTS.md').read_text()
```

- [ ] **Step 2: Run it to see it fail**

Run: `python3 -m pytest -q -p no:cacheprovider tests/test_skill_hygiene.py -k budget`

- [ ] **Step 3: Move procedure sections verbatim**

Create `references/operating-guide.md` starting with:

```markdown
# Operating guide

Procedures moved out of AGENTS.md on 2026-09-24. AGENTS.md keeps the rules that apply in every session; this file keeps commands, provider mechanics, output layouts and infrastructure pointers. Read the section you need.
```

Then cut these AGENTS.md sections into it unchanged: `## Commands`, `## Provider Policy` (keep only the two-line summary below in AGENTS.md), `## Outputs`, `## Infrastructure`, and the two long community-promotion / freshness-recheck bullets from Commands.

- [ ] **Step 4: Rewrite AGENTS.md to rules only**

AGENTS.md keeps, in this order, each trimmed to rule statements:
1. `# Evidence Scout Agent Set` one-paragraph purpose.
2. `## Operating Stance` (recruitment without payment; truthfulness; pain-first rule; evidence-first rule). Keep as is, these are rules.
3. `## Workspace Lifecycle` reduced to: run the existing `ls -d projects/...` command, present found workspaces as numbered options, ask exactly one question; link `references/workspace-lifecycle.md`.
4. `## Workflow` reduced to the mode selection (discovery vs validation vs ambiguous), the core sequence list, the route-before-dispatch rule (`scripts/route_workflow.py --intent --task-scope --check-skill`, exit 2 stops), and the subproject independence rule. Remove sentences that restate reference contents.
5. `## Provider Policy` two lines: "Paid customer-evidence API spend is pre-authorized with no cap; ad spend, paid asset generation and deployment need explicit approval. Credit failures are coverage gaps, never absence of demand. Details: `references/operating-guide.md`."
6. `## Where things live` five bullets: skills `.agents/skills/`, shared references `references/`, catalog/routes `config/`, procedures `references/operating-guide.md`, lifecycle `references/workspace-lifecycle.md`.

Target: under 200 lines. Check with `wc -l AGENTS.md`.

- [ ] **Step 5: Verify no link broke**

Run:

```bash
python3 - <<'EOF'
import re, os
for f in ['AGENTS.md', 'references/operating-guide.md']:
    for p in set(re.findall(r'`((?:\.agents/|references/|scripts/|config/|schemas/|templates/|docs/|\.claude/)[^`\s*<>]+)`', open(f).read())):
        print(('OK  ' if os.path.exists(p.split(' ')[0]) else 'MISS'), f, p)
EOF
```

Expected: only `MISS ... references/workflow.md` (that is the relative "selected skill's references/workflow.md" phrase; reword it to "the selected skill's own `references/workflow.md`" so the checker no longer treats it as a root path).

- [ ] **Step 6: Run everything and commit**

```bash
python3 -m pytest -q -p no:cacheprovider && bash scripts/validate_setup.sh
git add AGENTS.md CLAUDE.md references/operating-guide.md tests/test_skill_hygiene.py
git commit -m "docs: slim AGENTS.md to always-true rules; move procedures to references/operating-guide.md"
```

### Task 10: Permission allowlist for read-only and pre-authorized scripts

**Finding:** Only three repo scripts are allowlisted, so every research or validation command prompts.

**Files:**
- Modify: `.claude/settings.json` `permissions.allow`
- Test: `tests/test_claude_hooks.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_claude_hooks.py`:

```python
def test_read_only_and_preauthorized_scripts_are_allowlisted():
    settings = json.loads((ROOT / ".claude/settings.json").read_text())
    allow = set(settings["permissions"]["allow"])
    for rule in [
        "Bash(python3 scripts/route_workflow.py *)",
        "Bash(python3 scripts/validate_skill_routes.py)",
        "Bash(python3 scripts/run_evals.py *)",
        "Bash(python3 -m pytest *)",
        "Bash(bash scripts/validate_setup.sh)",
        "Bash(python3 scripts/case_economics.py *)",
        "Bash(python3 scripts/strategy_review.py *)",
        "Bash(python3 scripts/serper_fetch.py *)",
        "Bash(python3 scripts/evidence_scout/collect.py *)",
        "Bash(python3 scripts/evidence_scout/discover_market_problems.py *)",
        "Bash(python3 scripts/evidence_scout/plan_customer_feedback.py *)",
        "Bash(python3 scripts/evidence_scout/build_interview_kit.py *)",
    ]:
        assert rule in allow, rule
    assert "Bash(python3 scripts/brand/website_launch.py *)" not in allow
    assert "Bash(python3 scripts/fal_assets.py *)" not in allow
```

- [ ] **Step 2: Add the rules**

Insert the twelve `Bash(...)` strings from the test into the `allow` array after `"Bash(python3 scripts/validate_setup.sh)"`. Also delete the stale entry `"Bash(python3 scripts/validate_setup.sh)"` (it is a bash script) and keep `"Bash(bash scripts/validate_setup.sh)"`.

- [ ] **Step 3: Validate and commit**

```bash
python3 -c "import json; json.load(open('.claude/settings.json'))" && python3 -m pytest -q -p no:cacheprovider tests/test_claude_hooks.py
git add .claude/settings.json tests/test_claude_hooks.py
git commit -m "chore(settings): allowlist read-only validators and pre-authorized evidence scripts"
```

### Task 11: Research subagents and parallel VOC collection

**Finding:** No `.claude/agents/` definitions exist; heavy provider output lands in the main context; topic-led and entity-led VOC passes and competitor lanes run sequentially. `agent-modes/` duplicates this intent without enforcement.

**Files:**
- Create: `.claude/agents/evidence-researcher.md`
- Create: `.claude/agents/competitor-researcher.md`
- Create: `.claude/agents/brand-critic.md`
- Modify: `.agents/skills/evidence-scout/references/workflow.md` (add "Parallel collection" section)
- Modify: `.agents/skills/competitive-landscape-builder/references/workflow.md` (add one paragraph)
- Delete: `agent-modes/` (three files)
- Modify: `references/workspace-lifecycle.md:147` and `references/operating-guide.md` (remove agent-modes mentions)
- Test: `tests/test_claude_hooks.py`

**Interfaces:**
- Produces: subagent names `evidence-researcher`, `competitor-researcher`, `brand-critic` usable via the Agent tool; coordinators pass a packet shaped by `references/modules/source-worker-packet.md`.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_claude_hooks.py`:

```python
def test_project_subagents_exist_with_restricted_tools():
    import re
    agents = ROOT / ".claude/agents"
    for name, must_have, must_not in [
        ("evidence-researcher", "Bash", "Write"),
        ("competitor-researcher", "Bash", "Write"),
        ("brand-critic", "Read", "Bash"),
    ]:
        text = (agents / f"{name}.md").read_text()
        front = text.split("---")[1]
        assert re.search(rf"^name:\s*{name}\s*$", front, re.M)
        tools = re.search(r"^tools:\s*(.+)$", front, re.M).group(1)
        assert must_have in tools and must_not not in tools, f"{name}: tools={tools}"
    assert not (ROOT / "agent-modes").exists(), "agent-modes/ is superseded by .claude/agents/"
```

- [ ] **Step 2: Create the researcher agents**

`.claude/agents/evidence-researcher.md`:

```markdown
---
name: evidence-researcher
description: Runs one bounded customer-voice collection packet (topic-led or entity-led) with repository scripts and returns a short sourced handoff. Use for parallel VOC collection; never for synthesis.
tools: Read, Grep, Glob, Bash, WebFetch, WebSearch
model: sonnet
maxTurns: 40
---

You execute exactly one source worker packet (see references/modules/source-worker-packet.md). Read the packet's question, scope, allowed providers, allocation and output directory before running anything.

Rules:
- Use only `python3 scripts/evidence_scout/*.py`, `python3 scripts/serper_fetch.py` and read-only shell. Never edit files outside your exclusive output directory.
- Paid customer-evidence APIs are pre-authorized. On `insufficient_credits`/`billing_required`, record the gap in your handoff and continue with fallbacks.
- Record every attempted query, provider status, and source locator. Separate customer voice from supplier voice and quoted third parties.
- Do not synthesize, rank, or decide. Do not treat retrieval failure as absence of demand.

Return, in under 400 words: output directory, providers attempted/failed, record counts by source role, the five most consequential source locators with dates, counter-evidence seen, duplicates against the packet's known sources, and open questions.
```

`.claude/agents/competitor-researcher.md`:

```markdown
---
name: competitor-researcher
description: Verifies one lane of competitor candidates (market, analog, or capability reference) with repository scripts and returns a classified, sourced handoff. Use for parallel competitor discovery; never for positioning decisions.
tools: Read, Grep, Glob, Bash, WebFetch, WebSearch
model: sonnet
maxTurns: 40
---

You verify one competitor lane only. Inputs: lane name, candidate list or discovery query, market/locale, exclusive output directory.

Rules:
- Use `python3 scripts/evidence_scout/discover_competitors.py` and `analyze_competitor_marketing.py`; write only inside your output directory.
- For every candidate record: official URL checked, date, offer summary, visible prices (raw token and normalized), public social handles, evidence that it serves the same job for the same segment, and false-positive reasons.
- Supplier copy is a claim, not proof of performance. Do not infer demand or saturation.

Return under 400 words: verified candidates with locators, rejected candidates with reasons, coverage gaps, and unresolved identity matches.
```

`.claude/agents/brand-critic.md`:

```markdown
---
name: brand-critic
description: Independent reviewer of brand or website outputs against brief, accessibility, consistency and legal-check criteria. Use for the finalization gate; it reads and reports, it never edits.
tools: Read, Grep, Glob, WebFetch
model: opus
maxTurns: 25
---

Review the named brand or website package without the creator's rationale. Apply `.agents/skills/brand-quality-reviewer/references/review-checklist.md` and `best-practices-guidelines.md`.

Report findings first, ordered HIGH, MEDIUM, LOW, each with file path, the criterion violated, and a concrete fix. Check specifically: WCAG AA contrast on every text/background pair in tokens; monochrome and 16px legibility of the mark; recorded trademark similarity search and human vector-edit pass; guideline completeness; stale stage/archive paths. End with one of: approve, fix, request revision, accept residual risk.
```

- [ ] **Step 3: Add the parallel collection section to evidence-scout**

Append to `.agents/skills/evidence-scout/references/workflow.md`:

```markdown
## Parallel collection with subagents

When the topic-led and entity-led frames, or several locales, are independent, dispatch one `evidence-researcher` subagent per packet using `references/modules/source-worker-packet.md`. Give each an exclusive output directory under the run (`<run>/workers/<packet-id>/`) and disjoint query IDs. Wait for all handoffs, then verify sources, deduplicate shared incidents, and own the synthesis yourself. Agreement between workers is not independent evidence. Never let a worker edit `evidence.jsonl`, source reviews, syntheses or manifests.
```

Add the equivalent paragraph (with `competitor-researcher`, one per lane) to `.agents/skills/competitive-landscape-builder/references/workflow.md`, and a one-line note in `.agents/skills/brand-quality-reviewer/references/workflow.md` replacing "If subagents are available, ask one critic subagent..." with "Dispatch the `brand-critic` subagent for the independent pass."

- [ ] **Step 4: Remove agent-modes**

```bash
git rm -r agent-modes
grep -rn "agent-modes" --include=*.md . --exclude-dir=projects --exclude-dir=docs
```

Edit every hit (expected: `references/workspace-lifecycle.md`, `references/operating-guide.md`) to point to `.claude/agents/` instead.

- [ ] **Step 5: Run tests and commit**

```bash
python3 -m pytest -q -p no:cacheprovider && bash scripts/validate_setup.sh
git add .claude/agents .agents/skills references
git commit -m "feat(harness): add research and critic subagents; retire agent-modes"
```

### Task 12: Opt-in live behavioral evals

**Finding:** All evals are structural. Nothing runs the model against `evals.json` prompts.

**Files:**
- Create: `scripts/run_live_evals.py`
- Test: `tests/test_live_evals.py`
- Modify: `references/operating-guide.md` (one bullet under Infrastructure)

**Interfaces:**
- Produces: CLI `python3 scripts/run_live_evals.py --skill <name> [--case <id>] [--live] [--out <dir>]`. Without `--live` it prints the cases it would run. With `--live` it runs `claude -p <prompt> --output-format json` per case in a temp cwd and writes `<out>/<skill>-<id>.json` with `passed`, `missing_terms`, `forbidden_terms_hit`.

- [ ] **Step 1: Write the failing test (dry-run and scoring only, no model)**

Create `tests/test_live_evals.py`:

```python
import json
from scripts import run_live_evals as live


def test_dry_run_lists_cases_for_a_skill(capsys):
    cases = live.load_cases('idea-grill')
    assert cases and all({'id', 'prompt'} <= set(c) for c in cases)


def test_scoring_checks_must_and_must_not_mention():
    case = {'id': 1, 'prompt': 'x', 'must_mention': ['segment', 'assumption'], 'must_not_mention': ['start coding']}
    good = live.score(case, 'Which segment? What assumption is riskiest?')
    bad = live.score(case, 'Great idea, start coding now.')
    assert good['passed'] and good['missing_terms'] == []
    assert not bad['passed'] and bad['missing_terms'] == ['segment', 'assumption'] and bad['forbidden_terms_hit'] == ['start coding']
```

- [ ] **Step 2: Implement the runner**

Create `scripts/run_live_evals.py`:

```python
#!/usr/bin/env python3
"""Opt-in live skill evals: run evals.json prompts through `claude -p` in fresh sessions and score them.

Dry run by default (lists cases). `--live` spends model tokens; run it deliberately.
"""
from __future__ import annotations
import argparse
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_cases(skill: str) -> list[dict]:
    path = ROOT / '.agents/skills' / skill / 'evals/evals.json'
    data = json.loads(path.read_text())
    return data.get('evals', [])


def score(case: dict, answer: str) -> dict:
    lower = answer.lower()
    missing = [t for t in case.get('must_mention', []) if t.lower() not in lower]
    hit = [t for t in case.get('must_not_mention', []) if t.lower() in lower]
    return {'case_id': case.get('id'), 'passed': not missing and not hit,
            'missing_terms': missing, 'forbidden_terms_hit': hit}


def run_case(skill: str, case: dict) -> str:
    prompt = f"Use the {skill} skill. {case['prompt']}"
    with tempfile.TemporaryDirectory() as cwd:
        out = subprocess.run(['claude', '-p', prompt, '--output-format', 'json', '--add-dir', str(ROOT)],
                             cwd=cwd, text=True, capture_output=True, timeout=600)
    if out.returncode != 0:
        raise RuntimeError(out.stderr[-2000:])
    payload = json.loads(out.stdout)
    return payload.get('result', '') if isinstance(payload, dict) else str(payload)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--skill', required=True)
    ap.add_argument('--case', type=str, default='')
    ap.add_argument('--live', action='store_true', help='actually call the model')
    ap.add_argument('--out', type=Path, default=ROOT / 'evals/live-results')
    args = ap.parse_args()
    cases = [c for c in load_cases(args.skill) if not args.case or str(c.get('id')) == args.case]
    if not args.live:
        for c in cases:
            print(f"[dry-run] {args.skill} #{c.get('id')}: {c['prompt'][:100]}")
        print(f"{len(cases)} case(s). Add --live to run them.")
        return 0
    args.out.mkdir(parents=True, exist_ok=True)
    failures = 0
    for c in cases:
        answer = run_case(args.skill, c)
        result = score(c, answer) | {'answer': answer}
        (args.out / f"{args.skill}-{c.get('id')}.json").write_text(json.dumps(result, indent=2))
        failures += not result['passed']
        print(f"{'PASS' if result['passed'] else 'FAIL'} {args.skill} #{c.get('id')} missing={result['missing_terms']} forbidden={result['forbidden_terms_hit']}")
    return 1 if failures else 0


if __name__ == '__main__':
    raise SystemExit(main())
```

Add `evals/live-results/` to `.gitignore`.

- [ ] **Step 3: Run the tests and a dry run**

```bash
python3 -m pytest -q -p no:cacheprovider tests/test_live_evals.py
python3 scripts/run_live_evals.py --skill idea-grill
```

Expected: tests pass; dry run lists 6 cases.

- [ ] **Step 4: Document and commit**

Add to `references/operating-guide.md` under Infrastructure: `- **Live evals (opt-in, spends tokens):** python3 scripts/run_live_evals.py --skill <name> --live; results under evals/live-results/.`

```bash
git add scripts/run_live_evals.py tests/test_live_evals.py .gitignore references/operating-guide.md
git commit -m "feat(evals): opt-in live skill evals via claude -p"
```

### Task 13: Archive dated docs

**Finding:** `docs/` is 4.8 MB of dated audits, plans and reviews that agents grep into and that still mention removed components.

**Files:**
- Move: dated files and folders in `docs/` to `docs/archive/`
- Keep in place: `docs/implementation-plan.md`, `docs/implementation-status.md`, `docs/to_be_improved.md`, `docs/deferred-maintenance.md`, `docs/agentic-evaluation.md`, `docs/api-access-matrix.md`, `docs/superpowers/`, `docs/migrations/`
- Modify: `AGENTS.md`/`references/operating-guide.md` links if any point at moved files

- [ ] **Step 1: Move**

```bash
mkdir -p docs/archive
git mv docs/agent-improvements docs/audits docs/agentic-audit-2026-09-11.md docs/archive/search-visibility-*.md \
  docs/archive/digital-marketing-optimization-plan*.md docs/skill-test-report-2026-06-20.md docs/agent-coach-implementation-plan.md \
  docs/customer-need-and-entrant-success-plan.md docs/strategic-positioning-implementation-plan.md \
  docs/imagery-style-motion-concept-gates.md docs/archive/
```

- [ ] **Step 2: Fix links**

Run: `grep -rn "docs/agent-improvements\|docs/audits\|docs/archive/digital-marketing-optimization-plan\|docs/search-visibility" --include=*.md --include=*.json . --exclude-dir=projects --exclude-dir=.git --exclude-dir=archive`
Edit each hit to the `docs/archive/...` path. Known hits: `.agents/skills/brand-website-designer-builder/references/aeo-geo-visibility.md`, `references/subprojects.md`.

- [ ] **Step 3: Validate and commit**

```bash
bash scripts/validate_setup.sh && python3 -m pytest -q -p no:cacheprovider
git add -A docs .agents references
git commit -m "chore(docs): archive dated audits and plans under docs/archive"
```

---

## Phase 2 — Business validation content

### Task 14: Smoke-test design mode with kit generator

**Finding:** Smoke test to interview is the founder's required default, yet "fake door" and "pre-order" appear nowhere, no skill produces a smoke-test kit, and there is no artifact for a small ad-budget approval.

**Files:**
- Create: `references/smoke-test.md`
- Create: `scripts/evidence_scout/build_smoke_test_kit.py`
- Modify: `config/workflow-routes.json` (new route `smoke-test-design`)
- Modify: `config/skill-catalog.json` (new mode `smoke_test` on `opportunity-risk-designer`)
- Modify: `.agents/skills/opportunity-risk-designer/SKILL.md` (mode line + link)
- Modify: `.agents/skills/opportunity-risk-designer/evals/evals.json` (one case)
- Test: `tests/test_smoke_test_kit.py`

**Interfaces:**
- Produces: CLI `python3 scripts/evidence_scout/build_smoke_test_kit.py --run-dir <evidence run> --hypothesis-id H1 --offer "<one line>" --segment "<segment>" --variants 3 --out-dir <run>/experiments/smoke-<date>` writing `smoke-test-plan.md`, `message-variants.json`, `budget-approval.json` (`{"status": "pending", "requested_amount": null, "currency": null, "channel": null, "approved_by": null, "approved_at": null}`), `responders.json` (`[]`).
- Route id `smoke-test-design` → skill `opportunity-risk-designer`, mode `smoke_test`, required_references `["references/smoke-test.md", "references/interview-recruitment.md"]`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_smoke_test_kit.py`:

```python
import json
from pathlib import Path
from scripts.evidence_scout import build_smoke_test_kit as kit
from scripts import route_workflow


def test_kit_writes_plan_variants_and_pending_budget(tmp_path):
    run = tmp_path / 'run'; run.mkdir()
    (run / 'summary.json').write_text(json.dumps({'topic': 'expat health insurance switching', 'customer_segment': 'expats in Germany'}))
    out = kit.build(run_dir=run, hypothesis_id='H1', offer='Switch your PKV in 7 days with a fee-only adviser',
                    segment='English-speaking employees in Germany', variants=3, out_dir=tmp_path / 'smoke')
    assert (out / 'smoke-test-plan.md').exists()
    variants = json.loads((out / 'message-variants.json').read_text())
    assert len(variants) == 3 and all({'id', 'headline', 'promise', 'cta', 'pain_frame'} <= set(v) for v in variants)
    budget = json.loads((out / 'budget-approval.json').read_text())
    assert budget['status'] == 'pending' and budget['approved_by'] is None
    assert json.loads((out / 'responders.json').read_text()) == []
    plan = (out / 'smoke-test-plan.md').read_text()
    for heading in ['## Hypothesis', '## Conversion action and thresholds', '## Disclosure', '## Budget approval', '## Responder to interview funnel', '## Stop rules']:
        assert heading in plan


def test_smoke_test_route_selects_risk_designer_mode():
    packet = route_workflow.route_request('design a landing page smoke test for my idea', intent='smoke-test-design',
                                         task_scope='strategy', check_skill='opportunity-risk-designer')
    assert packet['skill'] == 'opportunity-risk-designer' and packet['mode'] == 'smoke_test'
    assert 'references/smoke-test.md' in packet['required_references']
    assert 'references/interview-recruitment.md' in packet['required_references']
```

- [ ] **Step 2: Run to see failures**

Run: `python3 -m pytest -q -p no:cacheprovider tests/test_smoke_test_kit.py`
Expected: ImportError / route not found.

- [ ] **Step 3: Write the reference**

Create `references/smoke-test.md`:

```markdown
# Smoke test to interview

Default validation path for a founder without a customer panel: expose a specific promise to the intended segment, measure a behavioral step, then interview the people who took it. Read after the riskiest assumption is named. This designs a test brief; publishing, ad spend and outreach keep their own authorization.

## Sequence

1. Problem interviews or reviewed public evidence name the segment, trigger and pain in customer language (idea-grill, evidence-scout).
2. Message/offer smoke test: one page, one segment, one conversion action, two or three message variants that differ in pain frame, not wording.
3. Escalate commitment only after the page converts: priced fake door, deposit, pre-order, booked qualified call, or concierge sale.
4. Recruit interviewees from responders (screener → booked → attended → usable incident). Feed results to interview-bridge and back into the risk ranking.

## Conversion action and thresholds

Choose the action that matches the buying cycle: email capture is directional only; a booked qualified call, deposit or payment is behavioral evidence. Set thresholds before launch and label them as proposed learning budgets, not benchmarks. Published ranges (checked 2026-09-24) vary widely; one practitioner rule treats 5%+ visitor-to-signup from cold traffic as a go signal, others refuse universal benchmarks. Compute the required sample from the threshold: to distinguish 2% from 5% conversion you need several hundred qualified visitors per variant. Record visitor source, variant and segment fit for every responder; unqualified signups do not count.

## Disclosure

A fake door must tell the responder within one step that the product is not yet available, what happens with their data, and offer the interview or waitlist honestly. No fake scarcity, no fabricated testimonials, no collecting payment details without the ability to refund.

## Budget approval

Advertising spend is not pre-authorized. Write `budget-approval.json` with the requested amount, currency, channel, duration and the decision it will inform; the founder fills `approved_by`/`approved_at`. Launch only when `status` is `approved`. Size the request from the threshold and an assumed CPC range retrieved for the channel at run time; state the CPC source and date.

## Responder to interview funnel

identified → exposed → responded → eligible → booked → attended → usable incident. Keep denominators per variant and channel. Apply `references/interview-recruitment.md` for screening and no-payment rules. Responders are volunteers, not customers; the interview verifies the incident, workaround and spend.

## Stop rules

Stop or change the test when: the approved budget or window is spent; qualified traffic is below the minimum sample and the channel cannot supply more; responders are out of segment; or the segment consistently reports a different pain. A failed smoke test refutes the message or channel first; it does not by itself refute the need.
```

- [ ] **Step 4: Write the generator**

Create `scripts/evidence_scout/build_smoke_test_kit.py`:

```python
#!/usr/bin/env python3
"""Generate a smoke-test kit (plan, message variants, pending budget approval, responders ledger)."""
from __future__ import annotations
import argparse
import json
import time
from pathlib import Path

PAIN_FRAMES = ['cost of the current workaround', 'time or effort lost', 'risk or fear of getting it wrong',
               'missed outcome or opportunity', 'trust in existing providers']


def build(*, run_dir: Path, hypothesis_id: str, offer: str, segment: str, variants: int, out_dir: Path) -> Path:
    summary = json.loads((run_dir / 'summary.json').read_text()) if (run_dir / 'summary.json').exists() else {}
    topic = summary.get('topic', 'unknown topic')
    out_dir.mkdir(parents=True, exist_ok=False)
    msgs = [{'id': f'V{i+1}', 'pain_frame': PAIN_FRAMES[i % len(PAIN_FRAMES)],
             'headline': f'[{PAIN_FRAMES[i % len(PAIN_FRAMES)]}] headline for {segment}', 'promise': offer,
             'cta': 'Book a 20-minute call', 'evidence_ref': None} for i in range(variants)]
    (out_dir / 'message-variants.json').write_text(json.dumps(msgs, indent=2))
    (out_dir / 'budget-approval.json').write_text(json.dumps({
        'status': 'pending', 'requested_amount': None, 'currency': None, 'channel': None, 'duration_days': None,
        'decision_informed': f'{hypothesis_id}: does {segment} take a behavioral step for "{offer}"?',
        'cpc_assumption': None, 'cpc_source': None, 'approved_by': None, 'approved_at': None}, indent=2))
    (out_dir / 'responders.json').write_text('[]\n')
    plan = f"""# Smoke test plan — {topic}

Generated {time.strftime('%Y-%m-%d')} from `{run_dir}`. Follow `references/smoke-test.md`.

## Hypothesis
{hypothesis_id}: {segment} experiencing {topic} will take a behavioral step for "{offer}".

## Segment and traffic source
Segment: {segment}. Traffic: <channel, why this reaches the segment, retrieved CPC range with source and date>.

## Message variants
See `message-variants.json` ({variants} variants, one pain frame each). Replace bracketed headlines with customer language from the evidence run and record the evidence_ref.

## Conversion action and thresholds
Action: <booked call | deposit | pre-order | email (directional only)>. Pass threshold: <x% of qualified visitors>, proposed learning budget, not a benchmark. Minimum qualified visitors per variant: <n>.

## Disclosure
<exact on-page text shown after the CTA>.

## Budget approval
See `budget-approval.json`; status pending. Do not launch before it is approved.

## Responder to interview funnel
identified → exposed → responded → eligible → booked → attended → usable incident. Log in `responders.json`; screen with the interview kit.

## Stop rules
<budget/window spent | qualified traffic below minimum | responders out of segment | different pain reported>.
"""
    (out_dir / 'smoke-test-plan.md').write_text(plan)
    return out_dir


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--run-dir', required=True, type=Path)
    ap.add_argument('--hypothesis-id', required=True)
    ap.add_argument('--offer', required=True)
    ap.add_argument('--segment', required=True)
    ap.add_argument('--variants', type=int, default=3)
    ap.add_argument('--out-dir', required=True, type=Path)
    a = ap.parse_args()
    print(build(run_dir=a.run_dir, hypothesis_id=a.hypothesis_id, offer=a.offer, segment=a.segment,
                variants=a.variants, out_dir=a.out_dir))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
```

- [ ] **Step 5: Add the route and catalog mode**

In `config/skill-catalog.json` under `skills.opportunity-risk-designer.modes` add:

```json
"smoke_test": {
  "prerequisites": ["named riskiest assumption", "segment and pain in customer language"],
  "required_references": ["references/smoke-test.md", "references/interview-recruitment.md"],
  "artifacts": ["smoke-test-plan.md", "message-variants.json", "budget-approval.json", "responders.json"],
  "inputs": ["hypothesis", "offer", "segment", "evidence run"],
  "output_owner": "opportunity-risk-designer"
}
```

In `config/workflow-routes.json` add a route object shaped like `opportunity-prioritization` (copy it, then change): `"id": "smoke-test-design"`, `"skill": "opportunity-risk-designer"`, `"mode": "smoke_test"`, `"match": ["smoke test", "fake door", "landing page test", "pre-order test", "waitlist test", "validation page"]`, same `forbidden` list as `opportunity-prioritization`.

- [ ] **Step 6: Update SKILL.md and evals**

In `.agents/skills/opportunity-risk-designer/SKILL.md` add after the case-appraisal paragraph:

```
For the checked `smoke-test-design` route, read repo-root `references/smoke-test.md` and generate the kit with `python3 scripts/evidence_scout/build_smoke_test_kit.py`. This is the default next test when the riskiest assumption is demand or message and the founder has no customer panel; interviews recruit from responders. Ad spend needs the recorded approval.
```

Append to `.agents/skills/opportunity-risk-designer/evals/evals.json` `evals` array:

```json
{"id": "smoke-1", "prompt": "Evidence shows expats in Germany complain about switching private health insurance. What should I test next? I have no customer list.",
 "expected_output": "Recommends a message/offer smoke test with a single conversion action, variants by pain frame, pre-set thresholds, disclosure, a pending budget approval, and interviews recruited from responders.",
 "must_mention": ["smoke test", "threshold", "responders", "interview", "budget"],
 "must_not_mention": ["build the product", "survey your friends"], "required_artifacts": [], "files": []}
```

- [ ] **Step 7: Run everything and commit**

```bash
python3 -m pytest -q -p no:cacheprovider tests/test_smoke_test_kit.py tests/test_skill_route_coverage.py && python3 scripts/validate_skill_routes.py && python3 scripts/run_evals.py && python3 -m pytest -q -p no:cacheprovider
git add references/smoke-test.md scripts/evidence_scout/build_smoke_test_kit.py config tests/test_smoke_test_kit.py .agents/skills/opportunity-risk-designer
git commit -m "feat(validation): smoke-test design mode with kit generator and pending budget approval"
```

### Task 15: Validation-page mode for the website skill

**Finding:** The website skill has no smoke/validation landing-page mode and is locked to a full Next.js build.

**Files:**
- Create: `.agents/skills/brand-website-designer-builder/references/validation-page.md`
- Modify: `.agents/skills/brand-website-designer-builder/SKILL.md` (one bullet)
- Modify: `config/workflow-routes.json` (route `validation-page`), `config/skill-catalog.json` (mode `validation_page`)
- Test: `tests/test_website_launch.py` (one routing test)

**Interfaces:**
- Route id `validation-page` → skill `brand-website-designer-builder`, mode `validation_page`, required_references `[".agents/skills/brand-website-designer-builder/references/validation-page.md", "references/smoke-test.md"]`.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_website_launch.py`:

```python
def test_validation_page_route_is_lightweight_and_reads_smoke_reference():
    from scripts import route_workflow
    packet = route_workflow.route_request('build a smoke test landing page', intent='validation-page',
                                         task_scope='execution', check_skill='brand-website-designer-builder')
    assert packet['mode'] == 'validation_page'
    assert 'references/smoke-test.md' in packet['required_references']
```

- [ ] **Step 2: Write the reference**

Create `.agents/skills/brand-website-designer-builder/references/validation-page.md`:

```markdown
# Validation page mode

A single-purpose page for a smoke test designed under `references/smoke-test.md`. Inputs: `smoke-test-plan.md`, `message-variants.json`, approved brand tokens if any, the conversion action, disclosure text and the analytics decision.

Requirements:
- One page per variant or one page with a server-selected variant; no navigation, one CTA, message match to the ad or post that sends traffic (headline and promise identical).
- Static export (`output: 'export'` in the pinned Next.js config) or a single static HTML file when no product site exists yet; no server code, no auth, no CMS.
- Disclosure block after the CTA in the exact plan wording; thank-you route `noindex`; no fabricated testimonials, ratings or scarcity.
- Events: `page_view`, `cta_click`, `lead_submit`, `call_booked` with `variant` and `utm_*` attached; consent handling per `consent-eu.md` before any non-essential script. Analytics remains opt-in and owner-activated.
- Performance: mobile LCP under 2.5 s in the lab run; images sized; system or subset fonts.
- Form fields limited to what screening needs; include the screener question from the interview kit when responders will be interviewed.
- Hand back: preview URL or local build, variant mapping, event names, and the plan path. Publishing and traffic buying keep their existing authorization.
```

- [ ] **Step 3: Wire route, catalog mode and SKILL.md**

Add to `config/skill-catalog.json` `skills.brand-website-designer-builder.modes`:

```json
"validation_page": {
  "prerequisites": ["smoke-test-plan.md with conversion action and disclosure"],
  "required_references": [".agents/skills/brand-website-designer-builder/references/validation-page.md", "references/smoke-test.md"],
  "artifacts": ["static validation page", "variant mapping", "event names"],
  "inputs": ["smoke-test-plan.md", "message-variants.json", "brand tokens (optional)"],
  "output_owner": "brand-website-designer-builder"
}
```

Add route `validation-page` to `config/workflow-routes.json` (copy `website-build`, set `"mode": "validation_page"`, `"match": ["validation page", "smoke test page", "fake door page", "waitlist page", "coming soon page"]`).

Add to SKILL.md bullets: `- Validation page for a smoke test: apply [validation page](references/validation-page.md) and repo-root references/smoke-test.md; static, single CTA, disclosure, no analytics without owner activation.`

- [ ] **Step 4: Run and commit**

```bash
python3 -m pytest -q -p no:cacheprovider tests/test_website_launch.py tests/test_skill_route_coverage.py && python3 scripts/validate_skill_routes.py && python3 -m pytest -q -p no:cacheprovider
git add .agents/skills/brand-website-designer-builder config tests/test_website_launch.py
git commit -m "feat(website): validation-page mode for smoke tests"
```

### Task 16: Interview kit intake from smoke-test responders

**Finding:** `interview-bridge` recruits from evidence sources only; there is no way to turn smoke-test responders into screened interview rows.

**Files:**
- Modify: `scripts/evidence_scout/build_interview_kit.py` (new `--responders` option)
- Modify: `.agents/skills/interview-bridge/references/workflow.md` (one paragraph)
- Test: `tests/test_interview_source_review.py`

**Interfaces:**
- Consumes: `responders.json` from Task 14: list of `{"id": str, "variant": str, "source": str, "responded_at": str, "contact_ref": str, "screener_answers": {}}`.
- Produces: `interview-tracker.md` gains a `## Responder intake` table with columns `responder_id | variant | source | segment_fit (unresolved) | recent_incident (unresolved) | booked | attended | usable_incident`.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_interview_source_review.py` (reuse that file's existing run fixture helper if one exists; otherwise create a minimal run with `summary.json` and an empty `evidence.jsonl`):

```python
def test_responders_are_added_to_tracker_as_unresolved(tmp_path):
    import json, subprocess, sys
    run = tmp_path / 'run'; run.mkdir()
    (run / 'summary.json').write_text(json.dumps({'topic': 't', 'customer_segment': 's'}))
    (run / 'evidence.jsonl').write_text('')
    responders = tmp_path / 'responders.json'
    responders.write_text(json.dumps([{'id': 'R1', 'variant': 'V2', 'source': 'meta-ads', 'responded_at': '2026-09-24',
                                       'contact_ref': 'form-17', 'screener_answers': {}}]))
    out = subprocess.run([sys.executable, 'scripts/evidence_scout/build_interview_kit.py', '--run-dir', str(run),
                          '--responders', str(responders), '--allow-empty-evidence'], text=True, capture_output=True)
    assert out.returncode == 0, out.stderr
    tracker = (run / 'interview' / 'interview-tracker.md').read_text()
    assert '## Responder intake' in tracker and '| R1 | V2 | meta-ads | unresolved | unresolved |' in tracker
```

- [ ] **Step 2: Implement**

In `scripts/evidence_scout/build_interview_kit.py` add arguments:

```python
    parser.add_argument("--responders", type=Path, default=None,
                        help="responders.json from a smoke-test kit; rows are added to the tracker as unresolved.")
    parser.add_argument("--allow-empty-evidence", action="store_true",
                        help="Build a hypothesis-only kit when no accepted evidence exists (responder intake still applies).")
```

Add a helper and call it where `interview-tracker.md` is written:

```python
def responder_intake_table(path: Path | None) -> str:
    if not path:
        return ""
    rows = json.loads(path.read_text())
    if not isinstance(rows, list):
        raise SystemExit("--responders must be a JSON list")
    lines = ["", "## Responder intake", "",
             "Responders are volunteers, not customers. Screen segment fit and a recent incident before counting an interview.", "",
             "| responder_id | variant | source | segment_fit | recent_incident | booked | attended | usable_incident |",
             "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r.get('id','?')} | {r.get('variant','?')} | {r.get('source','?')} | unresolved | unresolved |  |  |  |")
    return "\n".join(lines) + "\n"
```

Append `responder_intake_table(args.responders)` to the tracker content. Where the script currently stops on missing/empty accepted evidence, allow continuation when `--allow-empty-evidence` is set, emitting the H-hypothesis guide already described in the workflow.

- [ ] **Step 3: Document**

Append to `.agents/skills/interview-bridge/references/workflow.md` under `## Command`:

```
After a smoke test, pass `--responders <run>/experiments/<smoke>/responders.json` to add responder rows to the tracker as unresolved. Screen each for segment fit and a recent incident before booking; unpaid volunteering is not evidence of need.
```

- [ ] **Step 4: Run and commit**

```bash
python3 -m pytest -q -p no:cacheprovider tests/test_interview_source_review.py && python3 -m pytest -q -p no:cacheprovider
git add scripts/evidence_scout/build_interview_kit.py .agents/skills/interview-bridge tests/test_interview_source_review.py
git commit -m "feat(interviews): intake smoke-test responders into the interview tracker"
```

### Task 17: Explicit viability targets in the economics model

**Finding:** No artifact states the founder's actual viability test (profitable within 2 to 3 years within a bounded investment and owner income). `case_economics.py` computes cash but never judges it.

**Files:**
- Modify: `scripts/case_economics.py` (`INPUT_KEYS`, `_calculate_base` result, new `viability` block)
- Modify: `references/case-assessment.md` (one paragraph)
- Modify: `templates/project/case-business-case.md` (new section)
- Test: `tests/test_case_economics.py`

**Interfaces:**
- Consumes input key `viability_targets`: `{"profitable_by_month": int|null, "max_cash_need": number|null, "owner_income_per_month": number|null}`.
- Produces `results.viability`: `{"status": "pass"|"fail"|"unresolved", "first_profitable_month": int|null, "min_closing_cash": number|null, "profit_target_met": bool|null, "cash_target_met": bool|null, "owner_income_met": bool|null, "reasons": [str]}`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_case_economics.py`:

```python
def cash_inputs():
    d = inputs()
    d.update(horizon_months=6, opening_cash=5000, startup_cash_cost=2000, receipt_lag_months=0,
             service_payment_lag_months=0, acquisition_payment_lag_months=0,
             sales_per_month=[20, 40, 60, 60, 60, 60], lead_to_customer=None,
             viability_targets={'profitable_by_month': 4, 'max_cash_need': 6000, 'owner_income_per_month': 2500})
    return d


def test_viability_verdict_from_cash_schedule():
    v = calculate(cash_inputs())['results']['viability']
    assert v['status'] in {'pass', 'fail'}
    assert isinstance(v['first_profitable_month'], (int, type(None)))
    assert v['reasons'] and all(isinstance(r, str) for r in v['reasons'])


def test_viability_unresolved_without_targets_or_cash():
    assert calculate(inputs())['results']['viability']['status'] == 'unresolved'
    d = cash_inputs(); d.pop('viability_targets')
    assert calculate(d)['results']['viability']['status'] == 'unresolved'


def test_viability_targets_are_validated():
    d = cash_inputs(); d['viability_targets'] = {'profitable_by_month': 0}
    with pytest.raises(ValueError, match='viability_targets'):
        calculate(d)
```

- [ ] **Step 2: Implement**

In `scripts/case_economics.py`:
1. Add `viability_targets` to `INPUT_KEYS`.
2. Add after `_calculate_base` a function:

```python
def _viability(inputs, result, vals, labor):
    targets = inputs.get('viability_targets')
    out = {'status': 'unresolved', 'first_profitable_month': None, 'min_closing_cash': None,
           'profit_target_met': None, 'cash_target_met': None, 'owner_income_met': None, 'reasons': []}
    if targets is None:
        out['reasons'].append('viability_targets not supplied'); return out
    if not isinstance(targets, dict) or set(targets) - {'profitable_by_month', 'max_cash_need', 'owner_income_per_month'}:
        raise ValueError('viability_targets accepts profitable_by_month, max_cash_need, owner_income_per_month')
    pbm = targets.get('profitable_by_month')
    if pbm is not None and (type(pbm) is not int or pbm < 1):
        raise ValueError('viability_targets.profitable_by_month must be a positive integer')
    months = result['cash'].get('months') if result['cash'].get('status') == 'conditional' else None
    if not months:
        out['reasons'].append('no conditional cash schedule; supply horizon, opening cash and monthly volumes'); return out
    profitable = [m['month'] for m in months if m['contribution'] - vals['fixed_per_month'] - vals['owner_cash_per_month'] > 0]
    out['first_profitable_month'] = profitable[0] if profitable else None
    out['min_closing_cash'] = min(m['closing_cash'] for m in months)
    checks = []
    if pbm is not None:
        out['profit_target_met'] = out['first_profitable_month'] is not None and out['first_profitable_month'] <= pbm
        checks.append(out['profit_target_met'])
        out['reasons'].append(f"first profitable month {out['first_profitable_month']} vs target {pbm}")
    if targets.get('max_cash_need') is not None:
        need = inputs.get('opening_cash', 0) - out['min_closing_cash']
        out['cash_target_met'] = need <= targets['max_cash_need']
        checks.append(out['cash_target_met'])
        out['reasons'].append(f"peak cash need {round(need, 2)} vs max {targets['max_cash_need']}")
    if targets.get('owner_income_per_month') is not None:
        out['owner_income_met'] = vals['owner_cash_per_month'] >= targets['owner_income_per_month']
        checks.append(out['owner_income_met'])
        out['reasons'].append(f"modelled owner cash {vals['owner_cash_per_month']} vs target {targets['owner_income_per_month']}")
    out['status'] = 'pass' if checks and all(checks) else ('fail' if checks else 'unresolved')
    out['reasons'].append('conditional on the supplied schedule; arithmetic is not demand evidence')
    return out
```

3. At the end of `_calculate_base`, before returning, set `result['viability'] = _viability(inputs, result, vals, labor)` (adapt to the local names for the values dict and labor already in scope; return shape must stay `{'results': result, ...}` as today).

- [ ] **Step 3: Run tests**

Run: `python3 -m pytest -q -p no:cacheprovider tests/test_case_economics.py`
Expected: PASS (adjust the fixture volumes if `status` resolves to something the assertions do not accept; assertions only require a decision and reasons).

- [ ] **Step 4: Surface the verdict in the contract and template**

Append to `references/case-assessment.md` under `## Numerical prose and derived-input corrections`:

```
## Viability verdict

`economics_inputs.viability_targets` records the founder's test: `profitable_by_month` (default proposal 24–36 months, the founder confirms), `max_cash_need`, `owner_income_per_month`. The helper returns `results.viability` with status pass/fail/unresolved and reasons. Quote it with `{{economics.results.viability.status}}` and `{{economics.results.viability.first_profitable_month}}`; never hand-write the verdict. Unresolved means the schedule or targets are missing, not that the business is unviable.
```

Add to `templates/project/case-business-case.md` before `## Alternatives and decision`:

```
## Viability verdict

Status `{{economics.results.viability.status}}`; first profitable month `{{economics.results.viability.first_profitable_month}}`; peak cash need vs. the founder's limit; owner income vs. target. State the downside scenario result and which single driver flips the verdict.
```

- [ ] **Step 5: Full suite and commit**

```bash
python3 -m pytest -q -p no:cacheprovider
git add scripts/case_economics.py tests/test_case_economics.py references/case-assessment.md templates/project/case-business-case.md
git commit -m "feat(economics): founder viability targets and verdict in the case model"
```

### Task 18: Desirability / feasibility / viability evidence scorecard

**Finding:** Decision gates exist per skill but no single scorecard combines desirability, feasibility and viability with evidence strength.

**Files:**
- Modify: `templates/project/case-README.md` (new section)
- Modify: `references/case-assessment.md` (scorecard rule)
- Modify: `references/strategic-positioning.md` (one sentence linking `insufficient_evidence/investigate/test/commit` to the ladder)
- Test: `tests/test_case_end_to_end.py` (template assertion)

- [ ] **Step 1: Write the failing test**

Append to `tests/test_case_end_to_end.py`:

```python
def test_case_readme_template_has_evidence_scorecard():
    from pathlib import Path
    text = (Path(__file__).resolve().parents[1] / 'templates/project/case-README.md').read_text()
    assert '## Evidence scorecard' in text
    for col in ['Dimension', 'Assumption', 'Evidence strength', 'Status']:
        assert col in text
```

- [ ] **Step 2: Add the section**

Insert into `templates/project/case-README.md` after the first heading block:

```markdown
## Evidence scorecard

One row per decision-changing assumption. Evidence strength uses the ladder `opinion < behavior < money` (Strategyzer): opinions are statements and interest; behavior is a completed step such as a booked call, workaround or repeated use; money is payment, deposit or signed pilot. Status is `insufficient_evidence`, `investigate`, `test` or `commit`. The verdict row summarizes each dimension; it never averages rows.

| Dimension | Assumption | Evidence strength | Source refs | Counter-evidence | Status | Next test |
|---|---|---|---|---|---|---|
| Desirability | | opinion / behavior / money | | | | |
| Feasibility | | | | | | |
| Viability | `{{economics.results.viability.status}}` | | | | | |
```

- [ ] **Step 3: Add the rule and cross-link**

In `references/case-assessment.md` `## Research content` add a bullet: `- Scorecard: maintain the Evidence scorecard in the case README with the opinion/behavior/money ladder; the viability row quotes the helper's verdict placeholder.` In `references/strategic-positioning.md` after the sentence distinguishing `insufficient_evidence`, `investigate`, `test` and `commit`, add: `Record the supporting evidence strength (opinion, behavior, money) in the case README scorecard.`

- [ ] **Step 4: Run and commit**

```bash
python3 -m pytest -q -p no:cacheprovider tests/test_case_end_to_end.py
git add templates/project/case-README.md references/case-assessment.md references/strategic-positioning.md tests/test_case_end_to_end.py
git commit -m "feat(case): desirability/feasibility/viability evidence scorecard"
```

---

## Phase 3 — Branding content

### Task 19: Verbal identity stage and export

**Finding:** No brand skill covers tone of voice, messaging framework or tagline, so marketing has nothing to consume.

**Files:**
- Create: `.agents/skills/brand-strategy-director/references/verbal-identity.md`
- Modify: `.agents/skills/brand-strategy-director/SKILL.md` (link)
- Modify: `.agents/skills/brand-workspace-manager/scripts/manage-brand-workspace.py:19` and `workspace_cli.py:20` (add `"voice"` after `"strategy"`)
- Modify: `.agents/skills/brand-designer/references/workflow.md` (pipeline order), `references/routing.md` (dispatch row)
- Modify: `.agents/skills/brand-exporter/references/export-format.md` (add `voice.json`)
- Modify: `.agents/skills/brand-guidelines-writer/references/*.md` anatomy (add Verbal identity chapter)
- Modify: `schemas/brand-manifest.schema.json` (`$defs.stage.enum` is an enum today; add `"voice"` after `"strategy"`)
- Test: `tests/brand_designer/` (add `test_voice_stage.py`)

**Interfaces:**
- Produces: stage id `voice`; artifact `voice/voice.json` with keys `personality`, `tone_sliders` (list of `{axis, position, rationale}`), `value_proposition`, `message_pillars` (list of `{pillar, proof}`), `tagline_candidates`, `vocabulary` (`use`, `avoid`), `examples` (`do`, `dont`), `source_refs`.

- [ ] **Step 1: Write the failing test**

Create `tests/brand_designer/test_voice_stage.py`:

```python
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_voice_stage_is_registered_everywhere():
    for script in ['manage-brand-workspace.py', 'workspace_cli.py']:
        text = (ROOT / '.agents/skills/brand-workspace-manager/scripts' / script).read_text()
        assert '"voice"' in text
    schema = json.loads((ROOT / 'schemas/brand-manifest.schema.json').read_text())
    stage = schema['$defs']['stage']
    assert 'enum' not in stage or 'voice' in stage['enum']
    assert 'voice' in (ROOT / '.agents/skills/brand-designer/references/workflow.md').read_text()
    assert (ROOT / '.agents/skills/brand-strategy-director/references/verbal-identity.md').exists()
    assert 'voice.json' in (ROOT / '.agents/skills/brand-exporter/references/export-format.md').read_text()
```

- [ ] **Step 2: Write the reference**

Create `.agents/skills/brand-strategy-director/references/verbal-identity.md`:

```markdown
# Verbal identity

Run after strategy is approved and before logo production. Output `voice/voice.json` and `voice/voice.md`; marketing and website consume them through the brand export.

1. Personality: three to five adjectives from the approved strategy, each with one sentence on what it rules out.
2. Tone sliders: formal↔casual, playful↔serious, expert↔peer, bold↔reserved, warm↔neutral. Position each with a rationale tied to audience evidence or the business-to-brand snapshot; note how tone flexes by channel (support, sales, social, legal).
3. Value proposition: one sentence: for [segment] who [situation], [brand] delivers [outcome] unlike [alternative] because [mechanism]. For business-linked work copy the selected promise; never rewrite the buyer or promise here.
4. Message pillars: three pillars, each with the proof the owner can actually show (no invented claims, ratings or numbers).
5. Tagline candidates: five, ranked, each with a plain-language reading test and a trademark-search note (see naming-and-checks.md).
6. Vocabulary: words to use, words to avoid, spelling/capitalization decisions, how to write the brand name.
7. Examples: three do/don't pairs across a headline, a support reply and a social post.

Ask one question at a time when a slider or pillar cannot be inferred. Search current competitor copy before finalizing so the voice contrasts deliberately. Record sources with dates.
```

- [ ] **Step 3: Register the stage**

In both workspace scripts insert `"voice"` after `"strategy"` in `STAGES`. In `schemas/brand-manifest.schema.json` the `$defs.stage.enum` list currently reads `discovery, research, strategy, logo, ...`; insert `"voice"` after `"strategy"`.

In `.agents/skills/brand-designer/references/workflow.md` change the pipeline line to begin `strategy -> voice (brand-strategy-director, verbal-identity mode) -> typography -> ...`. In `references/routing.md` add `- Verbal identity (voice, messaging, tagline): use brand-strategy-director per brand-strategy-director/references/verbal-identity.md.`

In `.agents/skills/brand-exporter/references/export-format.md` add under the package listing: `- voice/voice.json and voice/voice.md: verbal identity for marketing and website copy.`

In the guidelines-writer anatomy reference add a chapter `Verbal identity: personality, tone sliders and channel flex, value proposition, message pillars with proof, tagline, vocabulary, do/don't examples.`

Add to `.agents/skills/brand-strategy-director/SKILL.md`: `For the voice stage read [verbal identity](references/verbal-identity.md).`

- [ ] **Step 4: Run and commit**

```bash
python3 -m pytest -q -p no:cacheprovider tests/brand_designer && python3 -m pytest -q -p no:cacheprovider
git add .agents/skills schemas tests/brand_designer/test_voice_stage.py
git commit -m "feat(brand): verbal identity stage with voice export"
```

### Task 20: Naming and legal checks

**Finding:** The name is captured as intake only; no naming process, domain/handle check or trademark similarity search exists; AI-generated logos lack copyright protection in the US without human authorship, so trademark search and a human vector-edit pass are the protection that matters.

**Files:**
- Create: `.agents/skills/brand-strategy-director/references/naming-and-checks.md`
- Create: `scripts/brand/check_domain_rdap.py`
- Modify: `.agents/skills/brand-quality-reviewer/references/review-checklist.md` (four checks)
- Modify: `.agents/skills/brand-asset-producer/references/asset-rules.md` (human edit pass rule)
- Modify: `.agents/skills/brand-workspace-manager/scripts/{manage-brand-workspace.py,workspace_cli.py}` (add `"naming"` after `"discovery"`)
- Test: `tests/brand_designer/test_naming_checks.py`

**Interfaces:**
- CLI `python3 scripts/brand/check_domain_rdap.py <name> [--tlds com,de,io] --out naming/domain-checks.json` → JSON list of `{"domain": str, "status": "registered"|"available"|"unknown", "checked_at": iso, "source": "https://rdap.org/domain/<domain>"}`. Uses `urllib.request`; HTTP 404 → available, 200 → registered, anything else → unknown.

- [ ] **Step 1: Write the failing test (network mocked)**

Create `tests/brand_designer/test_naming_checks.py`:

```python
import json
from pathlib import Path
import urllib.error
from scripts.brand import check_domain_rdap as rdap

ROOT = Path(__file__).resolve().parents[2]


def test_status_mapping(monkeypatch):
    def fake_open(url, timeout=10):
        class R:
            status = 200
            def __enter__(self): return self
            def __exit__(self, *a): return False
        if url.endswith('taken.com'):
            return R()
        raise urllib.error.HTTPError(url, 404, 'nf', {}, None)
    monkeypatch.setattr(rdap.urllib.request, 'urlopen', fake_open)
    rows = rdap.check('taken', ['com'])
    assert rows[0]['status'] == 'registered'
    assert rdap.check('free-name-xyz', ['com'])[0]['status'] == 'available'


def test_naming_stage_and_reviewer_checks_exist():
    for script in ['manage-brand-workspace.py', 'workspace_cli.py']:
        assert '"naming"' in (ROOT / '.agents/skills/brand-workspace-manager/scripts' / script).read_text()
    checklist = (ROOT / '.agents/skills/brand-quality-reviewer/references/review-checklist.md').read_text().lower()
    for needle in ['trademark', 'human vector', '16px', 'monochrome']:
        assert needle in checklist
```

- [ ] **Step 2: Implement the RDAP checker**

Create `scripts/brand/check_domain_rdap.py`:

```python
#!/usr/bin/env python3
"""Preliminary domain availability via public RDAP (rdap.org). Not legal advice; registrar confirms."""
from __future__ import annotations
import argparse
import json
import time
import urllib.error
import urllib.request
from pathlib import Path


def check(name: str, tlds: list[str]) -> list[dict]:
    rows = []
    for tld in tlds:
        domain = f"{name.lower()}.{tld}"
        url = f"https://rdap.org/domain/{domain}"
        status = 'unknown'
        try:
            with urllib.request.urlopen(url, timeout=10) as resp:
                status = 'registered' if resp.status == 200 else 'unknown'
        except urllib.error.HTTPError as exc:
            status = 'available' if exc.code == 404 else 'unknown'
        except (urllib.error.URLError, TimeoutError):
            status = 'unknown'
        rows.append({'domain': domain, 'status': status, 'checked_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'source': url})
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('name')
    ap.add_argument('--tlds', default='com,de,io,co')
    ap.add_argument('--out', type=Path)
    a = ap.parse_args()
    rows = check(a.name, [t.strip() for t in a.tlds.split(',') if t.strip()])
    text = json.dumps(rows, indent=2)
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True); a.out.write_text(text)
    print(text)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
```

Ensure `scripts/brand/__init__.py` exists (create empty if missing).

- [ ] **Step 3: Write the naming reference**

Create `.agents/skills/brand-strategy-director/references/naming-and-checks.md`:

```markdown
# Naming and legal checks

Run when the founder needs a name or before any logo or tagline is approved. Outputs under `naming/`: `naming-brief.md`, `candidates.md`, `domain-checks.json`, `checks.md`. Agent checks are preliminary; a registrar, the trademark office or counsel confirms.

1. Brief: positioning, audience languages, tone, must-avoid associations, pronunciation constraints, descriptive vs. suggestive vs. abstract preference, target markets (which trademark jurisdictions and TLDs matter).
2. Candidates: 12–20 names across at least three naming strategies; screen for meaning in each audience language, spelling on hearing, and category clichés (search current competitor names first).
3. Domain: `python3 scripts/brand/check_domain_rdap.py <name> --tlds <list> --out naming/domain-checks.json`. `unknown` means recheck manually; `available` still needs registrar confirmation.
4. Social handles: record availability for the platforms the marketing plan will use; note the check date and that handles change.
5. Trademark: search identical and confusingly similar marks in the relevant classes on EUIPO eSearch, WIPO Global Brand Database and USPTO search; record the query, classes, date and hits in `checks.md`. Repeat for the chosen tagline and for the final logo's distinctive shape (image search). Any close hit stops approval until the founder decides.
6. Protection note: AI-generated artwork without meaningful human authorship is not copyrightable in the US (Thaler v. Perlmutter, affirmed 2025; cert. denied March 2026). Trademark protection through use and registration remains available. The human vector-edit pass on the mark is therefore mandatory and must be recorded.
7. Decision: present the top three with all check results; the founder chooses. Secure domain and handles before announcement.
```

Add `"naming"` after `"discovery"` in both workspace `STAGES` lists and in the `$defs.stage.enum` list of `schemas/brand-manifest.schema.json`. Link the reference from `.agents/skills/brand-strategy-director/SKILL.md`.

- [ ] **Step 4: Quality reviewer and asset rules**

Add to `.agents/skills/brand-quality-reviewer/references/review-checklist.md` HIGH-severity checks:

```
- Trademark similarity search recorded in naming/checks.md for name, tagline and mark, with date and classes.
- Human vector-edit pass on the approved mark recorded (who, what changed, date); AI raster output alone is not an approved master.
- Mark legible at 16px favicon size and in monochrome positive and reversed.
```

Add to `.agents/skills/brand-asset-producer/references/asset-rules.md` after the raster rule: `- After AI-assisted generation, rebuild or edit the mark in a vector editor and record the edit pass in the asset manifest; the unedited generation is never the master.`

- [ ] **Step 5: Run and commit**

```bash
python3 -m pytest -q -p no:cacheprovider tests/brand_designer && python3 -m pytest -q -p no:cacheprovider
git add scripts/brand .agents/skills schemas tests/brand_designer/test_naming_checks.py
git commit -m "feat(brand): naming stage with domain, handle and trademark checks; human edit pass required"
```

### Task 21: Lean brand sprint as the default scope

**Finding:** Fourteen brand skills; component libraries, app screens and motion systems are product-UI work that a pre-validation founder should defer.

**Files:**
- Modify: `.agents/skills/brand-designer/references/workflow.md`
- Modify: `.agents/skills/brand-designer/references/routing.md`
- Modify: `.agents/skills/brand-designer/evals/evals.json` (one case)

- [ ] **Step 1: Add the default-scope rule**

Insert after the `Rules:` list in `.agents/skills/brand-designer/references/workflow.md`:

```markdown
Default scope (lean brand sprint): discovery → naming (if needed) → strategy → voice → logo system (primary, secondary, mark, monochrome, favicon) → color → typography → guidelines (short) → export/brand kit. Imagery style, motion, UI tokens, component libraries and app screens are opt-in stages the founder requests explicitly or a website/product build triggers; do not propose them by default before product-market fit.
```

Mark those stages `(opt-in)` in the pipeline line and in `references/routing.md`.

- [ ] **Step 2: Add an eval case**

Append to `.agents/skills/brand-designer/evals/evals.json` `evals`:

```json
{"id": "lean-1", "prompt": "I have a validated idea and need a brand for launch next month. Keep it minimal.",
 "expected_output": "Proposes the lean sprint (name check, strategy, voice, logo system, color, type, short guidelines, kit) and explicitly defers motion, components and app screens.",
 "must_mention": ["voice", "logo", "guidelines", "defer"], "must_not_mention": ["component library", "motion tokens"],
 "required_artifacts": [], "files": []}
```

- [ ] **Step 3: Validate and commit**

```bash
python3 scripts/run_evals.py && python3 -m pytest -q -p no:cacheprovider
git add .agents/skills/brand-designer
git commit -m "docs(brand): lean brand sprint is the default scope; UI and motion are opt-in"
```

---

## Phase 4 — Marketing and handoffs

### Task 22: Per-asset content brief contract

**Finding:** Organic plans lack the production brief per asset the founder asked for ("a video about X for YouTube, a carousel about Y for Instagram").

**Files:**
- Create: `schemas/content-brief.schema.json`
- Create: `templates/project/content-brief.md`
- Modify: `.agents/skills/social-digital-marketing-planner/references/workflow.md` (output contract)
- Test: `tests/test_content_brief_schema.py`

**Interfaces:**
- Schema required keys: `brief_id`, `platform`, `format`, `pillar`, `audience_segment`, `hook`, `key_message`, `proof`, `cta`, `conversion_bridge`, `kpi`, `owner`, `evidence_refs`, `brand_voice_ref`, `status`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_content_brief_schema.py`:

```python
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_content_brief_schema_accepts_minimal_brief_and_rejects_missing_kpi():
    import jsonschema
    schema = json.loads((ROOT / 'schemas/content-brief.schema.json').read_text())
    brief = {"brief_id": "CB-001", "platform": "youtube", "format": "video_8min", "pillar": "pain_education",
             "audience_segment": "expats in Germany choosing PKV", "hook": "You can lose your PKV refund by switching wrong",
             "key_message": "Three checks before you switch", "proof": "walkthrough of a real tariff comparison",
             "cta": "Book a 20-minute check", "conversion_bridge": "validation page /pkv-check",
             "kpi": {"name": "qualified calls booked", "target": 5, "window_days": 30},
             "owner": "founder", "evidence_refs": ["pain_points/runs/2026-09-20/evidence.jsonl#E12"],
             "brand_voice_ref": "branding/voice/voice.json", "status": "planned"}
    jsonschema.validate(brief, schema)
    del brief["kpi"]
    try:
        jsonschema.validate(brief, schema)
    except jsonschema.ValidationError:
        return
    raise AssertionError('kpi must be required')
```

(`jsonschema` is pinned in `requirements-dev.txt` and already imported by `scripts/strategy_review.py`.)

- [ ] **Step 2: Write the schema**

Create `schemas/content-brief.schema.json`:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "content-brief.schema.json",
  "type": "object",
  "additionalProperties": false,
  "required": ["brief_id", "platform", "format", "pillar", "audience_segment", "hook", "key_message", "proof", "cta",
               "conversion_bridge", "kpi", "owner", "evidence_refs", "brand_voice_ref", "status"],
  "properties": {
    "brief_id": {"type": "string", "pattern": "^CB-[0-9]{3,}$"},
    "platform": {"enum": ["youtube", "instagram", "tiktok", "linkedin", "x", "facebook", "reddit", "newsletter", "blog", "podcast", "other"]},
    "format": {"type": "string", "minLength": 1},
    "pillar": {"type": "string", "minLength": 1},
    "audience_segment": {"type": "string", "minLength": 1},
    "hook": {"type": "string", "minLength": 1},
    "key_message": {"type": "string", "minLength": 1},
    "proof": {"type": "string", "minLength": 1},
    "cta": {"type": "string", "minLength": 1},
    "conversion_bridge": {"type": "string", "minLength": 1},
    "kpi": {"type": "object", "required": ["name", "target", "window_days"], "additionalProperties": false,
            "properties": {"name": {"type": "string"}, "target": {"type": "number"}, "window_days": {"type": "integer", "minimum": 1}}},
    "owner": {"type": "string", "minLength": 1},
    "evidence_refs": {"type": "array", "items": {"type": "string"}},
    "brand_voice_ref": {"type": ["string", "null"]},
    "status": {"enum": ["planned", "in_production", "published", "measured", "dropped"]},
    "publish_window": {"type": "string"},
    "notes": {"type": "string"}
  }
}
```

- [ ] **Step 3: Template and workflow contract**

Create `templates/project/content-brief.md` with one heading per required key in the same order, each followed by a one-line instruction (hook: first three seconds or first line; proof: only what the owner can show; conversion bridge: exact page or step; KPI: name, target, window).

Append to `.agents/skills/social-digital-marketing-planner/references/workflow.md` under `## Content System`:

```
Every planned asset is one content brief validated against `schemas/content-brief.schema.json` and stored under `marketing/briefs/<brief_id>.json` with a Markdown twin from `templates/project/content-brief.md`. A calendar is a list of brief IDs with publish windows. Do not deliver post ideas without a brief.
```

In `scripts/validate_setup.sh` append `content-brief` to the `for schema in evidence-record ads-record competitor ... strategy-plan; do` list under `--- Schemas ---` so the existence and valid-JSON checks cover it.

- [ ] **Step 4: Run and commit**

```bash
python3 -m pytest -q -p no:cacheprovider tests/test_content_brief_schema.py && bash scripts/validate_setup.sh
git add schemas/content-brief.schema.json templates/project/content-brief.md .agents/skills/social-digital-marketing-planner scripts/validate_setup.sh tests/test_content_brief_schema.py
git commit -m "feat(marketing): per-asset content brief schema and template"
```

### Task 23: Paid campaign planning reference

**Finding:** Paid planning is a ten-line execution note. No channel selection logic, learning-phase feasibility, structure, creative matrix, measurement or stop rules; "Performance Max" appears nowhere.

**Files:**
- Create: `.agents/skills/social-digital-marketing-planner/references/paid-campaign-planning.md`
- Modify: `.agents/skills/social-digital-marketing-planner/SKILL.md` (link in step 3)
- Modify: `.agents/skills/social-digital-marketing-planner/references/campaign-execution.md` (first line pointer)
- Modify: `.agents/skills/social-digital-marketing-planner/evals/evals.json` (one case)
- Test: `tests/test_skill_hygiene.py` (reference exists and is linked)

- [ ] **Step 1: Write the failing test**

Append to `tests/test_skill_hygiene.py`:

```python
def test_paid_campaign_reference_exists_and_is_linked():
    skill = SKILLS / 'social-digital-marketing-planner'
    ref = skill / 'references/paid-campaign-planning.md'
    assert ref.exists()
    assert 'paid-campaign-planning.md' in (skill / 'SKILL.md').read_text()
    text = ref.read_text()
    for needle in ['Performance Max', 'learning', '50', 'consent', 'stop rule']:
        assert needle in text
```

- [ ] **Step 2: Write the reference**

Create `.agents/skills/social-digital-marketing-planner/references/paid-campaign-planning.md`:

```markdown
# Paid campaign planning

Use for any paid plan or budget question. Retrieve current platform documentation before quoting thresholds; the figures below are planning anchors checked 2026-09-24 and must be re-verified and dated in the output.

## 1. Preconditions
Conversion path live and measured (event names, consent, UTM), message-market fit from the smoke test or organic learning, unit economics that define an affordable CPA. Without retained-value evidence the plan is a capped learning experiment with unlock gates, never a scaling plan.

## 2. Channel selection
Decide by intent and audience access, not habit:
- Google Search: explicit problem/category intent exists (verify with keyword research). Start with exact/phrase match on problem terms; brand terms only if competitors bid on them.
- Performance Max: only with a proven conversion signal and feed/asset volume; Google guidance expects roughly six weeks before judging.
- Meta (Facebook/Instagram): demand creation for consumer and local services, retargeting, older audiences; needs creative volume.
- LinkedIn: B2B titles and firm size; high CPC, use for narrow high-value segments or retargeting.
- TikTok/YouTube: discovery and education with native video; needs sustained creative cadence.
Name one primary channel and at most one supporting channel; defer the rest with reasons.

## 3. Learning-phase feasibility
- Meta: about 50 optimization events per ad set per week to exit learning; daily budget per ad set ≈ target CPA × 50 ÷ 7. Fewer ad sets with pooled budget exit faster. Budget changes above ~20% or targeting edits reset learning.
- Google Smart Bidding: judge Target CPA over at least ~30 conversions, Target ROAS over ~50; learning typically one to two conversion cycles. AI Max for Search: roughly a $50/day floor per current guidance.
If the formula exceeds the affordable spend, choose an upstream optimization event (lead, booked call), consolidate ad sets, extend the window, or conclude the channel is not viable for this offer. Do not spend more to satisfy the algorithm.

## 4. Structure
One campaign per objective; one ad set/ad group per distinct audience or intent theme; three to five ads per ad set; one landing page per message variant with message match. Name everything `channel_objective_audience_variant_date`.

## 5. Creative test matrix
Rows: pain frames from the smoke test variants. Columns: format (static, short video, carousel). Test one variable at a time; kill a cell after the minimum sample defined in the plan, not after a day.

## 6. Measurement
GA4 or the chosen analytics with consent mode v2 for EU traffic; server-side or offline conversion import for booked/attended calls; UTM discipline; platform attribution is diagnostic, incrementality or holdout is the truth when spend is meaningful.

## 7. Budget and stop rules
Total learning budget, daily cap, duration, and the decision it informs are written in `budget-approval.json` (see references/smoke-test.md) and approved by the founder before launch. Stop rules: CPA above affordable ceiling after the minimum sample; learning-limited after budget consolidation; qualified-lead rate below threshold; landing page conversion below the smoke-test baseline (fix page before buying more traffic).

Sources to re-check each run: Meta Business Help Center (learning phase), Google Ads Help (Smart Bidding, Performance Max), platform policy pages for the category.
```

- [ ] **Step 3: Link and eval**

In `.agents/skills/social-digital-marketing-planner/SKILL.md` step 3 append: `For channel choice, budget sizing, structure and stop rules read [paid campaign planning](references/paid-campaign-planning.md) first.` Prepend to `campaign-execution.md`: `Plan first with references/paid-campaign-planning.md.`

Append to `.agents/skills/social-digital-marketing-planner/evals/evals.json` `evals`:

```json
{"id": "paid-1", "prompt": "I have EUR 600 for ads to test my PKV switching service for expats. Where should I spend it?",
 "expected_output": "Chooses one channel by intent, sizes the budget against learning-phase thresholds, proposes an upstream optimization event, ties it to the validation page, and writes stop rules and an approval record.",
 "must_mention": ["learning", "optimization event", "stop rule", "approval", "landing page"],
 "must_not_mention": ["spread across all platforms"], "required_artifacts": [], "files": []}
```

- [ ] **Step 4: Run and commit**

```bash
python3 -m pytest -q -p no:cacheprovider tests/test_skill_hygiene.py && python3 scripts/run_evals.py
git add .agents/skills/social-digital-marketing-planner tests/test_skill_hygiene.py
git commit -m "feat(marketing): paid campaign planning reference with learning-phase feasibility and stop rules"
```

### Task 24: Keyword research ownership

**Finding:** Technical SEO lives in the website skill and question mining in its GEO reference, but no skill owns keyword-to-page mapping using the existing search scripts.

**Files:**
- Create: `.agents/skills/marketing-strategy-builder/references/keyword-research.md`
- Modify: `.agents/skills/marketing-strategy-builder/SKILL.md` (link)
- Modify: `.agents/skills/brand-website-designer-builder/references/content-and-conversion.md` (consume the map)
- Test: `tests/test_skill_hygiene.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_skill_hygiene.py`:

```python
def test_keyword_research_is_owned_by_marketing_and_consumed_by_website():
    ref = SKILLS / 'marketing-strategy-builder/references/keyword-research.md'
    assert ref.exists() and 'serper_fetch.py' in ref.read_text()
    assert 'keyword-research.md' in (SKILLS / 'marketing-strategy-builder/SKILL.md').read_text()
    assert 'keyword-map.json' in (SKILLS / 'brand-website-designer-builder/references/content-and-conversion.md').read_text()
```

- [ ] **Step 2: Write the reference**

Create `.agents/skills/marketing-strategy-builder/references/keyword-research.md`:

```markdown
# Keyword research and keyword-to-page map

Owner: marketing-strategy-builder. Consumer: brand-website-designer-builder (content architecture) and social-digital-marketing-planner (search ads).

1. Seed terms: problem, workaround and search-intent keywords from idea-grill and the evidence run; competitor names from the landscape. Never use segment prose as a keyword.
2. Expand: `python3 scripts/serper_fetch.py` for SERP features and related searches; `collect.py --providers google_autocomplete`; Google Trends only as a relative-demand proxy. Record query, locale, date and raw results under `marketing/keywords/raw/`.
3. Classify each term: intent (informational, comparison, transactional, navigational), funnel stage, SERP shape (AI Overview present, video, local pack), and who ranks (incumbents, forums, marketplaces). A forum-dominated SERP signals an unanswered question; an incumbent-dominated one signals a trust bar.
4. Cluster into topics; assign one primary page per cluster with page type (landing, guide, comparison, FAQ) and the conversion bridge.
5. Output `marketing/keywords/keyword-map.json`: list of `{cluster, primary_term, secondary_terms, intent, stage, serp_notes, page_type, target_url, priority, evidence_refs, checked_at}` plus a Markdown summary. Volume numbers are provider estimates; label them.
6. Hand off: the website skill builds pages from the map; search-ads planning uses transactional clusters only.
```

Link from SKILL.md: `For keyword research and the keyword-to-page map read [keyword research](references/keyword-research.md).`

In `.agents/skills/brand-website-designer-builder/references/content-and-conversion.md` add: `When `marketing/keywords/keyword-map.json` exists, derive page inventory and headings from its clusters; otherwise record the missing map as an owner action rather than inventing keywords.`

- [ ] **Step 3: Run and commit**

```bash
python3 -m pytest -q -p no:cacheprovider tests/test_skill_hygiene.py
git add .agents/skills/marketing-strategy-builder .agents/skills/brand-website-designer-builder tests/test_skill_hygiene.py
git commit -m "feat(marketing): keyword research owner and keyword-to-page map contract"
```

### Task 25: Cross-module handoff contract

**Finding:** Business→Brand and Brand→Website handoffs are concrete; Business→Marketing is thin; Brand→Marketing and Website→Marketing are implicit.

**Files:**
- Modify: `references/subprojects.md` (new `## Handoff contract` table)
- Modify: `schemas/marketing-workstream.schema.json` (`imported_decisions[].purpose` enum)
- Modify: `references/modules/marketing.md` (consume voice and keyword map)
- Test: `tests/test_gap_closure.py`

**Interfaces:**
- `imported_decisions[].purpose` enum: `positioning`, `segment_and_pain`, `customer_language`, `brand_voice`, `brand_assets`, `keyword_map`, `validation_page`, `experiment_results`.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_gap_closure.py`:

```python
def test_handoff_contract_table_and_purpose_enum():
    import json
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    text = (root / 'references/subprojects.md').read_text()
    assert '## Handoff contract' in text
    for pair in ['Business → Marketing', 'Brand → Marketing', 'Brand → Website', 'Website → Marketing', 'Business → Brand']:
        assert pair in text
    schema = json.loads((root / 'schemas/marketing-workstream.schema.json').read_text())
    purpose = schema['properties']['imported_decisions']['items']['properties']['purpose']
    assert set(purpose['enum']) >= {'positioning', 'brand_voice', 'keyword_map', 'validation_page'}
```

- [ ] **Step 2: Add the table**

Append to `references/subprojects.md`:

```markdown
## Handoff contract

Each handoff is an explicit import with owner, path, hash and applicability. Consumers reject stale hashes and recheck applicability against the current task.

| Handoff | Artifact | Producer | Consumer | Staleness check |
|---|---|---|---|---|
| Business → Brand | `branding/business-to-brand-*.json` (schema `business-to-brand.schema.json`) | startup-business-builder via `build_business_to_brand_handoff.py` | brand-designer | `validate_business_to_brand_handoff.py --check-sources` |
| Business → Marketing | `strategy-plan.json` positioning + `customer-voc-synthesis.json` customer language | archetype-gtm-strategist / evidence-scout | marketing-strategy-builder, social-digital-marketing-planner | `imported_decisions` hash + `applicability` review |
| Brand → Marketing | `branding/voice/voice.json`, asset manifest | brand-strategy-director / brand-exporter | both marketing skills (`brand_voice_ref` in content briefs) | `imported_decisions` purpose `brand_voice`/`brand_assets` |
| Brand → Website | tokens, `brand_refs`, favicon package | brand-exporter / brand-asset-producer | brand-website-designer-builder | `website-manifest.json` `brand_refs` hashes |
| Marketing → Website | `marketing/keywords/keyword-map.json` | marketing-strategy-builder | brand-website-designer-builder | `checked_at` older than 90 days → owner action |
| Website → Marketing | validation page URL, event names, variant mapping | brand-website-designer-builder | social-digital-marketing-planner (paid), opportunity-risk-designer (smoke test) | `imported_decisions` purpose `validation_page` |
| Experiments → Business | `experiments/*/results.json`, responder tracker | opportunity-risk-designer / interview-bridge | case appraisal, startup-business-builder | case `source_bindings` digest |
```

- [ ] **Step 3: Schema enum and module note**

In `schemas/marketing-workstream.schema.json` change `imported_decisions.items.properties.purpose` to `{"enum": ["positioning", "segment_and_pain", "customer_language", "brand_voice", "brand_assets", "keyword_map", "validation_page", "experiment_results"]}`. Run the existing marketing lifecycle test; the fixture already uses `positioning`.

Append to `references/modules/marketing.md`: `Consume brand voice (`voice.json`) and the keyword map through imported decisions with purposes `brand_voice` and `keyword_map`; when absent, record the gap as an owner action instead of inventing tone or keywords.`

- [ ] **Step 4: Run and commit**

```bash
python3 -m pytest -q -p no:cacheprovider tests/test_gap_closure.py && bash scripts/validate_setup.sh && python3 -m pytest -q -p no:cacheprovider
git add references/subprojects.md references/modules/marketing.md schemas/marketing-workstream.schema.json tests/test_gap_closure.py
git commit -m "feat(subprojects): explicit cross-module handoff contract and import purposes"
```

---

## Phase 5 — Optional consolidation (decide before starting)

### Task 26: Fold `social-media-idea-validator` into the planner as a gate

Only run after Phases 0–4 are green. This removes one skill directory, so every step must keep `tests/test_skill_route_coverage.py` green.

**Files:**
- Move: `.agents/skills/social-media-idea-validator/references/{workflow,founder-playbooks}.md` → `.agents/skills/social-digital-marketing-planner/references/idea-gate.md` and `founder-playbooks.md`
- Delete: `.agents/skills/social-media-idea-validator/`
- Modify: `config/skill-catalog.json` (remove skill; add mode `idea_gate` to planner), `config/workflow-routes.json` (route `social-media-idea-validator` → skill `social-digital-marketing-planner`, mode `idea_gate`), `config/routing-evals.json` (expected skill), `.agents/skills/marketing-strategy-builder/references/workflow.md` (two path references), `scripts/run_behavioral_evals.py` if it names the skill.

- [ ] **Step 1: Grep every reference**

Run: `grep -rn "social-media-idea-validator" --include=*.md --include=*.json --include=*.py . --exclude-dir=projects --exclude-dir=.git --exclude-dir=archive`

- [ ] **Step 2: Move references and update the two config files as described above; keep the route id so existing prompts still resolve**
- [ ] **Step 3: Run `python3 scripts/validate_skill_routes.py && python3 scripts/run_evals.py && python3 -m pytest -q -p no:cacheprovider`**
- [ ] **Step 4: Commit** `refactor(skills): social-media-idea-validator becomes the planner's idea gate`

### Deferred decisions (not planned here)

- Merging the three competitor skills and the three niche strategy skills: same procedure as Task 26, one skill per commit. Decide after observing routing mis-hits with the live evals from Task 12.
- Making Ed25519 community-promotion signing optional for solo use: security-design change; needs an explicit decision on what the local-only mode may unlock.
- Packaging the skill set as a Claude Code plugin for reuse across projects.

---

## Self-review

- Spec coverage: red suite (T1–T3), hook timeouts (T4), dispatch error (T5), SubagentStop (T6), duplicate frontmatter/boilerplate (T7), paid-spend contradiction (T8), AGENTS.md size (T9), permissions (T10), subagents/agent-modes (T11), behavioral evals (T12), docs bloat (T13), smoke test path (T14–T16), viability criterion (T17), DFV scorecard (T18), verbal identity (T19), naming/trademark/human edit (T20), lean brand default (T21), asset briefs (T22), paid planning (T23), keyword ownership (T24), handoffs (T25), skill overlap (T26 + deferred). Ceremony reduction and plugin packaging are explicitly deferred.
- Placeholder scan: markdown content tasks give the actual text; code tasks give the code; angle-bracket fields inside generated templates are intentional user-fill slots, not plan placeholders.
- Type consistency: route tests call `route_request` only with kwargs it accepts today (`intent`, `task_scope`, `check_skill`, `project`, `entry_mode`, `standalone_brief`); `results.viability` keys match between T17 implementation, tests and template placeholders; content-brief keys match between schema, test and template; `budget-approval.json` shape matches between T14 and T23.
