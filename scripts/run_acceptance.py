#!/usr/bin/env python3
"""End-to-end acceptance run: a founder scenario driven headlessly through `claude -p`, then scored.

The run happens in a disposable detached git worktree of --ref (default HEAD; the baseline uses
486a7ae). The eval project is an ordinary top-level project, projects/eval-<scenario>-<timestamp>/, so the
router and the pain-first gate treat it exactly like a real project; the scenario is copied to its scenario/ inside that worktree,
plus a read-only copy of the reference project's manifests so the workspace check has something to
offer. Intake questions are answered from founder-answers.json by resuming the session. Produced files
are copied from the eval project directories only; the worktree is always removed.

--dry-run creates and removes the worktree, prints planned writes, and runs no model and no provider.
A live run spends model tokens (capped by --model-budget-usd) and paid evidence APIs. Provider spend
cannot be enforced inside the tree under test: the cap is stated in the prompt and spend is measured
before/after from provider account endpoints and recorded in the scorecard.

Model cost: `total_cost_usd` is session-cumulative across `--resume` and repeats on every result event (one
round can emit several, e.g. background-agent notifications), as the 7.2 smoke run showed. Model cost is
therefore the maximum `total_cost_usd` per session; per-round cost is the difference of consecutive maxima.
Whether `--max-budget-usd` caps one invocation or the whole session is unverified; the runner takes the safer
reading and passes the remaining budget (model budget minus cumulative cost) on every round, which is
correct if the cap is per invocation and stricter than needed if it is per session.
A round killed on timeout may emit no result event, so its cost can be unreported.

Bash permissions: ALLOWED_TOOLS grants `Bash(python3 *)`, which by itself allows `python3 -c "import runpy; ..."`
or any other interpreter one-liner. Such a command can run a denylisted script without naming its path in a
form a deny rule or the Bash guard can match. That is a pre-existing hole the denylist cannot close; the guard
(see bash_guard_output) never approves anything and only denies, rewrites a plain `cd <dir> &&` prefix, or defers.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCENARIO = ROOT / 'evals/acceptance/hybrid-insurance-advisor'
SCHEMA_PATH = ROOT / 'evals/acceptance/scorecard.schema.json'
BASELINE_REF = '486a7ae'
HARD_BUDGET_CEILING_USD = 50.0  # refuse to start above this, for provider and model budgets alike
COMBINED_BUDGET_CEILING_USD = 65.0  # and when provider + model budget together exceed this
MAX_ROUNDS = 12
ROUND_TIMEOUT_S = 45 * 60
WALL_CAP_S = 4 * 60 * 60
MIN_ROUND_BUDGET_USD = 0.5
REFERENCE_PROJECT_SLUG = 'german-insurance-opportunity'
EVAL_PROJECT_PREFIX = 'eval-'  # eval projects are ordinary top-level projects: projects/eval-<scenario>-<timestamp>/
MIGRATION_COORDINATION = '_infra/layout-migrations'  # relative to projects/; see scripts/layout_migration.py
REFERENCE_SEED_FILES = (
    'project-manifest.json',
    'business-analysis/project-manifest.json',
    'business-analysis/cases/surelius/market_research/manifest.json',
    'business-analysis/cases/surelius/case_insights.md',
)
COPY_SKIP_DIRS = {'node_modules', '.next', '.git', '.turbo', '.cache', '.vercel'}
TEXT_SUFFIXES = {'.md', '.json', '.jsonl', '.txt', '.html', '.csv', '.yaml', '.yml', '.tsx', '.ts', '.mdx'}
MAX_READ_BYTES = 5_000_000

ALLOWED_TOOLS = [
    'Read', 'Glob', 'Grep', 'WebSearch', 'WebFetch', 'Skill', 'Agent', 'Task', 'TodoWrite',
    'Bash(python3 *)', 'Bash(python *)', 'Bash(bash scripts/*)', 'Bash(ls *)', 'Bash(cat *)', 'Bash(head *)',
    'Bash(tail *)', 'Bash(wc *)', 'Bash(find *)', 'Bash(grep *)', 'Bash(rg *)', 'Bash(sed -n *)', 'Bash(jq *)',
    'Bash(sort *)', 'Bash(uniq *)', 'Bash(date*)', 'Bash(pwd)', 'Bash(echo *)', 'Bash(mkdir *)', 'Bash(cp *)',
    'Bash(mv *)', 'Bash(touch *)', 'Bash(test *)', 'Bash(diff *)', 'Bash(git status*)', 'Bash(git diff*)',
    'Bash(git log*)', 'Bash(node *)', 'Bash(npm *)', 'Bash(npx *)',
    'mcp__brave-search', 'mcp__firecrawl', 'mcp__dialog-mcp', 'mcp__apify',
]
# Anything that deploys, sends, publishes, writes to an external account or generates paid assets.
DISALLOWED_TOOLS = [
    'Artifact', 'ArtifactComments', 'ArtifactData', 'RemoteTrigger', 'CronCreate', 'CronDelete',
    'PushNotification', 'SendUserMessage', 'Skill(schedule)', 'Skill(loop)',
    'mcp__claude_ai_Gmail', 'mcp__claude_ai_Google_Calendar', 'mcp__claude_ai_Google_Drive',
    'mcp__claude_ai_Claude_Docs',
    'mcp__firecrawl__firecrawl_monitor_create', 'mcp__firecrawl__firecrawl_monitor_update',
    'mcp__firecrawl__firecrawl_monitor_delete', 'mcp__firecrawl__firecrawl_monitor_run',
    'mcp__firecrawl__firecrawl_interact', 'mcp__firecrawl__firecrawl_feedback',
    'mcp__firecrawl__firecrawl_search_feedback',
    'Bash(git push*)', 'Bash(git commit*)', 'Bash(git remote*)', 'Bash(git rev-parse*)', 'Bash(gh *)', 'Bash(curl*)', 'Bash(wget*)',
    'Bash(vercel*)', 'Bash(npx vercel*)', 'Bash(netlify*)', 'Bash(npx netlify*)', 'Bash(wrangler*)',
    'Bash(npx wrangler*)', 'Bash(firebase*)', 'Bash(npx firebase*)', 'Bash(npm publish*)',
    'Bash(python3 scripts/fal_assets.py*)', 'Bash(python3 scripts/brand/finalize_fal_assets.py*)',
    'Bash(python3 scripts/brand/indexnow_ping.py*)', 'Bash(python3 scripts/marketing/execute.py*)',
]


# --------------------------------------------------------------------------- subagent Bash guard
# Research subagents wrote `cd <dir> && python3 scripts/...`; Claude Code matched the `cd` part against no allow
# rule and, with --permission-prompts none, denied the whole call (Task 7.3 audit, root cause 3). A PreToolUse hook
# (installed by claude_command) narrows that one shape. The guard NEVER returns permissionDecision "allow": an
# allow would skip Claude Code's own Bash safety checks. Its only powers are:
#   1. deny a command that mentions a denylisted script in any form (path, ./, absolute, python -m, after a cd);
#   2. rewrite exactly `cd <plain path inside the worktree> && <rest>` to `<rest>` via updatedInput, with no
#      permissionDecision, so Claude Code evaluates its normal allow/deny rules against <rest>;
#   3. otherwise return nothing (defer to Claude Code's rules; in headless runs an unmatched command is denied).
# DISALLOWED_TOOLS remains authoritative: deny rules apply whatever a hook returns.
# Pre-existing hole the denylist cannot close: `Bash(python3 *)` itself allows `python3 -c "import runpy; ..."`
# (or any interpreter one-liner) to run a denylisted script without naming its path in a matchable form.

DENIED_SCRIPTS = [m.group(1) for r in DISALLOWED_TOOLS for m in [re.fullmatch(r'Bash\(python3? (scripts/\S+\.py)\*?\)', r)] if m]
CD_PREFIX_RE = re.compile(r'\A\s*cd\s+([A-Za-z0-9_.][A-Za-z0-9_./-]*|/[A-Za-z0-9_./-]+)\s*&&\s*(\S.*)\Z', re.S)
REST_UNSAFE_RE = re.compile(r'[`\n\r]|\$\(|<\(|>\(|\|\s*(sh|bash|zsh|dash|eval|xargs|source)\b|^\s*cd\b')
CREATING_CMDS = {'mkdir', 'touch', 'cp', 'mv', 'rm', 'tee', 'ln', 'rsync', 'install', 'dd', 'unzip', 'tar'}


def _denied_script_forms(script: str) -> list[re.Pattern]:
    """Every spelling of a denylisted script: scripts/a/b.py, a/b.py, a.b module, and its file name."""
    rel = script[len('scripts/'):] if script.startswith('scripts/') else script
    parts = rel[:-3].split('/')
    forms = [re.escape(rel), re.escape('.'.join(parts)) + r'\b']
    if len(parts) == 1:
        forms.append(re.escape(parts[0]) + r'\b')  # top-level script names are distinctive
    else:  # a nested name (execute.py) counts when its directory is also named (after a `cd`)
        forms.append(r'(?=.*\b' + re.escape(parts[-2]) + r'\b).*\b' + re.escape(parts[-1]) + r'\.py\b')
    return [re.compile(f, re.S) for f in forms]


DENIED_FORMS = [(s, f) for s in DENIED_SCRIPTS for f in _denied_script_forms(s)]


def _has_unquoted(command: str, chars: str) -> bool:
    quote = ''
    escaped = False
    for ch in command:
        if escaped:
            escaped = False
        elif ch == '\\' and quote != "'":
            escaped = True
        elif quote:
            quote = '' if ch == quote else quote
        elif ch in ('"', "'"):
            quote = ch
        elif ch in chars:
            return True
    return False


def _within(path: str, root: str) -> bool:
    try:
        return os.path.commonpath([os.path.realpath(path), os.path.realpath(root)]) == os.path.realpath(root)
    except ValueError:
        return False


def bash_guard_output(tool_input: dict, root: str, cwd: str | None = None) -> tuple[dict | None, str]:
    """(hook output or None, reason). Never contains permissionDecision "allow"."""
    command = str(tool_input.get('command') or '')
    root = str(root)
    cwd = cwd if cwd and _within(cwd, root) else root
    hits = sorted({s for s, rx in DENIED_FORMS if rx.search(command)})
    if hits:
        reason = 'acceptance harness denylist: ' + ', '.join(hits)
        return {'hookSpecificOutput': {'hookEventName': 'PreToolUse', 'permissionDecision': 'deny',
                                       'permissionDecisionReason': reason}}, reason
    m = CD_PREFIX_RE.match(command)
    if not m:
        return None, 'defer: not a cd-prefixed command'
    target, rest = m.group(1), m.group(2).strip()
    if '..' in target.split('/') or REST_UNSAFE_RE.search(rest) or _has_unquoted(command, '#'):
        return None, 'defer: unsafe cd target or rest'
    dest = os.path.realpath(os.path.join(cwd, target))
    if not _within(dest, root):
        return None, 'defer: cd target outside the eval worktree'
    try:
        lex = shlex.shlex(rest, posix=True, punctuation_chars=True)
        lex.whitespace_split = True
        lex.commenters = ''
        tokens = list(lex)
    except ValueError:
        return None, 'defer: unparsable rest'
    if dest != os.path.realpath(cwd):
        # Dropping a cd into a subdirectory changes what relative paths mean. Rewrite only when nothing in
        # <rest> names an existing path relative to the cd target and <rest> does not create files.
        if any(t in CREATING_CMDS for t in tokens):
            return None, 'defer: rest creates files relative to the cd target'
        if any(t not in ('.', '..') and not t.startswith('-') and os.path.lexists(os.path.join(dest, t)) for t in tokens):
            return None, 'defer: rest names paths relative to the cd target'
    return {'hookSpecificOutput': {'hookEventName': 'PreToolUse', 'updatedInput': {**tool_input, 'command': rest}}}, \
        'rewrite: cd prefix dropped; normal permission rules evaluate the rest'


def bash_guard_hook(root: str, stdin=None) -> int:
    """PreToolUse hook entry point: print a deny or a rewrite, or nothing to defer."""
    try:
        payload = json.load(stdin or sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0
    if payload.get('tool_name') != 'Bash' or not isinstance(payload.get('tool_input'), dict):
        return 0
    output, _ = bash_guard_output(payload['tool_input'], root, cwd=payload.get('cwd'))
    if output:
        print(json.dumps(output))
    return 0


def bash_guard_settings(wt: Path) -> str:
    command = f'python3 {shlex.quote(str(Path(__file__).resolve()))} --bash-guard {shlex.quote(str(wt))}'
    return json.dumps({'hooks': {'PreToolUse': [{'matcher': 'Bash', 'hooks': [{'type': 'command', 'command': command}]}]}})


INTAKE_PATTERN = re.compile(r'(?i)(which path|continue \[\d\]|please (confirm|choose|tell me)|let me know (which|whether|if)'
                            r'|do you want|would you like|shall i|should i)')


# --------------------------------------------------------------------------- utilities

def now_iso() -> str:
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def _git(args: list[str], cwd: Path = ROOT, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(['git', *args], cwd=cwd, check=check, capture_output=True, text=True)


def host_repo_roots() -> list[Path]:
    """The runner's checkout and the main checkout behind it (when ROOT is itself a worktree)."""
    roots = {ROOT}
    try:
        common = Path(_git(['rev-parse', '--path-format=absolute', '--git-common-dir'], check=False).stdout.strip())
        if common.name == '.git':
            roots.add(common.parent)
    except Exception:
        pass
    return sorted(roots)


def default_reference_project() -> Path:
    for root in reversed(host_repo_roots()):
        candidate = root / 'projects' / REFERENCE_PROJECT_SLUG
        if candidate.is_dir():
            return candidate
    return ROOT / 'projects' / REFERENCE_PROJECT_SLUG


def check_budgets(budget_usd: float, model_budget_usd: float) -> None:
    for name, value in (('budget_usd', budget_usd), ('model_budget_usd', model_budget_usd)):
        if not isinstance(value, (int, float)) or value <= 0:
            raise ValueError(f'{name} must be a positive number')
        if value > HARD_BUDGET_CEILING_USD:
            raise ValueError(f'{name}={value} exceeds the hard ceiling of {HARD_BUDGET_CEILING_USD} USD; refusing to start')
    if budget_usd + model_budget_usd > COMBINED_BUDGET_CEILING_USD:
        raise ValueError(f'provider + model budget {budget_usd + model_budget_usd:g} USD exceeds the combined ceiling of '
                         f'{COMBINED_BUDGET_CEILING_USD} USD; refusing to start')


def blocked_tools(host_roots: Iterable[Path]) -> list[str]:
    host = []
    for root in host_roots:
        host += [f'Edit(/{root}/**)', f'Write(/{root}/**)']  # `//abs/path` form: never edit the host checkouts
        host += [f'Read(/{root}/{HIDDEN_TREE}/**)']  # nor read the scoring rules/answers from the runner's repo
    return [*DISALLOWED_TOOLS, *host]


# --------------------------------------------------------------------------- scenario and feeder

def load_prompt(scenario_dir: Path, *, budget_usd: float, eval_dir: str, alt_slug: str) -> str:
    text = (scenario_dir / 'scenario.md').read_text(encoding='utf-8').strip()
    return text.replace('{budget_usd}', f'{budget_usd:g}').replace('{eval_dir}', eval_dir).replace('{alt_slug}', alt_slug)


def sentences(text: str) -> list[str]:
    cleaned = re.sub(r'https?://\S+', 'URL', text)
    cleaned = re.sub(r'[*_`>#]', '', cleaned)
    return [s.strip() for s in re.split(r'(?<=[.!?])\s+|\n+', cleaned) if s.strip()]


def question_sentences(text: str) -> list[str]:
    return [s for s in sentences(text) if s.rstrip(' )"\'').endswith('?')]


def count_questions(text: str) -> int:
    return len(question_sentences(text))


LIST_ITEM = re.compile(r'^\s*(\d+[.)]|[-*+•])\s+')
CONTINUATION_Q = re.compile(r'(?i)^(or|if not|if so|otherwise|alternatively|and if|failing that)\b')


def count_question_blocks(text: str) -> int:
    """Questions about one decision count once.

    A block is a run of consecutive question sentences within one paragraph (blank lines and list items
    start a new paragraph); a later question in the same paragraph that opens with Or / If not / Otherwise /
    Alternatively continues the current block. Whether two questions really concern the same decision is
    left to the blinded grader; this is the deterministic proxy."""
    cleaned = re.sub(r'https?://\S+', 'URL', text)
    paragraphs: list[list[str]] = [[]]
    for line in cleaned.splitlines():
        if not line.strip() or LIST_ITEM.match(line):
            paragraphs.append([])
        if line.strip():
            paragraphs[-1].append(line)
    blocks = 0
    for para in paragraphs:
        open_block, seen_q = False, False
        for s in sentences(' '.join(para)):
            is_q = s.rstrip(' )"\'').endswith('?')
            if not is_q:
                open_block = False
                continue
            if not (open_block or (seen_q and CONTINUATION_Q.match(s))):
                blocks += 1
            open_block = seen_q = True
    return blocks


PRIVATE_ANSWERS = 'founder-answers.private.json'
# Only the founder brief reaches the agent: scripted answers and scoring rules stay with the runner.
SCENARIO_COPY_FILES = ('scenario.md',)
HIDDEN_TREE = 'evals/acceptance'


def load_answers(path: Path, private_path: Path | None = None) -> dict:
    """Tracked answers merged with the gitignored private file (if present) via each entry's private_ref."""
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    private_path = Path(private_path) if private_path else Path(path).with_name(PRIVATE_ANSWERS)
    private = {}
    if private_path.is_file():
        private = json.loads(private_path.read_text(encoding='utf-8')).get('answers', {})
    for entry in data.get('answers', []):
        ref = entry.get('private_ref')
        value = private.get(ref) if ref else None
        if isinstance(value, dict) and value.get('answer'):
            entry['answer'] = value['answer']
            entry['persist_markers'] = list(value.get('persist_markers', []))
            entry['private'] = True
    return data


def _kw_hit(keyword: str, text: str) -> bool:
    kw = keyword.lower()
    right = r'(?![a-z0-9])' if kw[-1:].isalnum() else ''  # whole words; 'invest' must not match 'investigate'
    return re.search(r'(?<![a-z0-9])' + re.escape(kw) + right, text) is not None


GATE_CUE = re.compile(r'(?i)(override|pain[- ]first|problem_validation)')
OPTIONS_LIST = re.compile(r'(?m)^\s*\d+[.)]\s+\S')
OPTIONS_CUE = re.compile(r"(?i)(your call|option|choose|which|tell me|what i need from you|say:|decide|decision)")


def offers_options(text: str) -> bool:
    """A numbered options list (two or more items) next to a choice cue, as in 'Your call: 1. ... 2. ...'."""
    return len(OPTIONS_LIST.findall(text)) >= 2 and OPTIONS_CUE.search(text) is not None


INTAKE_CAP_AFTER = 4  # answered intake rounds before the feeder stops inviting more questions
INTAKE_CAP_TEXT = 'No more intake questions; proceed under stated assumptions through all remaining steps.'


class Feeder:
    """Answers the agent's end-of-turn questions from founder-answers.json by keyword match."""

    def __init__(self, data: dict, *, eval_dir: str, alt_slug: str, budget_usd: float):
        self.data = data
        self.subs = {'{eval_dir}': eval_dir, '{alt_slug}': alt_slug, '{budget_usd}': f'{budget_usd:g}'}
        self.nudges_left = int(data.get('nudge', {}).get('max', 4))
        self.marker = str(data.get('completion_marker', 'journey complete')).lower()
        self.intake_answers = 0

    @classmethod
    def load(cls, path: Path, private_path: Path | None = None, **kwargs) -> 'Feeder':
        return cls(load_answers(path, private_path), **kwargs)

    def _fill(self, text: str) -> str:
        for key, value in self.subs.items():
            text = text.replace(key, value)
        return text

    def entry(self, entry_id: str) -> dict | None:
        return next((e for e in self.data.get('answers', []) if e.get('id') == entry_id), None)

    def match(self, text: str) -> list[dict]:
        tail = text[-1500:]
        questions = question_sentences(text)[-2:]  # only the closing question(s) of the final message
        # The gate counts as asked only when the closing question(s) (or, without one, the last 400 characters)
        # raise it: an earlier mention of "override" must not hijack an intake question.
        closing = ' '.join(questions) or text[-400:]
        gate_asked = GATE_CUE.search(closing) is not None
        whole = offers_options(tail) or gate_asked
        # Options lists and gate requests are often not phrased as questions: match the whole final message then.
        context = text if whole else (' '.join(questions) if questions else text[-600:])
        context = context.lower()
        scored = []
        for order, entry in enumerate(self.data.get('answers', [])):
            hits = sum(_kw_hit(k, context) for k in entry.get('keywords', []))
            if hits:
                scored.append((-hits, order, entry))
        ranked = [e for _, _, e in sorted(scored, key=lambda t: (t[0], t[1]))]
        gate = [e for e in ranked if e.get('id') == 'gate_override']
        if gate and gate_asked:
            return gate  # the gate decision is the decision-changing one
        ranked = [e for e in ranked if e.get('id') != 'gate_override']
        return ranked[:2] if whole else ranked

    def text_for(self, entry: dict) -> str:
        if entry.get('answer'):
            return self._fill(entry['answer'])
        generic = self.data.get('generic', {})
        return generic.get('text') or 'Please proceed under a stated assumption.'

    def completed(self, text: str) -> bool:
        """The completion marker counts only at the very end of the final message."""
        return text.rstrip(' \t\r\n.!*_`\'"').lower().endswith(self.marker)

    def reply(self, final_text: str, rounds_left: int | None = None) -> tuple[str, str, list[str]] | None:
        """Return (kind, reply, matched_ids), or None when the run should stop.

        After INTAKE_CAP_AFTER answered intake rounds, or when at most that many rounds remain, the answer
        is followed by INTAKE_CAP_TEXT and logged with kind 'intake_cap'."""
        text = final_text or ''
        if self.completed(text):
            return None
        asks = (bool(question_sentences(text[-800:])) or bool(INTAKE_PATTERN.search(text[-400:]))
                or offers_options(text[-1500:]) or GATE_CUE.search(text[-1500:]) is not None)
        if asks:
            matched = self.match(text)
            kind = 'answer' if matched else 'generic'
            reply = '\n\n'.join(dict.fromkeys(self.text_for(e) for e in matched)) if matched else self.text_for({})
            capped = self.intake_answers >= INTAKE_CAP_AFTER or (rounds_left is not None and rounds_left <= INTAKE_CAP_AFTER)
            self.intake_answers += 1
            if capped:
                return 'intake_cap', reply + '\n\n' + INTAKE_CAP_TEXT, [e['id'] for e in matched]
            return kind, reply, [e['id'] for e in matched]
        if self.nudges_left <= 0:
            return None
        self.nudges_left -= 1
        return 'nudge', self._fill(self.data.get('nudge', {}).get('text', 'Please continue.')), []


# --------------------------------------------------------------------------- transcript parsing

def _text_of(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return '\n'.join(_text_of(c.get('text', c.get('content', ''))) if isinstance(c, dict) else str(c) for c in content)
    return '' if content is None else str(content)


def load_rounds(out_dir: Path) -> list[dict]:
    path = out_dir / 'rounds.jsonl'
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text(encoding='utf-8').splitlines() if l.strip()]


def parse_transcript(out_dir: Path) -> dict:
    """Normalize stream-json lines into ordered events with round numbers."""
    rounds = load_rounds(out_dir)

    def round_of(line_no: int) -> int:
        for r in rounds:
            if r.get('line_start', 0) <= line_no < r.get('line_end', 0):
                return int(r['round'])
        return rounds[-1]['round'] if rounds else 0

    events: list[dict] = []
    results: dict[str, dict] = {}
    path = out_dir / 'transcript.jsonl'
    lines = path.read_text(encoding='utf-8', errors='replace').splitlines() if path.exists() else []
    for no, raw in enumerate(lines):
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if not isinstance(obj, dict):
            continue
        kind, rnd = obj.get('type'), round_of(no)
        top = obj.get('parent_tool_use_id') in (None, '')
        if kind == 'assistant':
            for block in (obj.get('message') or {}).get('content') or []:
                if not isinstance(block, dict):
                    continue
                if block.get('type') == 'text' and block.get('text'):
                    events.append({'kind': 'text', 'line': no, 'round': rnd, 'top': top, 'text': block['text']})
                elif block.get('type') == 'tool_use':
                    events.append({'kind': 'tool_use', 'line': no, 'round': rnd, 'top': top, 'id': block.get('id'),
                                   'name': block.get('name', ''), 'input': block.get('input') or {}})
        elif kind == 'user':
            for block in (obj.get('message') or {}).get('content') or []:
                if isinstance(block, dict) and block.get('type') == 'tool_result':
                    results[str(block.get('tool_use_id'))] = {'line': no, 'is_error': bool(block.get('is_error')),
                                                              'text': _text_of(block.get('content'))}
        elif kind == 'result':
            events.append({'kind': 'result', 'line': no, 'round': rnd, 'top': True, 'obj': obj})
        elif kind == 'system' and 'hook' in str(obj.get('subtype', '')):
            events.append({'kind': 'hook', 'line': no, 'round': rnd, 'top': True, 'obj': obj})
    for i, ev in enumerate(events):
        ev['idx'] = i
        if ev['kind'] == 'tool_use':
            res = results.get(str(ev.get('id')))
            ev['result'] = res
            ev['input_text'] = json.dumps(ev['input'], ensure_ascii=False) if not isinstance(ev['input'], str) else ev['input']
            ev['denied'] = bool(res and res['is_error'] and DENIAL_RE.search(res['text']))
    return {'events': events, 'rounds': rounds}


DENIAL_RE = re.compile(r'(?i)(hook|route envelope|skill route rejected|permissiondecision|denied|blocked|not allowed|permission)')
HOOK_DENIAL_RE = re.compile(r'(?i)(PreToolUse|\bhook\b|route envelope|skill route rejected|permissionDecision)')
HOOK_EVENT_DENY_RE = re.compile(r'permissionDecision\W+deny|"decision\W+block')


def hook_denials(parsed: dict) -> dict:
    events, by_tool = [], {}
    for ev in parsed['events']:
        if ev['kind'] == 'tool_use' and ev.get('result') and ev['result']['is_error'] and HOOK_DENIAL_RE.search(ev['result']['text']):
            events.append({'line': ev['line'], 'tool': ev['name'], 'input': ev['input_text'][:200], 'reason': ev['result']['text'][:300]})
        elif ev['kind'] == 'hook':
            dumped = json.dumps(ev['obj'])
            if HOOK_EVENT_DENY_RE.search(dumped):
                events.append({'line': ev['line'], 'tool': str(ev['obj'].get('hook_name') or ev['obj'].get('subtype')),
                               'input': '', 'reason': dumped[:300]})
    # A hook denial is reported both as a hook event and as an error tool result: drop the hook event when a
    # denied tool result for the same tool sits within 10 lines.
    results = [e for e in events if not e['tool'].startswith('PreToolUse:')]
    events = [e for e in events if not (e['tool'].startswith('PreToolUse:') and any(
        r['tool'] == e['tool'].split(':', 1)[1] and abs(r['line'] - e['line']) <= 10 for r in results))]
    seen, unique = set(), []
    for e in events:
        key = (e['line'], e['tool'])
        if key not in seen:
            seen.add(key)
            unique.append(e)
            by_tool[e['tool']] = by_tool.get(e['tool'], 0) + 1
    return {'count': len(unique), 'by_tool': by_tool, 'events': unique}


HOOK_INPUT_MAX = 80


def scorecard_hook_denials(parsed: dict) -> dict:
    """hook_denials() for the committed scorecard: tool inputs truncated so private founder answers quoted in
    Skill args cannot leak."""
    data = hook_denials(parsed)
    data['events'] = [{**e, 'input': e['input'][:HOOK_INPUT_MAX]} for e in data['events']]
    return data


# --------------------------------------------------------------------------- checks

CHECK_TYPES = {'all', 'any', 'not', 'text', 'tool_use', 'artifact', 'json_len', 'jsonl_distinct', 'order',
               'max_questions_per_turn', 'answers_persisted', 'hook_denials', 'gate_sequence', 'provider_gaps',
               'skill_reached'}


def validate_check(check: dict) -> None:
    if not isinstance(check, dict) or check.get('type') not in CHECK_TYPES:
        raise ValueError(f'unknown check: {check!r}')
    for child in check.get('checks', []):
        validate_check(child)
    for key in ('check', 'first', 'then', 'near_miss_check'):
        if key in check:
            validate_check(check[key])


class Ctx:
    def __init__(self, out_dir: Path, scenario_dir: Path | None = None):
        self.out_dir = out_dir
        self.art = out_dir / 'artifacts'
        self.parsed = parse_transcript(out_dir)
        self.events = self.parsed['events']
        self.rounds = self.parsed['rounds']
        self.scenario_dir = scenario_dir
        self._files: list[Path] | None = None
        self._cache: dict[Path, str] = {}
        self.flags: dict[str, Any] = {}  # per-checkpoint report-only flags, reset by score()

    def files(self) -> list[Path]:
        if self._files is None:
            self._files = sorted(p for p in self.art.rglob('*') if p.is_file()) if self.art.exists() else []
        return self._files

    def glob(self, pattern: str) -> list[Path]:
        rx = glob_regex(pattern)
        return [p for p in self.files() if rx.fullmatch(p.relative_to(self.art).as_posix())]

    def read(self, path: Path) -> str:
        if path not in self._cache:
            try:
                with path.open('rb') as fh:
                    self._cache[path] = fh.read(MAX_READ_BYTES).decode('utf-8', errors='replace')
            except OSError:
                self._cache[path] = ''
        return self._cache[path]

    def rel(self, path: Path) -> str:
        return path.relative_to(self.out_dir).as_posix()

    def documents(self, scope: str) -> list[tuple[str, str]]:
        """The agent's own deliverables: top-level assistant text per round and authored eval-project files.

        Subagent text and collected provider data (evidence runs, raw payloads, provider checkpoints, run
        summaries and any *.jsonl) are excluded, so a text check cannot pass on third-party content the
        agent merely collected (Task 7.3 audit, cp07)."""
        docs: list[tuple[str, str]] = []
        if scope in ('assistant', 'both'):
            by_round: dict[int, list[str]] = {}
            first_line: dict[int, int] = {}
            for ev in self.events:
                if ev['kind'] == 'text' and ev['top']:
                    by_round.setdefault(ev['round'], []).append(ev['text'])
                    first_line.setdefault(ev['round'], ev['line'])
            docs += [(f'transcript.jsonl#L{first_line[r] + 1}', '\n'.join(t)) for r, t in sorted(by_round.items())]
        if scope in ('artifacts', 'both'):
            docs += [(self.rel(p), self.read(p)) for p in self.files()
                     if p.suffix.lower() in TEXT_SUFFIXES and not is_collected_data(p.relative_to(self.art).as_posix())]
        return docs


COLLECTED_DATA_GLOBS = ('**/runs/**', '**/raw/**', '**/provider-checkpoints/**', '**/run-checkpoint.json',
                        '**/summary.json', '**/*.jsonl')


def is_collected_data(rel: str) -> bool:
    """Collected provider output (forum, review or SERP text) rather than something the agent authored."""
    return any(glob_regex(g).fullmatch(rel) for g in COLLECTED_DATA_GLOBS)


def glob_regex(pattern: str) -> re.Pattern:
    """Path glob: `**/` spans zero or more directories, `*` and `?` stay within one path segment."""
    out, i = '', 0
    while i < len(pattern):
        if pattern.startswith('**/', i):
            out, i = out + '(?:.*/)?', i + 3
        elif pattern.startswith('**', i):
            out, i = out + '.*', i + 2
        elif pattern[i] == '*':
            out, i = out + '[^/]*', i + 1
        elif pattern[i] == '?':
            out, i = out + '[^/]', i + 1
        else:
            out, i = out + re.escape(pattern[i]), i + 1
    return re.compile(out)


Result = tuple[bool | None, str | None, str]  # passed (None = not exercised), evidence_path, detail
ANSWER_KINDS = ('answer', 'generic', 'intake_cap')


COMMAND_SPLIT_RE = re.compile(r'&&|\|\||[;|\n]')


def command_parts(ev: dict) -> list[str]:
    """A Bash command split into its simple commands, so `a --help && a create x` is judged part by part."""
    inp = ev.get('input')
    command = inp.get('command') if isinstance(inp, dict) else (inp if isinstance(inp, str) else None)
    if not isinstance(command, str):
        return [ev['input_text']]
    return [p.strip() for p in COMMAND_SPLIT_RE.split(command) if p.strip()]


def _tool_matches(ctx: Ctx, check: dict) -> list[dict]:
    name_re, input_re = re.compile(check.get('name', '.*')), re.compile(check.get('input', '.*'))
    result_re = re.compile(check['result']) if check.get('result') else None
    hits = []
    for ev in ctx.events:
        if ev['kind'] != 'tool_use' or not name_re.search(ev['name']) or not input_re.search(ev['input_text']):
            continue
        if check.get('exclude_input') and not any(
                input_re.search(part) and not any(re.search(x, part) for x in check['exclude_input'])
                for part in command_parts(ev)):
            continue  # every matching part is a read-only invocation, e.g. `scripts/x.py --help`
        res = ev.get('result')
        if check.get('exclude_denied') and (ev['denied'] or (res and res['is_error'])):
            continue  # denied or failed calls do not count as reaching the tool
        if check.get('result_ok') and (not res or res['is_error']):
            continue
        if result_re and not (res and result_re.search(res['text'])):
            continue
        hits.append(ev)
    return hits


def event_indices(ctx: Ctx, check: dict) -> list[int]:
    """Transcript positions where an event-level matcher (text/tool_use/any) fires."""
    kind = check['type']
    if kind == 'any':
        return sorted({i for c in check['checks'] for i in event_indices(ctx, c)})
    if kind == 'tool_use':
        return [ev['idx'] for ev in _tool_matches(ctx, check)]
    if kind == 'text':
        pats = [re.compile(p) for p in check['patterns']]
        return [ev['idx'] for ev in ctx.events if ev['kind'] == 'text' and all(p.search(ev['text']) for p in pats)]
    raise ValueError(f'{kind} cannot be used as an ordered event matcher')


def _line_ref(ctx: Ctx, idx: int) -> str:
    return f"transcript.jsonl#L{ctx.events[idx]['line'] + 1}"


def run_check(ctx: Ctx, check: dict) -> Result:
    ok, evidence, detail = _run_check(ctx, check)
    if ok is False and check.get('near_miss_check'):  # report a partial attempt; it never passes the check
        n_ok, n_ev, n_detail = _run_check(ctx, check['near_miss_check'])
        if n_ok is True:
            detail += f"; near miss: {check.get('near_miss_label', 'partial attempt')} ({n_ev or n_detail})"
    return ok, evidence, detail


def _run_check(ctx: Ctx, check: dict) -> Result:
    """None = not exercised (nothing to check), True = pass, False = fail."""
    kind = check['type']
    label = check.get('label') or kind
    if kind in ('all', 'any'):
        results = [(c, run_check(ctx, c)) for c in check['checks']]
        oks = [r for _, r in results if r[0] is True]
        if kind == 'all':
            failed = [(c.get('label') or c['type'], r[2]) for c, r in results if r[0] is False]
            unexercised = [(c.get('label') or c['type'], r[2]) for c, r in results if r[0] is None]
            evidence = next((r[1] for _, r in results if r[1]), None)
            if failed:
                return False, evidence, 'missing: ' + '; '.join(f'{l} ({d})' for l, d in failed)
            if unexercised:
                return None, evidence, 'not exercised: ' + '; '.join(f'{l} ({d})' for l, d in unexercised)
            return True, evidence, 'all sub-checks passed'
        if oks:
            return True, oks[0][1], oks[0][2]
        return False, None, f'{label}: none matched (' + '; '.join(r[2] for _, r in results) + ')'
    if kind == 'not':
        ok, ev, detail = run_check(ctx, check['check'])
        ok = ok is True
        return (not ok), ev, (f'{label}: forbidden event found ({detail})' if ok else f'{label}: none found')
    if kind == 'text':
        pats = [re.compile(p) for p in check['patterns']]
        excludes = [re.compile(p) for p in check.get('exclude', [])]
        per_line = bool(check.get('per_line'))
        unit = 'line' if per_line else 'document'
        for ref, text in ctx.documents(check.get('scope', 'both')):
            # per_line: all patterns on one line (a sentence or table row), and no exclude pattern on that line,
            # so a gap statement ("UK analogs not checked") is not read as a precedent.
            for chunk in (text.splitlines() if per_line else [text]):
                if all(p.search(chunk) for p in pats) and not any(x.search(chunk) for x in excludes):
                    return True, ref, f'{label}: all patterns in one {unit}'
        detail = f'{label}: no single {unit} matched all {len(pats)} patterns'
        near_excl = [re.compile(p) for p in check.get('exclude', [])]
        near = [re.compile(p) for p in (check.get('near_miss_patterns') or (check['patterns'][:2] if check.get('near_miss_label') else []))]
        if near:
            for ref, text in ctx.documents(check.get('scope', 'both')):
                for chunk in text.splitlines():
                    if all(p.search(chunk) for p in near) and not any(x.search(chunk) for x in near_excl):
                        return False, None, (f"{detail}; near miss: {check.get('near_miss_label', 'partial match')} "
                                             f"at {ref}: {chunk.strip()[:80]!r}")
        return False, None, detail
    if kind == 'tool_use':
        hits = _tool_matches(ctx, check)
        need = int(check.get('min', 1))
        ok = len(hits) >= need
        return ok, (_line_ref(ctx, hits[0]['idx']) if hits else None), f'{label}: {len(hits)} matching call(s), need {need}'
    if kind == 'artifact':
        files = ctx.glob(check['glob'])
        pats = [re.compile(p) for p in check.get('contains', [])]
        hits = [p for p in files if all(r.search(ctx.read(p)) for r in pats)]
        need = int(check.get('min', 1))
        return len(hits) >= need, (ctx.rel(hits[0]) if hits else None), \
            f"{label}: {len(hits)} of {len(files)} file(s) matching {check['glob']} contain all patterns"
    if kind == 'json_len':
        best, best_path = 0, None
        for p in ctx.glob(check['glob']):
            try:
                node: Any = json.loads(ctx.read(p))
                for key in check['path'].split('.'):
                    node = node.get(key) if isinstance(node, dict) else None
                size = len(node) if isinstance(node, (list, dict)) else 0
            except (json.JSONDecodeError, AttributeError):
                size = 0
            if size > best:
                best, best_path = size, p
        need = int(check.get('min', 1))
        return best >= need, (ctx.rel(best_path) if best_path else None), f"{label}: max {best} entries at {check['path']}, need {need}"
    if kind == 'jsonl_distinct':
        values, where_path = set(), None
        for p in ctx.glob(check['glob']):
            for line in ctx.read(p).splitlines():
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(rec, dict) and all(rec.get(k) == v for k, v in check.get('where', {}).items()) and rec.get(check['field']):
                    values.add(str(rec[check['field']]))
                    where_path = where_path or p
        need = int(check.get('min', 1))
        return len(values) >= need, (ctx.rel(where_path) if where_path else None), \
            f"{label}: {len(values)} distinct {check['field']}, need {need}"
    if kind == 'order':
        firsts, thens = event_indices(ctx, check['first']), event_indices(ctx, check['then'])
        if not firsts:
            return False, None, 'order: the required first event never happened'
        if thens and thens[0] < firsts[0]:
            return False, _line_ref(ctx, thens[0]), 'order: a write happened before the first event'
        return True, _line_ref(ctx, firsts[0]), 'order: first event precedes any later event'
    if kind == 'max_questions_per_turn':
        answered = {r['round'] for r in ctx.rounds if r.get('kind') in ANSWER_KINDS}
        worst, worst_ref, checked = 0, None, 0
        for r in ctx.rounds:
            if r['round'] + 1 not in answered:
                continue
            final = round_final_text(ctx, r['round'])
            checked += 1
            n = count_question_blocks(final)
            if n > worst:
                worst, worst_ref = n, f"rounds.jsonl#round{r['round']}"
        limit = int(check.get('max', 1))
        if not checked:
            return None, None, 'proxy: no answered intake turns to measure (not exercised)'
        return worst <= limit, worst_ref, f'proxy: max {worst} question block(s) over {checked} answered turn(s), limit {limit}'
    if kind == 'answers_persisted':
        feeder_data = _founder_answers(ctx)
        fed = [i for r in ctx.rounds if r.get('kind') in ANSWER_KINDS for i in r.get('matched_ids', [])]
        with_markers = [e for e in feeder_data.get('answers', []) if e.get('id') in set(fed) and e.get('persist_markers')]
        if not with_markers:
            return None, None, 'answers_persisted: no fed answer carried persist markers (not exercised)'
        corpus = [(p, ctx.read(p).lower()) for p in ctx.files() if p.suffix.lower() in TEXT_SUFFIXES]
        found, first = 0, None
        for entry in with_markers:
            hit = next((p for p, t in corpus if any(m.lower() in t for m in entry['persist_markers'])), None)
            if hit:
                found += 1
                first = first or hit
        frac = found / len(with_markers)
        need = float(check.get('min_fraction', 0.5))
        return frac >= need, (ctx.rel(first) if first else None), f'answers_persisted: {found}/{len(with_markers)} fed answers found in artifacts'
    if kind == 'hook_denials':
        tool_re, input_re = re.compile(check.get('tool', '.*')), re.compile(check.get('input', '.*'))
        hits = [e for e in hook_denials(ctx.parsed)['events'] if tool_re.search(e['tool']) and input_re.search(e['input'])]
        limit = int(check.get('max', 0))
        return len(hits) <= limit, (f"transcript.jsonl#L{hits[0]['line'] + 1}" if hits else None), \
            f'hook_denials: {len(hits)} matching denial(s), max {limit}'
    if kind == 'gate_sequence':
        return gate_sequence(ctx, check)
    if kind == 'skill_reached':
        return skill_reached(ctx, check)
    if kind == 'provider_gaps':
        return provider_gaps(ctx, check)
    raise ValueError(f'unknown check type {kind}')


def _founder_answers(ctx: Ctx) -> dict:
    for base in (ctx.scenario_dir, ctx.out_dir / 'scenario', DEFAULT_SCENARIO):
        if base and (base / 'founder-answers.json').exists():
            return load_answers(base / 'founder-answers.json')
    return {}


def round_final_text(ctx: Ctx, rnd: int) -> str:
    for ev in reversed(ctx.events):
        if ev['round'] == rnd and ev['kind'] == 'result' and isinstance(ev['obj'].get('result'), str):
            return ev['obj']['result']
    texts = [ev['text'] for ev in ctx.events if ev['round'] == rnd and ev['kind'] == 'text' and ev['top']]
    return texts[-1] if texts else ''


OVERRIDE_RECORDED_RE = re.compile(r'"?gate_override"?\s*:\s*true\b')
ROUTER_REJECTED_RE = re.compile(r'(?im)^(usage: |[\w.]+\.py: error:|error:|traceback )')
DEFAULT_DOWNSTREAM_WRITES = r'(?i)(gtm|go-to-market|digital-assets/|/website/|campaign)'


def router_result_ok(res: dict | None) -> bool:
    """A router result that is not an argparse/usage failure. `| head` hides the exit code, so the text decides."""
    return bool(res) and not res['is_error'] and not ROUTER_REJECTED_RE.search(res['text'])


def _skill_file_re(skills: str) -> re.Pattern:
    return re.compile(r'(?:\.agents|\.claude)/skills/' + skills + r'/SKILL\.md')


def _skill_loads(ctx: Ctx, skills: str) -> tuple[list[int], list[int], list[int]]:
    """(Skill tool calls, SKILL.md reads, denied Skill calls) for skills matching the `skills` regex."""
    down_re, file_re = re.compile(skills), _skill_file_re(skills)
    invoked, read, denied = [], [], []
    for ev in ctx.events:
        if ev['kind'] != 'tool_use':
            continue
        res = ev.get('result') or {'text': '', 'is_error': False}
        if ev['name'] == 'Skill' and down_re.search(ev['input_text']):
            (denied if ev['denied'] or res['is_error'] else invoked).append(ev['idx'])
        elif ev['name'] in ('Read', 'Bash') and file_re.search(ev['input_text']) and not res['is_error']:
            read.append(ev['idx'])
    return invoked, read, denied


def gate_sequence(ctx: Ctx, check: dict) -> Result:
    """Pain-first block, then a recorded override, then downstream work.

    Downstream work = a downstream skill loaded (Skill tool call, or a Read/cat of its SKILL.md) and a
    GTM/website/campaign artifact written after the override. An override counts only when the router's
    result records it (gate_override: true); a usage/argparse failure piped through `head` does not."""
    route_re = re.compile(check['route'])
    blocked_res = [re.compile(b) for b in (check['blocked'] if isinstance(check['blocked'], list) else [check['blocked']])]
    denial_re = re.compile(check.get('denial', r'(?i)pain.first|problem_validation'))
    override_re = re.compile(check['override'])
    writes_re = re.compile(check.get('writes', DEFAULT_DOWNSTREAM_WRITES))
    blocks, overrides, writes = [], [], []
    for ev in ctx.events:
        if ev['kind'] != 'tool_use':
            continue
        res = ev.get('result') or {'text': '', 'is_error': False}
        if ev['name'] == 'Bash' and route_re.search(ev['input_text']):
            if override_re.search(ev['input_text']):
                if router_result_ok(res) and OVERRIDE_RECORDED_RE.search(res['text']):
                    overrides.append(ev['idx'])
            elif all(b.search(res['text']) for b in blocked_res):  # matched independently: key order varies
                blocks.append(ev['idx'])
        elif ev['name'] in ('Write', 'Edit', 'MultiEdit', 'NotebookEdit') and not res['is_error']:
            path = str(ev['input'].get('file_path') or ev['input'].get('notebook_path') or '')
            if writes_re.search(path):
                writes.append(ev['idx'])
    invoked, read, denied = _skill_loads(ctx, check['downstream'])
    blocks += [i for i in denied if denial_re.search((ctx.events[i].get('result') or {}).get('text', ''))]
    blocks.sort()
    if not blocks:
        return False, None, 'gate: no blocked gated route observed'
    if not overrides:
        return False, _line_ref(ctx, blocks[0]), 'gate: blocked, but no --override-gate call recorded'
    first_override = min((o for o in overrides if o > blocks[0]), default=None)
    if first_override is None:
        return False, _line_ref(ctx, overrides[0]), 'gate: override recorded before any block'
    early = sorted(i for i in invoked + writes if i < first_override)
    if early:
        return False, _line_ref(ctx, early[0]), 'gate: a downstream skill or GTM artifact ran before the override'
    loads = [i for i in invoked + read if i > first_override]
    late_writes = [w for w in writes if loads and w > min(loads)]
    if not loads:
        return False, _line_ref(ctx, first_override), 'gate: override recorded but no downstream skill was loaded'
    if not late_writes:
        return False, _line_ref(ctx, first_override), \
            'gate: override and downstream skill load recorded, but no GTM/website/campaign artifact was written'
    how = 'Skill tool' if any(i > first_override for i in invoked) else 'SKILL.md read (Skill tool bypassed)'
    return True, _line_ref(ctx, first_override), \
        f'gate: blocked, overridden, downstream skill via {how}, then {len(late_writes)} artifact write(s)'


def skill_reached(ctx: Ctx, check: dict) -> Result:
    """A successful route check for the skill plus the skill loaded by the Skill tool or a read of its SKILL.md.

    Sets flags.skill_tool_bypassed when the skill was only read, so a Skill-tool bypass (which also skips the
    PreToolUse hook and its injected route context) is visible instead of silently scored."""
    skill = check['skill']
    route_re = re.compile(check.get('route', r'route_workflow\.py'))
    packet_re = re.compile(r'"?(skill|first_skill)"?\s*:\s*"' + re.escape(skill) + '"')
    routes = [ev for ev in ctx.events if ev['kind'] == 'tool_use' and ev['name'] == 'Bash'
              and route_re.search(ev['input_text']) and router_result_ok(ev.get('result'))
              and packet_re.search(ev['result']['text'])]
    invoked, read, _ = _skill_loads(ctx, re.escape(skill))
    ctx.flags['skill_tool_bypassed'] = bool(read) and not invoked
    if not routes:
        return False, None, f'skill_reached: no successful route check returning {skill}'
    if not (invoked or read):
        return False, _line_ref(ctx, routes[0]['idx']), f'skill_reached: route check ran but {skill} was never loaded'
    how = 'Skill tool' if invoked else 'SKILL.md read (Skill tool bypassed)'
    return True, _line_ref(ctx, (invoked or read)[0]), f'skill_reached: route check plus {skill} via {how}'


QUOTA_RE = re.compile(r'(?i)(\b402\b[^\n]{0,40}payment required|\b429\b[^\n]{0,40}too many|usage limit exceeded'
                      r'|quota (exceeded|exhausted)|insufficient (credits?|balance)|\"status\"\s*:\s*402)')


HELPER_SCRIPT_RE = re.compile(r'scripts/(?:capability_lookup|route_workflow|evaluate|run_acceptance|project_workspace|case_workspace'
                              r'|subprojects|enforce_skill_route)\.py|scripts/(?:[\w/]*/)?validate_[\w]*\.py')


def quota_events(ctx: Ctx) -> list[dict]:
    """Tool calls whose result says a provider is out of quota or credit (a coverage gap, not absence of demand)."""
    out = []
    for ev in ctx.events:
        res = ev.get('result') if ev['kind'] == 'tool_use' else None
        if not res or not QUOTA_RE.search(res['text'][:4000]):
            continue
        if ev['name'].startswith('mcp__'):
            provider = ev['name'].split('__')[1]
        else:
            scripts = re.findall(r'scripts/[\w/.-]+\.py', ev['input_text'])
            providers = [x for x in scripts if not HELPER_SCRIPT_RE.search(x)]
            if scripts and not providers:
                continue  # only repository helpers (catalog lookup, router, validator) ran; their text may mention credits
            provider = providers[0] if providers else ev['name']
        out.append({'line': ev['line'] + 1, 'provider': provider})
    return out


def provider_status(ctx: Ctx) -> dict:
    ok, failed = set(), set()
    quota = {q['provider'] for q in quota_events(ctx)}
    for p in ctx.glob('**/summary.json'):
        try:
            data = json.loads(ctx.read(p))
        except json.JSONDecodeError:
            continue
        providers = data.get('providers') if isinstance(data, dict) else None
        if not isinstance(providers, dict):
            continue
        for name, info in providers.items():
            attempts = info.get('attempts') if isinstance(info, dict) else None
            status = (attempts[-1].get('status') if attempts and isinstance(attempts[-1], dict) else
                      (info.get('status') if isinstance(info, dict) else None))
            (ok if status in ('ok', 'success', 'searched_empty', 'empty') else failed).add(name)
    failed |= quota
    return {'attempted': sorted(ok | failed), 'ok': sorted(ok - failed), 'failed': sorted(failed),
            'source': 'summary.json provider attempts in eval-project artifacts, plus quota/402 tool results in the transcript'}


def provider_gaps(ctx: Ctx, check: dict) -> Result:
    status = provider_status(ctx)
    docs = ctx.documents('assistant')
    absence = [re.compile(p) for p in check['absence_patterns']]
    for ref, text in docs:
        if any(p.search(text) for p in absence):
            return False, ref, 'proxy: an assistant round states absence of demand'
    if not docs or not (ctx.glob('**/summary.json') or quota_events(ctx)):
        return None, None, 'not exercised: needs an assistant round and a run summary.json or a provider quota error'
    if not status['failed']:
        return None, None, 'not exercised: no provider failure in run summaries, so gap reporting was not tested'
    gaps = [re.compile(p) for p in check['gap_patterns']]
    for ref, text in docs:
        if any(p.search(text) for p in gaps):
            for ev in ctx.events:  # point at the message that states the gap, not the round opener
                if ev['kind'] == 'text' and ev['top'] and any(p.search(ev['text']) for p in gaps):
                    ref = f"transcript.jsonl#L{ev['line'] + 1}"
                    break
            return True, ref, f"proxy: failed providers {status['failed']} and a coverage gap is stated"
    return False, None, f"proxy: providers {status['failed']} failed but no assistant round names a coverage gap"


# --------------------------------------------------------------------------- scoring

def _num(value: Any) -> float | None:
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def spend_summary(out_dir: Path, budget_usd: float | None) -> tuple[dict, bool | None]:
    path = out_dir / 'provider-spend.json'
    delta = (json.loads(path.read_text(encoding='utf-8')).get('delta') or {}) if path.exists() else {}
    apify, dfs = _num(delta.get('apify_usd')), _num(delta.get('dataforseo_usd'))
    serp_n, serp_usd = _num(delta.get('serpapi_searches')), _num(delta.get('serpapi_usd'))
    measured = sum(v for v in (apify, dfs, serp_usd) if v is not None)
    complete = None not in (apify, dfs, serp_usd)
    notes = ('Measured as account usage deltas around the run; other concurrent use of the same accounts is included, '
             'Apify usage can lag, and SerpApi reports searches, not USD (priced only with --serpapi-usd-per-search). '
             'The runner does not enforce provider caps inside the tree under test.')
    # Known only when every component is measured, or when the measured part alone already exceeds the cap.
    if budget_usd is None:
        over = None
    elif complete or measured > budget_usd:
        over = measured > budget_usd
    else:
        over = None
    return ({'apify_usd': apify, 'dataforseo_usd': dfs, 'serpapi_searches': serp_n, 'serpapi_usd': serp_usd,
             'measured_usd': round(measured, 4), 'complete': complete, 'notes': notes}, over)


def score(out_dir: Path, checkpoints: Path, scenario_dir: Path | None = None) -> dict:
    """Deterministic checkpoint results plus measured cost, time, tokens and denials for one run."""
    out_dir, spec = Path(out_dir), json.loads(Path(checkpoints).read_text(encoding='utf-8'))
    ctx = Ctx(out_dir, scenario_dir or Path(checkpoints).parent)
    manifest_path = out_dir / 'run-manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8')) if manifest_path.exists() else {}
    cps = []
    for cp in spec['checkpoints']:
        validate_check(cp['check'])
        ctx.flags = {}
        ok, evidence, detail = run_check(ctx, cp['check'])
        status = 'pass' if ok is True else ('not_exercised' if ok is None else 'fail')
        entry = {'id': cp['id'], 'stage': cp['stage'], 'title': cp['title'], 'passed': ok is True, 'status': status,
                 'proxy': bool(cp.get('proxy')), 'evidence_path': evidence, 'detail': detail}
        if cp['check']['type'] in ('all', 'any'):  # report each sub-check, so a partial pass shows what is missing
            entry['sub_checks'] = []
            for child in cp['check']['checks']:
                c_ok, c_ev, c_detail = run_check(ctx, child)
                entry['sub_checks'].append({'label': child.get('label') or child['type'], 'passed': c_ok is True,
                                            'evidence_path': c_ev, 'detail': c_detail})
        if ctx.flags:
            entry['flags'] = dict(ctx.flags)
        cps.append(entry)
    tokens, perm = {'input': 0, 'output': 0, 'cache_creation': 0, 'cache_read': 0}, 0
    session, per_session = None, {}
    for ev in ctx.events:
        if ev['kind'] != 'result':
            continue
        obj = ev['obj']
        sid = str(obj.get('session_id') or '')
        # total_cost_usd is session-cumulative and repeated: keep the maximum per session, never sum.
        per_session[sid] = max(per_session.get(sid, 0.0), _num(obj.get('total_cost_usd')) or 0.0)
        usage = obj.get('usage') or {}
        tokens['input'] += int(usage.get('input_tokens') or 0)
        tokens['output'] += int(usage.get('output_tokens') or 0)
        tokens['cache_creation'] += int(usage.get('cache_creation_input_tokens') or 0)
        tokens['cache_read'] += int(usage.get('cache_read_input_tokens') or 0)
        perm += len(obj.get('permission_denials') or [])
        session = obj.get('session_id') or session
    model_usd = sum(per_session.values())
    budget = _num(manifest.get('budget_usd'))
    provider_spend, over = spend_summary(out_dir, budget)
    passed = sum(c['passed'] for c in cps)
    notes = [
        'Model cost is the maximum cumulative total_cost_usd per session; token totals sum per-call usage of every '
        'result event (verify against modelUsage if exact token counts matter).',
        'Checkpoints marked proxy test presence or a countable stand-in, not the quality judgement in their title.',
        'Provider spend is measured, not enforced; see cost.provider_spend.notes.',
        'Artifacts are copied only from the eval project directories; work written elsewhere is listed in writes_outside_eval, not scored.',
    ]
    host = classify_host_writes(ctx, [w for w in manifest.get('writes_outside_eval', []) if str(w).startswith('host:')])
    if host['attributed']:
        notes.insert(0, f"WARNING: {len(host['attributed'])} host file change(s) under a projects/ tree match paths the "
                        'agent used in tool calls; inspect host_writes.attributed.')
    if host['unattributed_possibly_concurrent']:
        notes.append(f"{len(host['unattributed_possibly_concurrent'])} host projects/ change(s) never referenced in the "
                     'transcript; likely a concurrent session (listed under host_writes.unattributed_possibly_concurrent).')
    quota = quota_events(ctx)
    if quota:
        by = {}
        for q in quota:
            by[q['provider']] = by.get(q['provider'], 0) + 1
        notes.append('Provider quota/credit errors (402/429/usage limit): ' +
                     ', '.join(f'{k} ({v} call(s))' for k, v in sorted(by.items())) +
                     '. Counted as provider failures for cp11: a coverage gap, never absence of demand.')
    killed = [r['round'] for r in ctx.rounds if r.get('timed_out')]
    if killed:
        notes.append(f'Round(s) {killed} were killed on timeout and emitted no result event: their model cost is unreported.')
    if manifest.get('reference_seeded') is False:
        notes.append('The reference workspace could not be seeded; cp01 cannot pass on this run.')
    return {
        'schema_version': 1,
        'scenario': spec.get('scenario', manifest.get('scenario', '')),
        'run': {'ref': str(manifest.get('ref', '')), 'ref_sha': str(manifest.get('ref_sha', '')),
                'eval_slug': str(manifest.get('eval_slug', '')), 'started_at': manifest.get('started_at'),
                'finished_at': manifest.get('finished_at'), 'rounds': len(ctx.rounds),
                'stop_reason': manifest.get('stop_reason'), 'session_id': session,
                'blocked_tools': list(manifest.get('blocked_tools', []))},
        'checkpoints': cps,
        'summary': {'total': len(cps), 'passed': passed,
                    'failed': sum(c['status'] == 'fail' for c in cps),
                    'not_exercised': [c['id'] for c in cps if c['status'] == 'not_exercised'],
                    'proxy': sum(c['proxy'] for c in cps)},
        'providers': provider_status(ctx),
        'cost': {'model_usd': round(model_usd, 4), 'model_budget_usd': _num(manifest.get('model_budget_usd')),
                 'budget_usd': budget, 'provider_spend': provider_spend, 'over_budget': over, 'spend_enforced': False},
        'wall_time_s': _num(manifest.get('wall_time_s')),
        'tokens': tokens,
        'hook_denials': scorecard_hook_denials(ctx.parsed),
        'permission_denials': perm,
        'writes_outside_eval': list(manifest.get('writes_outside_eval', [])),
        'host_writes': host,
        'friction': str(manifest.get('friction', '')),
        'honesty_notes': notes,
    }


def classify_host_writes(ctx: Ctx, entries: list[str]) -> dict:
    """Attributed if the changed path, or a parent down to projects/<name>, appears in any tool input."""
    corpus = '\n'.join(ev['input_text'] for ev in ctx.events if ev['kind'] == 'tool_use')
    out = {'attributed': [], 'unattributed_possibly_concurrent': []}
    for entry in entries:
        path = Path(str(entry)[len('host:'):])
        parts = path.parts
        stop = parts.index('projects') + 2 if 'projects' in parts else len(parts)
        candidates = [path, *[q for q in path.parents if len(q.parts) >= stop]]
        hit = any(str(c) in corpus for c in candidates)
        out['attributed' if hit else 'unattributed_possibly_concurrent'].append(str(entry))
    return out


HOME_PATH_RE = re.compile(r'(?<![\w.-])/{1,2}home/[^/\s"\')*:]+')


def relativize_paths(node: Any) -> Any:
    """Scorecards are committed: replace a host home directory (and so the repo/worktree prefix) with `~`."""
    if isinstance(node, str):
        return HOME_PATH_RE.sub('~', node)
    if isinstance(node, list):
        return [relativize_paths(x) for x in node]
    if isinstance(node, dict):
        return {relativize_paths(k): relativize_paths(v) for k, v in node.items()}
    return node


def write_scorecard(out_dir: Path, card: dict) -> Path:
    card = relativize_paths(card)
    try:
        import jsonschema
        jsonschema.validate(card, json.loads(SCHEMA_PATH.read_text(encoding='utf-8')))
    except ImportError:  # pragma: no cover - jsonschema is a test dependency here
        pass
    path = Path(out_dir) / 'scorecard.json'
    path.write_text(json.dumps(card, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    return path


# --------------------------------------------------------------------------- provider spend probes

def _get_json(url: str, headers: dict[str, str] | None = None, timeout: int = 20) -> dict:
    req = urllib.request.Request(url, headers={'User-Agent': 'acceptance-runner/1', **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 - fixed https endpoints
        return json.loads(resp.read().decode('utf-8'))


def _probe(fn: Callable[[], dict]) -> dict:
    try:
        return {'status': 'ok', **fn()}
    except KeyError as exc:
        return {'status': 'missing_credentials', 'detail': str(exc)}
    except Exception as exc:  # never echo URLs or headers: they can contain keys
        code = getattr(exc, 'code', None)
        return {'status': 'error', 'detail': type(exc).__name__ + (f' HTTP {code}' if code else '')}


def measure_provider_spend() -> dict:
    """Read-only account usage snapshot for the paid evidence providers. Never prints or stores keys."""
    sys.path.insert(0, str(ROOT))
    from scripts.validate_apis.common import get_secret

    def need(*names: str) -> str:
        _, value = get_secret(*names)
        if not value:
            raise KeyError(names[0])
        return value

    def apify() -> dict:
        data = _get_json('https://api.apify.com/v2/users/me/limits', {'Authorization': 'Bearer ' + need('APIFY_TOKEN')})
        current = (data.get('data') or {}).get('current') or {}
        return {'monthly_usage_usd': _num(current.get('monthlyUsageUsd'))}

    def serpapi() -> dict:
        data = _get_json('https://serpapi.com/account.json?api_key=' + need('SERPAPI_API_KEY'))
        return {'this_month_usage': _num(data.get('this_month_usage')), 'total_searches_left': _num(data.get('total_searches_left'))}

    def dataforseo() -> dict:
        token = base64.b64encode(f"{need('DATAFORSEO_LOGIN')}:{need('DATAFORSEO_PASSWORD')}".encode()).decode()
        data = _get_json('https://api.dataforseo.com/v3/appendix/user_data', {'Authorization': 'Basic ' + token})
        result = ((data.get('tasks') or [{}])[0].get('result') or [{}])[0]
        return {'balance_usd': _num((result.get('money') or {}).get('balance'))}

    return {'taken_at': now_iso(), 'apify': _probe(apify), 'serpapi': _probe(serpapi), 'dataforseo': _probe(dataforseo)}


def spend_delta(before: dict, after: dict, serpapi_usd_per_search: float | None) -> dict:
    def val(snap: dict, provider: str, key: str) -> float | None:
        entry = snap.get(provider) or {}
        return _num(entry.get(key)) if entry.get('status') == 'ok' else None

    def diff(a: float | None, b: float | None) -> float | None:
        return None if a is None or b is None else round(b - a, 4)

    apify = diff(val(before, 'apify', 'monthly_usage_usd'), val(after, 'apify', 'monthly_usage_usd'))
    dfs = diff(val(after, 'dataforseo', 'balance_usd'), val(before, 'dataforseo', 'balance_usd'))
    searches = diff(val(before, 'serpapi', 'this_month_usage'), val(after, 'serpapi', 'this_month_usage'))
    serp_usd = round(searches * serpapi_usd_per_search, 4) if searches is not None and serpapi_usd_per_search else None
    return {'apify_usd': apify, 'dataforseo_usd': dfs, 'serpapi_searches': searches, 'serpapi_usd': serp_usd}


# --------------------------------------------------------------------------- worktree and file plumbing

def resolve_ref(ref: str) -> str:
    return _git(['rev-parse', '--verify', f'{ref}^{{commit}}']).stdout.strip()


def create_worktree(sha: str) -> tuple[Path, Path]:
    parent = Path(tempfile.mkdtemp(prefix='acceptance-'))
    wt = parent / 'wt'
    subprocess.run(['git', 'worktree', 'add', '--detach', str(wt), sha], cwd=ROOT, check=True, capture_output=True, text=True)
    return parent, wt


TOOLING_LINKS = ('scripts/brand/node_modules',)  # gitignored tooling site_gate.py needs; never copied


def link_tooling(wt: Path, sources: list[Path] | None = None) -> list[str]:
    """Symlink host tooling dirs (e.g. scripts/brand/node_modules) into the worktree; skip silently when absent."""
    linked = []
    for rel in TOOLING_LINKS:
        dst = wt / rel
        src = next((r / rel for r in (sources if sources is not None else host_repo_roots()) if (r / rel).is_dir()), None)
        if src is None or dst.exists() or dst.is_symlink() or not dst.parent.is_dir():
            continue
        dst.symlink_to(src.resolve(), target_is_directory=True)
        linked.append(rel)
    return linked


def remove_worktree(parent: Path, wt: Path) -> None:
    subprocess.run(['git', 'worktree', 'remove', '--force', str(wt)], cwd=ROOT, capture_output=True, text=True)
    shutil.rmtree(parent, ignore_errors=True)
    subprocess.run(['git', 'worktree', 'prune'], cwd=ROOT, capture_output=True, text=True, check=False)


def _inside(path: Path, base: Path) -> bool:
    try:
        path.resolve().relative_to(base.resolve())
        return True
    except ValueError:
        return False


def eval_project_slug(slug: str) -> str:
    """Top-level project slug for a run: the same slug rules as a real project, so routing and gates apply."""
    return f'{EVAL_PROJECT_PREFIX}{slug}'


def stage_inputs(scenario_dir: Path, wt: Path, eval_dir: Path, reference_project: Path | None) -> list[dict]:
    """Copy the scenario and the read-only reference seed into the disposable worktree."""
    writes = []
    target = eval_dir / 'scenario'
    # Only scenario.md is copied: the agent under test must not read the answers, private values or scoring rules.
    for src in sorted(scenario_dir / name for name in SCENARIO_COPY_FILES if (scenario_dir / name).is_file()):
        dst = target / src.relative_to(scenario_dir)
        if not _inside(dst, eval_dir):
            raise RuntimeError(f'refusing to write outside the eval slug: {dst}')
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        writes.append({'kind': 'scenario_copy', 'path': str(dst)})
    if reference_project and reference_project.is_dir():
        seed_root = wt / 'projects' / REFERENCE_PROJECT_SLUG
        for rel in REFERENCE_SEED_FILES:
            src = reference_project / rel
            if src.is_file():
                dst = seed_root / rel
                if not _inside(dst, wt):
                    raise RuntimeError(f'refusing to seed outside the worktree: {dst}')
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src, dst)  # read-only use of the source; content only
                writes.append({'kind': 'reference_seed', 'path': str(dst)})
    return writes


def hide_scoring_files(wt: Path) -> list[str]:
    """Delete evals/acceptance/ inside the disposable worktree before the model starts."""
    target = wt / HIDDEN_TREE
    if not _inside(target, wt):
        raise RuntimeError(f'refusing to delete outside the worktree: {target}')
    if target.exists():
        shutil.rmtree(target)
        return [str(target)]
    return []


def out_dir_writes(out_dir: Path) -> list[dict]:
    names = ['run-manifest.json', 'transcript.jsonl', 'rounds.jsonl', 'stderr.log', 'provider-spend.json',
             'artifacts/', 'scorecard.json']
    return [{'kind': 'out_dir', 'path': str(out_dir / n)} for n in names]


def snapshot(base: Path) -> dict[str, tuple[int, int]]:
    if not base.exists():
        return {}
    return {p.relative_to(base).as_posix(): (p.stat().st_size, p.stat().st_mtime_ns)
            for p in base.rglob('*') if p.is_file() and not (COPY_SKIP_DIRS & set(p.relative_to(base).parts))}


def copy_artifacts(wt: Path, eval_dirs: list[Path], dest: Path) -> int:
    count = 0
    for d in eval_dirs:
        if not d.is_dir():
            continue
        for src in d.rglob('*'):
            rel_parts = src.relative_to(d).parts
            # scenario/ holds the runner's staged input, not agent output.
            if not src.is_file() or COPY_SKIP_DIRS & set(rel_parts) or rel_parts[:1] == ('scenario',):
                continue
            target = dest / src.relative_to(wt)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, target)
            count += 1
    return count


def claude_command(prompt: str, *, session_id: str | None, model_budget: float, wt: Path, tools_blocked: list[str],
                   model: str | None = None) -> list[str]:
    cmd = ['claude', '-p', prompt]
    if session_id:
        cmd += ['--resume', session_id]
    cmd += ['--output-format', 'stream-json', '--verbose', '--include-hook-events',
            '--max-budget-usd', f'{model_budget:.2f}', '--permission-mode', 'acceptEdits', '--permission-prompts', 'none']
    if model:
        cmd += ['--model', model]
    if (wt / '.mcp.json').is_file():
        cmd += ['--strict-mcp-config', '--mcp-config', str(wt / '.mcp.json')]
    cmd += ['--settings', bash_guard_settings(wt)]
    cmd += ['--allowedTools', *ALLOWED_TOOLS, '--disallowedTools', *tools_blocked]
    return cmd


def run_round(cmd: list[str], *, cwd: Path, transcript: Path, stderr_log: Path, timeout_s: float) -> dict:
    """Run one `claude -p` invocation, appending stream-json to the transcript."""
    start_lines = _count_lines(transcript)
    started = time.monotonic()
    with transcript.open('a', encoding='utf-8') as out, stderr_log.open('a', encoding='utf-8') as err:
        proc = subprocess.Popen(cmd, cwd=cwd, stdout=out, stderr=err, text=True, start_new_session=True)
        timed_out = False
        try:
            proc.wait(timeout=max(1.0, timeout_s))
        except subprocess.TimeoutExpired:
            timed_out = True
            terminate(proc)
        except BaseException:
            # Ctrl-C / SIGTERM: the child runs in its own session and never sees SIGINT, so stop it explicitly.
            terminate(proc)
            raise
    end_lines = _count_lines(transcript)
    session, final, cost = None, '', 0.0
    for raw in transcript.read_text(encoding='utf-8', errors='replace').splitlines()[start_lines:end_lines]:
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            continue
        session = obj.get('session_id') or session
        if obj.get('type') == 'result':
            final = obj.get('result') if isinstance(obj.get('result'), str) else final
            cost = max(cost, _num(obj.get('total_cost_usd')) or 0.0)  # session-cumulative, repeated per event
        elif obj.get('type') == 'assistant' and obj.get('parent_tool_use_id') in (None, ''):
            texts = [b.get('text', '') for b in (obj.get('message') or {}).get('content') or [] if isinstance(b, dict) and b.get('type') == 'text']
            final = texts[-1] if texts and texts[-1] else final
    return {'line_start': start_lines, 'line_end': end_lines, 'session_id': session, 'final_text': final,
            'session_cost_usd': round(cost, 4), 'exit_code': proc.returncode, 'timed_out': timed_out,
            'duration_s': round(time.monotonic() - started, 1)}


def terminate(proc) -> None:
    """SIGTERM the child's process group, wait, then SIGKILL; a group that is already gone is fine."""
    for sig, wait_s in ((signal.SIGTERM, 30), (signal.SIGKILL, 30)):
        try:
            os.killpg(proc.pid, sig)
        except (ProcessLookupError, PermissionError):
            return
        try:
            proc.wait(timeout=wait_s)
            return
        except subprocess.TimeoutExpired:
            continue


def _raise_interrupt(signum, frame):
    raise KeyboardInterrupt(f'signal {signum}')


class signals_interrupt:
    """While active, SIGTERM and SIGHUP raise KeyboardInterrupt so every finally (kill, cleanup) runs."""

    def __enter__(self):
        self.saved = {}
        for sig in (signal.SIGTERM, getattr(signal, 'SIGHUP', None)):
            if sig is None:
                continue
            try:
                self.saved[sig] = signal.signal(sig, _raise_interrupt)
            except (ValueError, OSError):  # not the main thread
                pass
        return self

    def __exit__(self, *exc):
        for sig, handler in self.saved.items():
            signal.signal(sig, handler)
        return False


def _count_lines(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open('rb') as fh:
        return sum(1 for _ in fh)


# --------------------------------------------------------------------------- orchestration

def run_acceptance(scenario_dir: Path = DEFAULT_SCENARIO, out_dir: Path | None = None, *, ref: str = 'HEAD',
                   budget_usd: float = 25.0, model_budget_usd: float = 40.0, dry_run: bool = False,
                   reference_project: Path | None = None, now: str | None = None, model: str | None = None,
                   serpapi_usd_per_search: float | None = None, max_rounds: int = MAX_ROUNDS):
    """Run the scenario on a disposable worktree of `ref`. Live: returns the scorecard path. Dry run: returns the plan."""
    check_budgets(budget_usd, model_budget_usd)
    scenario_dir = Path(scenario_dir)
    stamp = now or datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')
    slug = f'{scenario_dir.name}-{stamp}'
    alt_slug = eval_project_slug(slug)
    out_dir = Path(out_dir) if out_dir else ROOT / 'evals/acceptance/runs' / f'{ref.replace("/", "-")}-{stamp}'
    reference_project = Path(reference_project) if reference_project else default_reference_project()
    sha = resolve_ref(ref)
    tools_blocked = blocked_tools(host_repo_roots())
    with signals_interrupt():
        return _run_in_worktree(scenario_dir, out_dir, sha, slug, alt_slug, ref, budget_usd, model_budget_usd, dry_run,
                                reference_project, model, serpapi_usd_per_search, max_rounds, tools_blocked)


def _run_in_worktree(scenario_dir, out_dir, sha, slug, alt_slug, ref, budget_usd, model_budget_usd, dry_run,
                     reference_project, model, serpapi_usd_per_search, max_rounds, tools_blocked):
    parent, wt = create_worktree(sha)
    try:
        eval_dir = wt / 'projects' / alt_slug  # a top-level slug: route_workflow --project accepts it unchanged
        eval_dirs = [eval_dir]
        removed = hide_scoring_files(wt)
        tooling = link_tooling(wt)
        writes = stage_inputs(scenario_dir, wt, eval_dir, reference_project)
        eval_rel = f'projects/{alt_slug}'
        prompt = load_prompt(scenario_dir, budget_usd=budget_usd, eval_dir=eval_rel, alt_slug=alt_slug)
        if dry_run:
            plan = {'ref': ref, 'ref_sha': sha, 'worktree': str(wt), 'eval_dirs': [str(d) for d in eval_dirs],
                    'project_slug': alt_slug,
                    'out_dir': str(out_dir), 'writes': writes + out_dir_writes(out_dir),
                    'reference_seeded': any(w['kind'] == 'reference_seed' for w in writes),
                    'removed_from_worktree': removed, 'tooling_linked': tooling,
                    'first_command': claude_command(prompt[:80] + '...', session_id=None, model_budget=model_budget_usd,
                                                    wt=wt, tools_blocked=tools_blocked, model=model),
                    'blocked_tools': tools_blocked}
            print_plan(plan)
            return plan
        return _live(scenario_dir, out_dir, wt, eval_dirs, writes, prompt, slug, alt_slug, eval_rel, ref, sha,
                     budget_usd, model_budget_usd, tools_blocked, model, serpapi_usd_per_search, max_rounds)
    finally:
        remove_worktree(parent, wt)


def _live(scenario_dir, out_dir, wt, eval_dirs, writes, prompt, slug, alt_slug, eval_rel, ref, sha,
          budget_usd, model_budget_usd, tools_blocked, model, serpapi_usd_per_search, max_rounds) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    transcript, stderr_log, rounds_log = out_dir / 'transcript.jsonl', out_dir / 'stderr.log', out_dir / 'rounds.jsonl'
    for p in (transcript, stderr_log, rounds_log):
        p.write_text('', encoding='utf-8')
    feeder = Feeder.load(scenario_dir / 'founder-answers.json', eval_dir=eval_rel, alt_slug=alt_slug, budget_usd=budget_usd)
    manifest = {'scenario': scenario_dir.name, 'ref': ref, 'ref_sha': sha, 'eval_slug': slug, 'alt_slug': alt_slug,
                'eval_dirs': [str(d.relative_to(wt)) for d in eval_dirs], 'budget_usd': budget_usd,
                'model_budget_usd': model_budget_usd, 'blocked_tools': tools_blocked, 'allowed_tools': ALLOWED_TOOLS,
                'reference_seeded': any(w['kind'] == 'reference_seed' for w in writes), 'started_at': now_iso(),
                'dry_run': False, 'limits': {'max_rounds': max_rounds, 'round_timeout_s': ROUND_TIMEOUT_S, 'wall_cap_s': WALL_CAP_S}}
    (out_dir / 'run-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    before_projects = snapshot(wt / 'projects')
    before_host = {root: snapshot(root / 'projects') for root in host_repo_roots()}
    spend = {'before': measure_provider_spend()}
    started, spent, session = time.monotonic(), 0.0, None
    message, kind, matched, stop = prompt, 'initial', [], 'max_rounds'
    try:
        for rnd in range(max_rounds):
            remaining_wall = WALL_CAP_S - (time.monotonic() - started)
            remaining_model = model_budget_usd - spent
            if remaining_wall <= 60:
                stop = 'wall_cap'
                break
            if remaining_model < MIN_ROUND_BUDGET_USD:
                stop = 'model_budget'
                break
            cmd = claude_command(message, session_id=session, model_budget=remaining_model, wt=wt,
                                 tools_blocked=tools_blocked, model=model)
            info = run_round(cmd, cwd=wt, transcript=transcript, stderr_log=stderr_log,
                             timeout_s=min(ROUND_TIMEOUT_S, remaining_wall))
            previous = spent
            spent = max(spent, info['session_cost_usd'])  # cumulative across --resume
            session = info['session_id'] or session
            record = {'round': rnd, 'kind': kind, 'matched_ids': matched, 'prompt': message,
                      'cost_usd': round(spent - previous, 4),
                      **{k: v for k, v in info.items() if k != 'final_text'}, 'final_text_tail': info['final_text'][-600:]}
            with rounds_log.open('a', encoding='utf-8') as fh:
                fh.write(json.dumps(record, ensure_ascii=False) + '\n')
            if info['timed_out']:
                stop = 'round_timeout'
                break
            if not session:
                stop = 'no_session_id'
                break
            nxt = feeder.reply(info['final_text'], rounds_left=max_rounds - rnd - 1)
            if nxt is None:
                stop = 'completed'
                break
            kind, message, matched = nxt
    finally:
        spend['after'] = measure_provider_spend()
        spend['delta'] = spend_delta(spend['before'], spend['after'], serpapi_usd_per_search)
        (out_dir / 'provider-spend.json').write_text(json.dumps(spend, indent=2) + '\n', encoding='utf-8')
        copy_artifacts(wt, eval_dirs, out_dir / 'artifacts')
        manifest.update(finished_at=now_iso(), wall_time_s=round(time.monotonic() - started, 1), stop_reason=stop,
                        writes_outside_eval=writes_outside_eval(wt, eval_dirs, before_projects, before_host))
        (out_dir / 'run-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    card = score(out_dir, scenario_dir / 'checkpoints.json', scenario_dir)
    return write_scorecard(out_dir, card)


def writes_outside_eval(wt: Path, eval_dirs: list[Path], before: dict, before_host: dict | None = None) -> list[str]:
    after = snapshot(wt / 'projects')
    prefixes = [d.relative_to(wt / 'projects').as_posix() + '/' for d in eval_dirs]
    # Guarded project APIs keep a per-project migration lock under _infra; it belongs to the eval project.
    prefixes += [f'{MIGRATION_COORDINATION}/{d.name}/' for d in eval_dirs if d.parent == wt / 'projects']
    changed = [f'projects/{rel}' for rel, meta in after.items()
               if before.get(rel) != meta and not any(rel.startswith(p) for p in prefixes)]
    status = subprocess.run(['git', 'status', '--porcelain'], cwd=wt, capture_output=True, text=True, check=False).stdout
    changed += [f'repo:{line.strip()}' for line in status.splitlines()
                if line.strip() and HIDDEN_TREE + '/' not in line  # the runner's own deletion is not an agent write
                and line[3:].strip().rstrip('/') not in TOOLING_LINKS]  # nor its tooling symlinks
    # The agent can reach host checkouts by absolute path through allowed Bash; audit their projects/ trees too.
    for root, snap in (before_host or {}).items():
        after_host = snapshot(Path(root) / 'projects')
        changed += [f'host:{Path(root) / "projects" / rel}' for rel in sorted(set(snap) | set(after_host))
                    if snap.get(rel) != after_host.get(rel)]
    return sorted(changed)


def print_plan(plan: dict) -> None:
    print(f"[dry-run] ref {plan['ref']} -> {plan['ref_sha']}")
    print(f"[dry-run] disposable worktree: {plan['worktree']} (removed after the run)")
    print('[dry-run] eval project dirs (only source of copied artifacts):')
    for d in plan['eval_dirs']:
        print(f'  {d}')
    print(f"[dry-run] reference workspace seeded: {plan['reference_seeded']}")
    for r in plan.get('removed_from_worktree', []):
        print(f'[dry-run] hidden from the agent (deleted in worktree): {r}')
    print('[dry-run] planned writes:')
    for w in plan['writes']:
        print(f"  {w['kind']:<15} {w['path']}")
    print('[dry-run] first command (prompt truncated): ' + ' '.join(plan['first_command'][:14]) + ' ...')
    print(f"[dry-run] blocked tools ({len(plan['blocked_tools'])}): " + ', '.join(plan['blocked_tools']))
    print('[dry-run] no model call and no provider call were made.')


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--scenario', type=Path, default=DEFAULT_SCENARIO)
    ap.add_argument('--ref', default='HEAD', help=f'git ref to test (baseline: {BASELINE_REF})')
    ap.add_argument('--out', type=Path, default=None, help='run output dir (default evals/acceptance/runs/<ref>-<ts>)')
    ap.add_argument('--budget-usd', type=float, default=25.0, help='paid evidence cap stated to the agent and measured')
    ap.add_argument('--model-budget-usd', type=float, default=40.0, help='passed to claude --max-budget-usd')
    ap.add_argument('--reference-project', type=Path, default=None)
    ap.add_argument('--model', default=None)
    ap.add_argument('--serpapi-usd-per-search', type=float, default=None, help='price SerpApi searches into USD')
    ap.add_argument('--max-rounds', type=int, default=MAX_ROUNDS)
    ap.add_argument('--dry-run', action='store_true', help='create/remove the worktree and print planned writes only')
    ap.add_argument('--score-only', type=Path, default=None, help='rescore an existing out_dir')
    ap.add_argument('--bash-guard', default=None, metavar='WORKTREE', help=argparse.SUPPRESS)  # PreToolUse hook mode
    args = ap.parse_args(argv)
    if args.bash_guard:
        return bash_guard_hook(args.bash_guard)
    try:
        check_budgets(args.budget_usd, args.model_budget_usd)
    except ValueError as exc:
        print(f'error: {exc}', file=sys.stderr)
        return 2
    if args.score_only:
        path = write_scorecard(args.score_only, score(args.score_only, args.scenario / 'checkpoints.json', args.scenario))
        print(path)
        return 0
    result = run_acceptance(args.scenario, args.out, ref=args.ref, budget_usd=args.budget_usd,
                            model_budget_usd=args.model_budget_usd, dry_run=args.dry_run,
                            reference_project=args.reference_project, model=args.model,
                            serpapi_usd_per_search=args.serpapi_usd_per_search, max_rounds=min(args.max_rounds, MAX_ROUNDS))
    if not args.dry_run:
        card = json.loads(Path(result).read_text(encoding='utf-8'))
        print(f"{result}: {card['summary']['passed']}/{card['summary']['total']} checkpoints passed")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
