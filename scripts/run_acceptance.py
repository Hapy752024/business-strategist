#!/usr/bin/env python3
"""End-to-end acceptance run: a founder scenario driven headlessly through `claude -p`, then scored.

The run happens in a disposable detached git worktree of --ref (default HEAD; the baseline uses
486a7ae). The scenario is copied to projects/_eval/<slug>-<timestamp>/scenario/ inside that worktree,
plus a read-only copy of the reference project's manifests so the workspace check has something to
offer. Intake questions are answered from founder-answers.json by resuming the session. Produced files
are copied from the eval project directories only; the worktree is always removed.

--dry-run creates and removes the worktree, prints planned writes, and runs no model and no provider.
A live run spends model tokens (capped by --model-budget-usd) and paid evidence APIs. Provider spend
cannot be enforced inside the tree under test: the cap is stated in the prompt and spend is measured
before/after from provider account endpoints and recorded in the scorecard.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
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
MAX_ROUNDS = 12
ROUND_TIMEOUT_S = 45 * 60
WALL_CAP_S = 4 * 60 * 60
MIN_ROUND_BUDGET_USD = 0.5
REFERENCE_PROJECT_SLUG = 'german-insurance-opportunity'
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
    'Bash(git log*)', 'Bash(git rev-parse*)', 'Bash(node *)', 'Bash(npm *)', 'Bash(npx *)',
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
    'Bash(git push*)', 'Bash(git commit*)', 'Bash(git remote*)', 'Bash(gh *)', 'Bash(curl*)', 'Bash(wget*)',
    'Bash(vercel*)', 'Bash(npx vercel*)', 'Bash(netlify*)', 'Bash(npx netlify*)', 'Bash(wrangler*)',
    'Bash(npx wrangler*)', 'Bash(firebase*)', 'Bash(npx firebase*)', 'Bash(npm publish*)',
    'Bash(python3 scripts/fal_assets.py*)', 'Bash(python3 scripts/brand/finalize_fal_assets.py*)',
    'Bash(python3 scripts/brand/indexnow_ping.py*)', 'Bash(python3 scripts/marketing/execute.py*)',
]

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


def blocked_tools(host_roots: Iterable[Path]) -> list[str]:
    host = []
    for root in host_roots:
        host += [f'Edit(/{root}/**)', f'Write(/{root}/**)']  # `//abs/path` form: never edit the host checkouts
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


PRIVATE_ANSWERS = 'founder-answers.private.json'
SCENARIO_COPY_EXCLUDE = {PRIVATE_ANSWERS, '.gitignore'}


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
    return re.search(r'(?<![a-z0-9])' + re.escape(keyword.lower()), text) is not None


class Feeder:
    """Answers the agent's end-of-turn questions from founder-answers.json by keyword match."""

    def __init__(self, data: dict, *, eval_dir: str, alt_slug: str, budget_usd: float):
        self.data = data
        self.subs = {'{eval_dir}': eval_dir, '{alt_slug}': alt_slug, '{budget_usd}': f'{budget_usd:g}'}
        self.nudges_left = int(data.get('nudge', {}).get('max', 4))
        self.marker = str(data.get('completion_marker', 'journey complete')).lower()

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
        questions = question_sentences(text)
        context = ' '.join(questions) if questions else text[-600:]
        context = context.lower()
        scored = []
        for order, entry in enumerate(self.data.get('answers', [])):
            hits = sum(_kw_hit(k, context) for k in entry.get('keywords', []))
            if hits:
                scored.append((-hits, order, entry))
        return [e for _, _, e in sorted(scored, key=lambda t: (t[0], t[1]))]

    def text_for(self, entry: dict) -> str:
        if entry.get('answer'):
            return self._fill(entry['answer'])
        generic = self.data.get('generic', {})
        return generic.get('text') or 'Please proceed under a stated assumption.'

    def reply(self, final_text: str) -> tuple[str, str, list[str]] | None:
        """Return (kind, reply, matched_ids), or None when the run should stop."""
        text = final_text or ''
        if self.marker in text.lower():
            return None
        asks = bool(question_sentences(text[-800:])) or bool(INTAKE_PATTERN.search(text[-400:]))
        if asks:
            matched = self.match(text)
            if not matched:
                return 'generic', self.text_for({}), []
            parts = list(dict.fromkeys(self.text_for(e) for e in matched))
            return 'answer', '\n\n'.join(parts), [e['id'] for e in matched]
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
    # A hook denial is reported both as a hook event and as an error tool result; count each line once.
    seen, unique = set(), []
    for e in events:
        key = (e['line'], e['tool'])
        if key not in seen:
            seen.add(key)
            unique.append(e)
            by_tool[e['tool']] = by_tool.get(e['tool'], 0) + 1
    return {'count': len(unique), 'by_tool': by_tool, 'events': unique}


# --------------------------------------------------------------------------- checks

CHECK_TYPES = {'all', 'any', 'not', 'text', 'tool_use', 'artifact', 'json_len', 'jsonl_distinct', 'order',
               'max_questions_per_turn', 'answers_persisted', 'hook_denials', 'gate_sequence', 'provider_gaps'}


def validate_check(check: dict) -> None:
    if not isinstance(check, dict) or check.get('type') not in CHECK_TYPES:
        raise ValueError(f'unknown check: {check!r}')
    for child in check.get('checks', []):
        validate_check(child)
    for key in ('check', 'first', 'then'):
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
        docs: list[tuple[str, str]] = []
        if scope in ('assistant', 'both'):
            by_round: dict[int, list[str]] = {}
            first_line: dict[int, int] = {}
            for ev in self.events:
                if ev['kind'] == 'text':
                    by_round.setdefault(ev['round'], []).append(ev['text'])
                    first_line.setdefault(ev['round'], ev['line'])
            docs += [(f'transcript.jsonl#L{first_line[r] + 1}', '\n'.join(t)) for r, t in sorted(by_round.items())]
        if scope in ('artifacts', 'both'):
            docs += [(self.rel(p), self.read(p)) for p in self.files() if p.suffix.lower() in TEXT_SUFFIXES]
        return docs


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


Result = tuple[bool, str | None, str]  # passed, evidence_path, detail


def _tool_matches(ctx: Ctx, check: dict) -> list[dict]:
    name_re, input_re = re.compile(check.get('name', '.*')), re.compile(check.get('input', '.*'))
    result_re = re.compile(check['result']) if check.get('result') else None
    hits = []
    for ev in ctx.events:
        if ev['kind'] != 'tool_use' or not name_re.search(ev['name']) or not input_re.search(ev['input_text']):
            continue
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
    kind = check['type']
    label = check.get('label') or kind
    if kind in ('all', 'any'):
        results = [(c, run_check(ctx, c)) for c in check['checks']]
        oks = [r for _, r in results if r[0]]
        if kind == 'all':
            failed = [(c.get('label') or c['type'], r[2]) for c, r in results if not r[0]]
            evidence = next((r[1] for _, r in results if r[1]), None)
            if failed:
                return False, evidence, 'missing: ' + '; '.join(f'{l} ({d})' for l, d in failed)
            return True, evidence, 'all sub-checks passed'
        if oks:
            return True, oks[0][1], oks[0][2]
        return False, None, f'{label}: none matched (' + '; '.join(r[2] for _, r in results) + ')'
    if kind == 'not':
        ok, ev, detail = run_check(ctx, check['check'])
        return (not ok), ev, (f'{label}: forbidden event found ({detail})' if ok else f'{label}: none found')
    if kind == 'text':
        pats = [re.compile(p) for p in check['patterns']]
        for ref, text in ctx.documents(check.get('scope', 'both')):
            if all(p.search(text) for p in pats):
                return True, ref, f'{label}: all patterns in one document'
        return False, None, f'{label}: no single document matched all {len(pats)} patterns'
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
        return len(hits) >= need, (ctx.rel(hits[0]) if hits else None), f"{label}: {len(hits)} file(s) match {check['glob']}"
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
        answered = {r['round'] for r in ctx.rounds if r.get('kind') in ('answer', 'generic')}
        worst, worst_ref, checked = 0, None, 0
        for r in ctx.rounds:
            if r['round'] + 1 not in answered:
                continue
            final = round_final_text(ctx, r['round'])
            checked += 1
            n = count_questions(final)
            if n > worst:
                worst, worst_ref = n, f"rounds.jsonl#round{r['round']}"
        limit = int(check.get('max', 1))
        if not checked:
            return False, None, 'proxy: no answered intake turns to measure'
        return worst <= limit, worst_ref, f'proxy: max {worst} question sentence(s) over {checked} answered turn(s), limit {limit}'
    if kind == 'answers_persisted':
        feeder_data = _founder_answers(ctx)
        fed = [i for r in ctx.rounds if r.get('kind') == 'answer' for i in r.get('matched_ids', [])]
        with_markers = [e for e in feeder_data.get('answers', []) if e.get('id') in set(fed) and e.get('persist_markers')]
        if not with_markers:
            return False, None, 'answers_persisted: no fed answer carried persist markers (not exercised)'
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


def gate_sequence(ctx: Ctx, check: dict) -> Result:
    route_re, blocked_re = re.compile(check['route']), re.compile(check['blocked'])
    override_re, down_re = re.compile(check['override']), re.compile(check['downstream'])
    blocks, overrides, downstream = [], [], []
    for ev in ctx.events:
        if ev['kind'] != 'tool_use':
            continue
        res = ev.get('result') or {'text': '', 'is_error': False}
        if ev['name'] == 'Bash' and route_re.search(ev['input_text']):
            if override_re.search(ev['input_text']):
                if not res['is_error']:
                    overrides.append(ev['idx'])
            elif blocked_re.search(res['text']):
                blocks.append(ev['idx'])
        elif ev['name'] == 'Skill' and down_re.search(ev['input_text']):
            if ev['denied'] and re.search(r'(?i)gate', res['text']):
                blocks.append(ev['idx'])
            elif not res['is_error']:
                downstream.append(ev['idx'])
    if not blocks:
        return False, None, 'gate: no blocked gated route observed'
    if not overrides:
        return False, _line_ref(ctx, blocks[0]), 'gate: blocked, but no --override-gate call recorded'
    first_override = min(o for o in overrides if o > blocks[0]) if any(o > blocks[0] for o in overrides) else None
    if first_override is None:
        return False, _line_ref(ctx, overrides[0]), 'gate: override recorded before any block'
    early = [d for d in downstream if d < first_override]
    if early:
        return False, _line_ref(ctx, early[0]), 'gate: a downstream skill ran before the override'
    late = [d for d in downstream if d > first_override]
    if not late:
        return False, _line_ref(ctx, first_override), 'gate: override recorded but no downstream stage ran'
    return True, _line_ref(ctx, first_override), f'gate: blocked, overridden, then {len(late)} downstream call(s)'


def provider_status(ctx: Ctx) -> dict:
    ok, failed = set(), set()
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
    return {'attempted': sorted(ok | failed), 'ok': sorted(ok), 'failed': sorted(failed),
            'source': 'summary.json provider attempts in eval-project artifacts'}


def provider_gaps(ctx: Ctx, check: dict) -> Result:
    status = provider_status(ctx)
    docs = ctx.documents('assistant')
    absence = [re.compile(p) for p in check['absence_patterns']]
    for ref, text in docs:
        if any(p.search(text) for p in absence):
            return False, ref, 'proxy: an assistant round states absence of demand'
    if not status['failed']:
        return True, None, 'proxy: no provider failure observed in run summaries (gap reporting not exercised)'
    gaps = [re.compile(p) for p in check['gap_patterns']]
    for ref, text in docs:
        if any(p.search(text) for p in gaps):
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
    any_measured = any(v is not None for v in (apify, dfs, serp_usd))
    over = (measured > budget_usd) if (any_measured and budget_usd is not None) else None
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
        ok, evidence, detail = run_check(ctx, cp['check'])
        cps.append({'id': cp['id'], 'stage': cp['stage'], 'title': cp['title'], 'passed': bool(ok),
                    'proxy': bool(cp.get('proxy')), 'evidence_path': evidence, 'detail': detail})
    model_usd, tokens, perm = 0.0, {'input': 0, 'output': 0, 'cache_creation': 0, 'cache_read': 0}, 0
    session = None
    for ev in ctx.events:
        if ev['kind'] != 'result':
            continue
        obj = ev['obj']
        model_usd += _num(obj.get('total_cost_usd')) or 0.0
        usage = obj.get('usage') or {}
        tokens['input'] += int(usage.get('input_tokens') or 0)
        tokens['output'] += int(usage.get('output_tokens') or 0)
        tokens['cache_creation'] += int(usage.get('cache_creation_input_tokens') or 0)
        tokens['cache_read'] += int(usage.get('cache_read_input_tokens') or 0)
        perm += len(obj.get('permission_denials') or [])
        session = obj.get('session_id') or session
    budget = _num(manifest.get('budget_usd'))
    provider_spend, over = spend_summary(out_dir, budget)
    passed = sum(c['passed'] for c in cps)
    notes = [
        'Checkpoints marked proxy test presence or a countable stand-in, not the quality judgement in their title.',
        'Provider spend is measured, not enforced; see cost.provider_spend.notes.',
        'Artifacts are copied only from the eval project directories; work written elsewhere is listed in writes_outside_eval, not scored.',
    ]
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
        'summary': {'total': len(cps), 'passed': passed, 'failed': len(cps) - passed, 'proxy': sum(c['proxy'] for c in cps)},
        'providers': provider_status(ctx),
        'cost': {'model_usd': round(model_usd, 4), 'model_budget_usd': _num(manifest.get('model_budget_usd')),
                 'budget_usd': budget, 'provider_spend': provider_spend, 'over_budget': over, 'spend_enforced': False},
        'wall_time_s': _num(manifest.get('wall_time_s')),
        'tokens': tokens,
        'hook_denials': hook_denials(ctx.parsed),
        'permission_denials': perm,
        'writes_outside_eval': list(manifest.get('writes_outside_eval', [])),
        'friction': str(manifest.get('friction', '')),
        'honesty_notes': notes,
    }


def write_scorecard(out_dir: Path, card: dict) -> Path:
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


def stage_inputs(scenario_dir: Path, wt: Path, eval_dir: Path, reference_project: Path | None) -> list[dict]:
    """Copy the scenario and the read-only reference seed into the disposable worktree."""
    writes = []
    target = eval_dir / 'scenario'
    # The private answers file is never copied: the agent under test must not read the founder's private values.
    for src in sorted(p for p in scenario_dir.rglob('*') if p.is_file() and p.name not in SCENARIO_COPY_EXCLUDE):
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
            if not src.is_file() or COPY_SKIP_DIRS & set(rel_parts) or (d.parent.name == '_eval' and rel_parts[:1] == ('scenario',)):
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
            try:
                os.killpg(proc.pid, signal.SIGTERM)
                proc.wait(timeout=30)
            except Exception:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait()
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
            cost += _num(obj.get('total_cost_usd')) or 0.0
        elif obj.get('type') == 'assistant' and obj.get('parent_tool_use_id') in (None, ''):
            texts = [b.get('text', '') for b in (obj.get('message') or {}).get('content') or [] if isinstance(b, dict) and b.get('type') == 'text']
            final = texts[-1] if texts and texts[-1] else final
    return {'line_start': start_lines, 'line_end': end_lines, 'session_id': session, 'final_text': final,
            'cost_usd': round(cost, 4), 'exit_code': proc.returncode, 'timed_out': timed_out,
            'duration_s': round(time.monotonic() - started, 1)}


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
    alt_slug = f'eval-{slug}'
    out_dir = Path(out_dir) if out_dir else ROOT / 'evals/acceptance/runs' / f'{ref.replace("/", "-")}-{stamp}'
    reference_project = Path(reference_project) if reference_project else default_reference_project()
    sha = resolve_ref(ref)
    tools_blocked = blocked_tools(host_repo_roots())
    parent, wt = create_worktree(sha)
    try:
        eval_dir = wt / 'projects/_eval' / slug
        eval_dirs = [eval_dir, wt / 'projects' / alt_slug]
        writes = stage_inputs(scenario_dir, wt, eval_dir, reference_project)
        eval_rel = f'projects/_eval/{slug}'
        prompt = load_prompt(scenario_dir, budget_usd=budget_usd, eval_dir=eval_rel, alt_slug=alt_slug)
        if dry_run:
            plan = {'ref': ref, 'ref_sha': sha, 'worktree': str(wt), 'eval_dirs': [str(d) for d in eval_dirs],
                    'out_dir': str(out_dir), 'writes': writes + out_dir_writes(out_dir),
                    'reference_seeded': any(w['kind'] == 'reference_seed' for w in writes),
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
            spent += info['cost_usd']
            session = info['session_id'] or session
            record = {'round': rnd, 'kind': kind, 'matched_ids': matched, 'prompt': message,
                      **{k: v for k, v in info.items() if k != 'final_text'}, 'final_text_tail': info['final_text'][-600:]}
            with rounds_log.open('a', encoding='utf-8') as fh:
                fh.write(json.dumps(record, ensure_ascii=False) + '\n')
            if info['timed_out']:
                stop = 'round_timeout'
                break
            if not session:
                stop = 'no_session_id'
                break
            nxt = feeder.reply(info['final_text'])
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
                        writes_outside_eval=writes_outside_eval(wt, eval_dirs, before_projects))
        (out_dir / 'run-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    card = score(out_dir, scenario_dir / 'checkpoints.json', scenario_dir)
    return write_scorecard(out_dir, card)


def writes_outside_eval(wt: Path, eval_dirs: list[Path], before: dict) -> list[str]:
    after = snapshot(wt / 'projects')
    prefixes = [d.relative_to(wt / 'projects').as_posix() + '/' for d in eval_dirs]
    changed = [f'projects/{rel}' for rel, meta in after.items()
               if before.get(rel) != meta and not any(rel.startswith(p) for p in prefixes)]
    status = subprocess.run(['git', 'status', '--porcelain'], cwd=wt, capture_output=True, text=True, check=False).stdout
    changed += [f'repo:{line.strip()}' for line in status.splitlines() if line.strip()]
    return sorted(changed)


def print_plan(plan: dict) -> None:
    print(f"[dry-run] ref {plan['ref']} -> {plan['ref_sha']}")
    print(f"[dry-run] disposable worktree: {plan['worktree']} (removed after the run)")
    print('[dry-run] eval project dirs (only source of copied artifacts):')
    for d in plan['eval_dirs']:
        print(f'  {d}')
    print(f"[dry-run] reference workspace seeded: {plan['reference_seeded']}")
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
    args = ap.parse_args(argv)
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
