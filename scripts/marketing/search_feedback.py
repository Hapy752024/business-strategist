"""Post-launch search feedback: compare a keyword map's planned clusters with real Search Console queries.

Matching rule (documented, deterministic): a query and each planned term (primary term, secondary terms and, for
proposed maps, question texts) are normalised (casefold, punctuation to spaces, whitespace collapsed). A query matches
a cluster `exact` when it equals one of its terms, or `contains` when a term's tokens appear as a contiguous run inside
the query tokens. Exact beats contains; then the longer term wins; then map order. Locale is not used for matching
(Search Console exports carry no locale). No stemming or fuzzy matching: unmatched queries are reported, not guessed.

Interpretation limits: Search Console omits rare (anonymised) queries, so a planned cluster with no matching rows is
`planned_no_impressions` (none observed in this export), not proven zero. A matching row with blank/suppressed values is
`unknown`. Output is a proposal for the keyword map's `decision` field; the reviewed map is never written.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

MIN_IMPRESSIONS = 10
LIMITATION = ('Search Console omits rare (anonymised) queries and exports are row-limited, so "no impressions" means none '
              'observed in this export, not proven zero.')


def normalise(text: str) -> str:
    return ' '.join(re.sub(r'[^\w]+', ' ', str(text).casefold()).split())


def _clusters(document: dict) -> list[dict]:
    out = []
    for row in document.get('rows', []):
        cid = row.get('id') or row.get('cluster_id')
        if not cid or not row.get('primary_term'):
            continue
        terms = [row['primary_term'], *row.get('secondary_terms', []),
                 *[q['text'] if isinstance(q, dict) else q for q in row.get('questions', [])]]
        out.append({'id': cid, 'primary_term': row['primary_term'], 'target_url': row.get('target_url') or row.get('existing_url'),
                    'terms': [t for t in dict.fromkeys(normalise(t) for t in terms if t) if t]})
    return out


def _match(query: str, clusters: list[dict]):
    q = normalise(query)
    tokens = q.split()
    best = None
    for index, cluster in enumerate(clusters):
        for term in cluster['terms']:
            t = term.split()
            if q == term:
                kind = 2
            elif any(tokens[i:i + len(t)] == t for i in range(len(tokens) - len(t) + 1)):
                kind = 1
            else:
                continue
            rank = (kind, len(t), -index)
            if best is None or rank > best[0]:
                best = (rank, cluster, 'exact' if kind == 2 else 'contains', term)
    return None if best is None else best[1:]


def _observations(gsc_export: Path, metadata: dict | None) -> dict:
    path = Path(gsc_export)
    if path.suffix.lower() == '.json':
        document = json.loads(path.read_text())
        if document.get('provider') != 'gsc' or 'observations' not in document:
            raise ValueError('JSON input must be an imported gsc-queries-v1 document')
        return document
    if not metadata:
        raise ValueError('a CSV export needs its confirmed metadata (property, period, timezone, exported_at, report_scope)')
    from scripts.marketing.import_presets import import_export
    return import_export(path, 'gsc-queries-v1', metadata)


def compare(keyword_map: Path, gsc_export: Path, *, metadata: dict | None = None, min_impressions: int = MIN_IMPRESSIONS) -> dict:
    """Compare planned clusters with real queries; returns proposals only and never writes the map."""
    clusters = _clusters(json.loads(Path(keyword_map).read_text()))
    document = _observations(gsc_export, metadata)
    meta = document['metadata']
    queries: dict[str, dict] = {}
    for obs in document['observations']:
        queries.setdefault(obs['dimension'], {})[obs['metric']] = obs['value']
    matched, unplanned, per_cluster = [], [], {c['id']: [] for c in clusters}
    for query, values in queries.items():
        hit = _match(query, clusters)
        row = {'query': query, 'impressions': values.get('impressions'), 'clicks': values.get('clicks'), 'position': values.get('position')}
        if hit:
            cluster, kind, term = hit
            per_cluster[cluster['id']].append(row)
            matched.append(row | {'cluster_id': cluster['id'], 'match': kind, 'matched_term': term})
        elif (row['impressions'] or 0) > 0:
            unplanned.append(row)
    no_impr, unknown, no_clicks = [], [], []
    for cluster in clusters:
        rows = per_cluster[cluster['id']]
        known = [r for r in rows if r['impressions'] is not None]
        ref = {'id': cluster['id'], 'primary_term': cluster['primary_term'], 'target_url': cluster['target_url']}
        if not rows:
            no_impr.append(ref)
        elif not known:
            unknown.append(ref | {'reason': 'matching export rows have blank or suppressed values'})
        for r in known:
            if r['impressions'] >= min_impressions and r['clicks'] == 0:
                no_clicks.append(r | {'cluster_id': cluster['id'], 'target_url': cluster['target_url']})
    unplanned.sort(key=lambda r: -r['impressions'])
    no_clicks.sort(key=lambda r: -r['impressions'])
    proposals = [{'signal': 'impressions_no_clicks', 'cluster_id': r['cluster_id'], 'query': r['query'], 'suggested_decision': 'improve',
                  'note': 'Hypothesis: title/snippet does not earn the click; test before rewriting.', 'reviewed': False} for r in no_clicks]
    proposals += [{'signal': 'planned_no_impressions', 'cluster_id': c['id'], 'suggested_decision': 'review',
                   'note': 'No impressions observed in this window; check indexing, publication date and window length first.', 'reviewed': False} for c in no_impr]
    proposals += [{'signal': 'unplanned_with_impressions', 'query': r['query'], 'suggested_decision': 'create',
                   'note': 'Real query with no planned cluster; candidate new content or an addition to an existing cluster.', 'reviewed': False} for r in unplanned]
    return {'schema_version': 1, 'status': 'proposal', 'reviewed': False, 'source': document['provider'], 'import_id': document.get('import_id'),
            'input_sha256': document['input_sha256'],
            'window': {k: meta[k] for k in ('period_start', 'period_end', 'timezone')},
            'matching_rule': 'normalised exact term, else contiguous term tokens inside the query; exact > contains > longer term > map order',
            'matched': matched,
            'planned_no_impressions': {'count': len(no_impr), 'clusters': no_impr, 'limitation': LIMITATION},
            'unknown': {'count': len(unknown), 'clusters': unknown},
            'impressions_no_clicks': {'count': len(no_clicks), 'min_impressions': min_impressions, 'queries': no_clicks,
                                      'interpretation': 'Title/snippet problem hypothesis only; position, intent and SERP features also lower click-through.'},
            'unplanned_with_impressions': {'count': len(unplanned), 'queries': unplanned},
            'decision_proposals': proposals}


def write_proposal(result: dict, out: Path) -> Path:
    out = Path(out)
    if out.name == 'keyword-map.json':
        raise ValueError('proposals must not overwrite a reviewed keyword map')
    tmp = out.with_name(out.name + '.tmp')
    tmp.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    tmp.replace(out)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('keyword_map', type=Path)
    ap.add_argument('gsc_export', type=Path, help='gsc-queries-v1 CSV (needs --metadata) or an imported JSON document')
    ap.add_argument('--metadata', type=Path, help='JSON export metadata for CSV input')
    ap.add_argument('--out', type=Path, help='proposal file (never keyword-map.json)')
    a = ap.parse_args()
    if a.out and a.out.resolve() == a.keyword_map.resolve():
        ap.error('--out must not be the reviewed keyword map')
    result = compare(a.keyword_map, a.gsc_export, metadata=json.loads(a.metadata.read_text()) if a.metadata else None)
    if a.out:
        write_proposal(result, a.out)
    print(json.dumps({k: result[k]['count'] for k in ('planned_no_impressions', 'unknown', 'impressions_no_clicks', 'unplanned_with_impressions')} | {'window': result['window']}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
