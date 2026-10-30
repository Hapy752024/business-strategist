"""Validate the intent/page map and capture bindings; legacy maps need reviewed conversion."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

from jsonschema import Draft202012Validator, FormatChecker

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.marketing.link_observations import ROOT, bound_bytes, url_key

SCHEMA = json.loads((ROOT / 'schemas/keyword-map.schema.json').read_text())
OPPORTUNITIES = json.loads((ROOT / 'schemas/content-opportunities.schema.json').read_text())
QUESTIONS = json.loads((ROOT / 'schemas/customer-questions.schema.json').read_text())
RESOURCE = json.loads((ROOT / 'schemas/content-brief.schema.json').read_text())['properties']['public_resource']


def validate(document: dict, base: Path | None = None, staged: dict | None = None) -> list[str]:
    errors = [e.message for e in Draft202012Validator(SCHEMA, format_checker=FormatChecker()).iter_errors(document)]
    if errors:
        return errors
    ids, assignments = set(), {}
    for row in document['rows']:
        if row['id'] in ids:
            errors.append('duplicate page-map row ID: ' + row['id'])
        ids.add(row['id'])
        identity = (row['locale'], row['primary_term'].casefold().strip())
        if identity in assignments and assignments[identity] != row['target_url'] and not row.get('assignment_exception', '').strip():
            errors.append('conflicting primary assignment needs reviewed exception: ' + row['id'])
        assignments[identity] = row['target_url']
        for value in [row['target_url'], *row.get('internal_links', []),
                      *[row[k] for k in ('existing_url', 'redirect_to') if row.get(k)]]:
            try:
                url_key(value)
            except ValueError:
                errors.append('invalid page-map URL: ' + row['id'])
        if row['decision'] != 'create' and not row['existing_url']:
            errors.append('existing-page decision needs existing_url: ' + row['id'])
        if row['decision'] == 'create' and row['existing_url']:
            errors.append('existing page requires retain/improve/consolidate decision: ' + row['id'])
        if row['decision'] in {'consolidate', 'retire'} and 'redirect_to' not in row:
            errors.append('consolidate/retire requires intentional redirect_to (null allowed): ' + row['id'])
        if row.get('volume') is not None and not ((row.get('volume_provider') and row.get('volume_checked_at'))
                                                  or (row.get('source') and row.get('fetched_at'))):
            errors.append('volume estimate requires provider and date: ' + row['id'])
        for binding in row['evidence_refs']:
            try:
                bound_bytes(binding, base, staged)
            except (ValueError, OSError) as exc:
                errors.append(row['id'] + ': ' + str(exc))
    return errors


def validate_resource(resource: dict, base: Path | None, staged: dict | None = None) -> list[str]:
    errors = [e.message for e in Draft202012Validator(RESOURCE).iter_errors(resource)]
    if errors:
        return errors
    try:
        url_key(resource['destination_url'])
        for binding in resource['source_bindings']:
            bound_bytes(binding, base, staged)
    except (ValueError, OSError) as exc:
        errors.append(str(exc))
    return errors


def render(document: dict) -> str:
    rows = ['# Page decisions', '', '| Page | Locale | Intent | Decision | Conversion path |', '| --- | --- | --- | --- | --- |']
    rows += [f"| {r['target_url']} | {r['locale']} | {r['intent']} | {r['decision']} | {r['conversion_bridge']} |" for r in document['rows']]
    return '\n'.join(rows) + '\n'


INPUT_NAMES = ('search', 'competitor_content', 'voc_questions', 'social_topics')


def _load(path: Path, schema: dict | None, label: str) -> dict:
    doc = json.loads(Path(path).read_text())
    if schema:
        errors = [e.message for e in Draft202012Validator(schema).iter_errors(doc)]
        if errors:
            raise ValueError(f'{label} invalid: ' + '; '.join(errors[:3]))
    return doc


def _topic_rows(doc: dict, label: str) -> list[dict]:
    """Minimal contract for competitor-content.json (Task 5.6) and social-topics.json (Task 5.7)."""
    rows = doc.get('rows') if isinstance(doc, dict) else None
    if not isinstance(rows, list):
        raise ValueError(f'{label} invalid: needs a rows array')
    for r in rows:
        if not (isinstance(r, dict) and isinstance(r.get('topic'), str) and r['topic'].strip()
                and isinstance(r.get('questions'), list) and all(isinstance(q, str) for q in r['questions'])
                and isinstance(r.get('refs'), list) and r['refs'] and all(isinstance(x, str) and x for x in r['refs'])
                and r.get('cluster_id', '') is not None and isinstance(r.get('cluster_id', ''), str)):
            raise ValueError(f'{label} invalid: every row needs topic (str), questions (list of str), refs (non-empty list of str); cluster_id optional')
    return rows


def _norm(text: str) -> str:
    return ' '.join(text.split()).casefold()


def merge_content_inputs(search: Path, competitor_content: Path | None = None, voc_questions: Path | None = None,
                         social_topics: Path | None = None, *, existing_map: Path | None = None, out: Path | None = None) -> dict:
    """Propose keyword-map rows from up to four content inputs, keeping per-input attribution.

    Inputs: `search` = content-opportunities.json (required; clusters, questions, SERP features, gaps);
    `voc_questions` = customer-questions.json (only kind=customer counts as customer voice; supplier and
    hypothesis items are ignored); `competitor_content` = competitor-content.json (Task 5.6) and
    `social_topics` = social-topics.json (Task 5.7). Contract those two tasks must meet: a JSON object
    `{"rows": [{"topic": str, "questions": [str], "refs": [str, non-empty], "cluster_id": str (optional)}]}`.
    A row joins the search cluster named by `cluster_id`, else the cluster whose id or query equals `topic`
    (case-insensitive); otherwise it becomes its own proposed cluster. Absent optional inputs are tolerated.

    Each proposed row lists `inputs` (name -> refs and questions) and `questions` (text -> contributing inputs).
    A cluster backed by one input is `single_input`. `existing_map` (the reviewed keyword-map.json) is matched
    first by primary/secondary term and locale: matches become `improve` with the existing URL, others `create`.
    Output goes to `out` (default `keyword-map.proposed.json` beside `search`); the reviewed map is never
    written, and the proposal is not a reviewed map.
    """
    target = Path(out) if out else Path(search).parent / 'keyword-map.proposed.json'
    if target.name == 'keyword-map.json' or (existing_map and target.resolve() == Path(existing_map).resolve()):
        raise ValueError('proposals must not overwrite a reviewed keyword map; use keyword-map.proposed.json')
    clusters: dict[str, dict] = {}
    present = ['search']

    def cluster(cid: str, **init) -> dict:
        return clusters.setdefault(cid, {'cluster_id': cid, 'terms': [], 'locale': None, 'intent': None, 'page_type': None,
                                         'journey_stage': None, 'serp_features': None, 'content_gap': None, 'inputs': {}, 'questions': {}, **init})

    def attach(c: dict, name: str, questions: list[str], refs: list[str]) -> None:
        entry = c['inputs'].setdefault(name, {'refs': [], 'questions': []})
        entry['refs'] += [r for r in refs if r not in entry['refs']]
        for q in questions:
            if q not in entry['questions']:
                entry['questions'].append(q)
            who = c['questions'].setdefault(_norm(q), {'text': q, 'inputs': []})
            if name not in who['inputs']:
                who['inputs'].append(name)

    for row in _load(search, OPPORTUNITIES, 'content-opportunities')['rows']:
        c = cluster(row['cluster_id'], terms=[q['query'] for q in row['queries']], locale=row['locale'], intent=row['intent'],
                    page_type=row['recommended_page_type'], journey_stage=row['journey_stage'],
                    serp_features=row['serp_features'], content_gap=row['content_gap']['hypothesis'])
        q = row['questions']
        attach(c, 'search', [*q['paa'], *q['related_searches'], *q['ai_overview_prompts']], row['evidence_refs'])

    def locate(cid: str | None, topic: str | None) -> dict:
        if cid and cid in clusters:
            return clusters[cid]
        if topic:
            key = _norm(topic)
            for c in clusters.values():
                if key == _norm(c['cluster_id']) or key in {_norm(t) for t in c['terms']}:
                    return c
        slug = re.sub(r'[^\w]+', '-', (topic or cid or 'topic').casefold()).strip('-')
        return cluster(cid or 'topic:' + slug, terms=[topic] if topic else [])

    ignored = 0
    if voc_questions:
        present.append('voc_questions')
        for item in _load(voc_questions, QUESTIONS, 'customer-questions')['questions']:
            if item['kind'] != 'customer':
                ignored += 1
                continue
            refs = [f"{item['id']}:{item['source']['path']}"]
            attach(locate(item.get('cluster_id'), None if item.get('cluster_id') else item['passage']), 'voc_questions', [item['passage']], refs)
    for name, path in (('competitor_content', competitor_content), ('social_topics', social_topics)):
        if path:
            present.append(name)
            for r in _topic_rows(_load(path, None, name), name):
                attach(locate(r.get('cluster_id') or None, r['topic']), name, r['questions'], r['refs'])

    existing = []
    if existing_map:
        existing = json.loads(Path(existing_map).read_text()).get('rows', [])
    rows = []
    for c in clusters.values():
        terms = [t for t in dict.fromkeys(c['terms'])]
        keys = {_norm(t) for t in terms}
        match = next((e for e in existing if (c['locale'] is None or e['locale'] == c['locale'])
                      and ({_norm(e['primary_term']), *map(_norm, e.get('secondary_terms', []))} & keys)), None)
        features = [k for k, v in (c['serp_features'] or {}).items() if v is True or v == 'observed']
        rows.append({'cluster_id': c['cluster_id'], 'primary_term': terms[0] if terms else c['cluster_id'], 'secondary_terms': terms[1:],
                     'locale': c['locale'], 'intent': c['intent'], 'journey_stage': c['journey_stage'], 'page_type': c['page_type'],
                     'content_gap_hypothesis': c['content_gap'], 'serp_features_targeted': features,
                     'questions': list(c['questions'].values()), 'inputs': c['inputs'], 'input_count': len(c['inputs']),
                     'single_input': len(c['inputs']) == 1,
                     'decision': 'improve' if match else 'create',
                     'existing_url': (match.get('existing_url') or match.get('target_url')) if match else None,
                     'matched_row_id': match['id'] if match else None, 'volume': None, 'needs_review': True})
    result = {'schema_version': 1, 'status': 'proposal', 'reviewed': False, 'inputs_present': present,
              'ignored_non_customer_questions': ignored, 'rows': rows}
    target.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    return result


def main_merge(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog='keyword_map.py merge', description='Propose keyword-map rows from content inputs (writes keyword-map.proposed.json).')
    ap.add_argument('search', type=Path, help='content-opportunities.json')
    ap.add_argument('--competitor-content', type=Path); ap.add_argument('--voc-questions', type=Path)
    ap.add_argument('--social-topics', type=Path); ap.add_argument('--existing-map', type=Path); ap.add_argument('--out', type=Path)
    a = ap.parse_args(argv)
    result = merge_content_inputs(a.search, a.competitor_content, a.voc_questions, a.social_topics, existing_map=a.existing_map, out=a.out)
    print(json.dumps({'status': result['status'], 'rows': len(result['rows']), 'single_input': sum(r['single_input'] for r in result['rows']),
                      'inputs_present': result['inputs_present']}))
    return 0


def main() -> int:
    if sys.argv[1:2] == ['merge']:
        return main_merge(sys.argv[2:])
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('map', type=Path); ap.add_argument('--base', required=True, type=Path)
    ap.add_argument('--out', type=Path)
    args = ap.parse_args()
    doc = json.loads(args.map.read_text())
    errors = validate(doc, args.base)
    if args.out and not errors:
        args.out.write_text(render(doc))
    print(json.dumps({'valid': not errors, 'errors': errors}))
    return int(bool(errors))


if __name__ == '__main__':
    raise SystemExit(main())
