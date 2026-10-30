#!/usr/bin/env python3
"""Group already-collected social evidence records into discussion topics (a fourth content input).

Deterministic and explainable; no model calls, no embeddings, no new collectors.

Method
1. Keep records from discussion sources (PLATFORM below); everything else is counted in `records_skipped`.
   Duplicates (same source + source_record_id/evidence_id, or identical text) are dropped.
2. Normalise text (casefold, no URLs, hashtags become words), split into sentences, drop de/en/es stopwords.
   Key phrases per record = adjacent non-stopword bigrams plus single words of >= 4 letters.
3. Anchors = phrases found in >= MIN_RECORDS records. On corpora of >= 20 records, phrases in more than
   MAX_DF_SHARE of all records are dropped as too generic (they name the study subject, not a topic).
   Anchors are ordered: bigrams before single words, then by record count (desc), then alphabetically.
4. Walking that order, each unassigned record containing the anchor joins its topic; a topic is kept only if it
   collects >= MIN_RECORDS records. Each record belongs to at most one topic. Leftovers are `unassigned`.
5. A topic matches a search-study cluster (content-opportunities.json) when every word of its anchor appears in
   one of the cluster's queries or its id (light plural stripping). No match = candidate to check in search.

Limits: surface-word grouping misses paraphrase and synonyms, mixes senses of one phrase, and is language-agnostic
beyond the stopword lists. Engagement is attention, not need or demand, and is reported per platform only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

MIN_RECORDS = 3
MAX_DF_SHARE = 0.35
MAX_TOPICS = 30
NEEDS_REVIEW_BELOW = 5  # single-word anchors, fewer than this many records, or supplier-only topics need review and never count as an input
MAX_PHRASES = 5
PHRASE_LEN = 120
MAX_QUESTIONS = 8

# evidence `source` -> platform (only discussion/social sources; reviews, search, news and web pages are excluded)
PLATFORM = {
    'reddit': 'reddit', 'reddit_comment': 'reddit', 'youtube': 'youtube', 'youtube_comment': 'youtube',
    'x': 'x', 'xai_x_search': 'x', 'tiktok': 'tiktok', 'instagram': 'instagram', 'threads': 'threads', 'facebook': 'facebook',
    'bluesky': 'bluesky', 'hn': 'hackernews', 'stackexchange': 'stackexchange', 'producthunt': 'producthunt',
    'producthunt_comment': 'producthunt', 'quora': 'quora', 'forum': 'forum', 'github': 'github',
    'v2ex': 'v2ex', 'zhihu': 'zhihu', 'weibo': 'weibo', 'douban': 'douban', 'tieba': 'tieba',
    'xiaohongshu': 'xiaohongshu', 'bilibili': 'bilibili', 'bilibili_comment': 'bilibili',
}
CREATOR_POST_SOURCES = {'youtube', 'tiktok', 'instagram', 'bilibili', 'xiaohongshu'}
SUPPLIER_ENTITY = re.compile(r'supplier|maker|founder|vendor|company_owner|page_owner', re.I)
PRO_MARK = re.compile(r'\b(advisor|adviser|broker|lawyer|accountant|consultant|professional|berater|makler)\b', re.I)
METRICS = ('upvotes', 'likes', 'comments', 'views')

STOP = set('''
a about above after again all also am an and any are as at be because been before being below between both but by can could did do does doing
down during each few for from further had has have having he her here hers him his how i if in into is it its just me more most my no nor not
now of off on once only or other our out over own same she should so some such than that the their them then there these they this those
through to too under until up very was we were what when where which while who whom why will with would you your yours really also get got
would could dont cant wont im ive thats theres isnt arent wasnt doesnt didnt like one even much many still maybe
aber alle als also am an auch auf aus bei bin bis bist da damit dann das dass dein der den des die dies diese dir doch dort du durch ein eine
einem einen einer eines er es euch für hab habe haben hat hatte hier ich ihr ihre im in ist ja kann kein keine man mein mich mir mit nach nicht
noch nur oder ohne sehr sein seit sich sie sind so über um und uns von vor war was weil wenn wer wie wir wird wo zu zum zur
wieder selbst alles dich danke nichts halt denn deutlich sondern bekommen dir dein deine keiner jemand sonst bereits schon dazu wohl evtl ggf mal noch
mehr würde wäre wären könnte könnten muss müssen soll sollte sollten wurde wurden werden worden gibt geben geht gehen ganz schon immer mal viel viele wenig habe hast hatten haben bekommt macht machen kannst können kommt gerade eigentlich eben also jetzt jedoch dazu dafür darf dürfen mein meine meinen meiner deine deinen seine seinen ihren ihrer wirklich einfach etwas bzw zb dabei damals heute leider gar
al algo como con cuando de del donde el ella en es esta este esto fue ha hay la las le lo los me mi muy no nos para pero por que se si sin sobre su
también te tu un una uno y ya
'''.split())


def _stem(word: str) -> str:
    return word[:-1] if len(word) > 4 and word.endswith('s') and not word.endswith('ss') else word


def _clean(text: str) -> str:
    text = re.sub(r'https?://\S+', ' ', text)
    return text.replace('#', ' ').replace('@', ' ')


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r'(?<=[.!?¿¡])\s+|\n+', _clean(text)) if s.strip()]


def _tokens(sentence: str) -> list[str]:
    return [t for t in re.findall(r"[^\W\d_]+(?:'[^\W\d_]+)?", sentence.casefold()) if len(t) >= 2]


def _phrases(text: str) -> set[str]:
    found: set[str] = set()
    for sentence in _sentences(text):
        words = [None if (t in STOP or len(t) < 3) else t for t in _tokens(sentence)]
        for a, b in zip(words, words[1:]):
            if a and b:
                found.add(f'{a} {b}')
        found.update(w for w in words if w and len(w) >= 4)
    return found


def _is_int(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def _speaker(r: dict) -> str:
    entity = str(r.get('source_entity_type', '')) + ' ' + str(r.get('author_relationship', ''))
    context = str(r.get('author_context', ''))
    if (r.get('author_voice_status') == 'supplier_context' or r.get('source_role') == 'competitor_context'
            or 'supplier' in entity or (r['source'] == 'producthunt_comment' and re.search(r'maker', context, re.I))):
        return 'suppliers'
    if r.get('source_role') == 'creator_statement' or r['source'] in CREATOR_POST_SOURCES and 'comment' not in entity:
        return 'creators'
    if PRO_MARK.search(context):
        return 'professionals'
    if r.get('source_role') in ('customer_statement', 'customer_review') or r.get('author_voice_status') in ('firsthand_customer', 'former_customer', 'prospective_user', 'nonadopter'):
        return 'customers'
    return 'unattributed'


def _format(r: dict) -> str:
    declared = r.get('content_format') or r.get('format')
    if declared:
        return str(declared)
    text = r['text']
    if re.search(r'\bAMA\b|ask me anything', text, re.I):
        return 'ama'
    if re.search(r'\bvs\.?\b|versus|compared (to|with)|comparison|vergleich', text, re.I):
        return 'comparison'
    if re.search(r'\bmeme\b', text, re.I):
        return 'meme'
    if r['source'] in CREATOR_POST_SOURCES:
        return 'video'
    if r.get('source_url') and re.search(r'/(watch|shorts|video|reel)', r['source_url']):
        return 'video'
    return 'unknown'


def _questions(text: str) -> list[str]:
    out = []
    for s in re.split(r'(?<=[.!?])\s+|\n+', _clean(text)):
        s = ' '.join(s.split())
        if s.endswith('?') and 8 <= len(s) <= 240:
            out.append(s)
    return out


def _snippet(text: str, anchor: str) -> str:
    text = ' '.join(_clean(text).split())
    sentences = _sentences(text) or [text]
    pick = next((s for s in sentences if all(w in s.casefold() for w in anchor.split())), sentences[0])
    pick = ' '.join(pick.split())
    if len(pick) > PHRASE_LEN:
        pick = pick[:PHRASE_LEN - 1].rsplit(' ', 1)[0].rstrip(',;:-') + '…'
        pick = pick[:PHRASE_LEN]
    return pick


def _date(r: dict) -> tuple[str, str]:
    if r.get('published_at'):
        return r['published_at'][:10], 'published_at'
    return (r.get('retrieved_at') or '')[:10], 'retrieved_at'


def _engagement(records: list[dict]) -> dict:
    by_platform: dict[str, list[dict]] = defaultdict(list)
    for r in records:
        by_platform[PLATFORM[r['source']]].append(r)
    out = {}
    for platform, rs in sorted(by_platform.items()):
        entry: dict = {'records': len(rs), 'records_with_engagement': 0}
        for m in METRICS:
            vals = [r['engagement'][m] for r in rs if isinstance(r.get('engagement'), dict) and _is_int(r['engagement'].get(m))]
            if vals:
                entry[m] = {'median': statistics.median(vals), 'top': max(vals), 'n': len(vals)}
        entry['records_with_engagement'] = sum(1 for r in rs if any(_is_int(r.get('engagement', {}).get(m)) for m in METRICS))
        out[platform] = entry
    return out


def _formats(records: list[dict]) -> dict:
    out: dict[str, dict] = {}
    for fmt in sorted({_format(r) for r in records}):
        rs = [r for r in records if _format(r) == fmt]
        per = {}
        for platform in sorted({PLATFORM[r['source']] for r in rs}):
            sub = [r for r in rs if PLATFORM[r['source']] == platform]
            attention = {}
            for m in METRICS:
                vals = [r['engagement'][m] for r in sub if isinstance(r.get('engagement'), dict) and _is_int(r['engagement'].get(m))]
                if vals:
                    attention[m + '_median'] = statistics.median(vals)
            per[platform] = {'records': len(sub), **attention}
        out[fmt] = per
    return out


def _cluster_index(clusters: list[dict] | None) -> list[tuple[str, set[str], list[set[str]]]]:
    index = []
    for c in clusters or []:
        cid = c['cluster_id']
        texts = [cid.replace('-', ' ').replace('_', ' ')] + [q['query'] if isinstance(q, dict) else str(q) for q in c.get('queries', [])]
        index.append((cid, set(), [{_stem(t) for t in _tokens(x)} for x in texts]))
    return index


def _match(anchor: str, index) -> list[str]:
    need = {_stem(w) for w in anchor.split()}
    scored = [(sum(1 for toks in sets if need <= toks), cid) for cid, _, sets in index]
    return [cid for n, cid in sorted(scored, key=lambda x: (-x[0], x[1])) if n]


def _dedupe(records: list[dict], skipped: Counter) -> list[dict]:
    seen, out, first_platform = set(), [], {}
    for r in records:
        if r.get('source') not in PLATFORM:
            skipped['not_a_discussion_source'] += 1
            continue
        if not str(r.get('text', '')).strip():
            skipped['empty_text'] += 1
            continue
        keys = {('id', r['source'], r.get('source_record_id') or r.get('evidence_id') or ''), ('text', ' '.join(r['text'].casefold().split()))}
        if r.get('source_record_id') is None and r.get('evidence_id') is None:
            keys = {k for k in keys if k[0] == 'text'}
        if keys & seen:
            skipped['duplicate'] += 1
            if PLATFORM[r['source']] != PLATFORM[first_platform.get(next(iter(keys & seen)), r['source'])]:
                skipped['duplicate_across_platforms'] += 1
            continue
        seen |= keys
        for k in keys:
            first_platform.setdefault(k, r['source'])
        out.append(r)
    return out


def build_social_topics(records: list[dict], clusters: list[dict] | None, *, source_ref: dict | None = None) -> dict:
    skipped: Counter = Counter()
    recs = _dedupe([dict(r) for r in records], skipped)
    for i, r in enumerate(recs):
        r.setdefault('evidence_id', f'rec-{i}-' + hashlib.sha256(r['text'].encode()).hexdigest()[:8])
    feats = [_phrases(r['text']) for r in recs]
    df = Counter(p for f in feats for p in f)
    cap = MAX_DF_SHARE * len(recs) if len(recs) >= 20 else float('inf')
    anchors = sorted((p for p, n in df.items() if MIN_RECORDS <= n <= cap), key=lambda p: (' ' not in p, -df[p], p))
    assigned: dict[int, str] = {}
    members: dict[str, list[int]] = {}
    for anchor in anchors:
        free = [i for i, f in enumerate(feats) if i not in assigned and anchor in f]
        if len(free) >= MIN_RECORDS:
            members[anchor] = free
            assigned.update({i: anchor for i in free})
    index = _cluster_index(clusters)
    ref = source_ref or {'path': 'records', 'sha256': hashlib.sha256(json.dumps([r['evidence_id'] for r in recs]).encode()).hexdigest()}
    rows = []
    ordered = sorted(members.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    for anchor, idx in ordered[:MAX_TOPICS]:
        rs = [recs[i] for i in idx]
        platforms = Counter(PLATFORM[r['source']] for r in rs)
        mix = Counter(_speaker(r) for r in rs)
        qs = Counter(q for r in rs for q in dict.fromkeys(_questions(r['text'])))
        dates = [_date(r) for r in rs if _date(r)[0]]
        cids = _match(anchor, index)
        supplier_only = set(mix) == {'suppliers'}
        voices = sorted(rs, key=lambda r: (_speaker(r) in ('suppliers', 'creators'), r['evidence_id']))
        phrases, used = [], set()
        for r in voices:
            snip = _snippet(r['text'], anchor)
            if snip and snip not in used and len(phrases) < MAX_PHRASES:
                used.add(snip)
                phrases.append({'text': snip, 'record_id': r['evidence_id'], 'speaker': _speaker(r)})
        label = ('Supplier-only discussion (suppliers/makers talking about themselves; not customer voice). ' if supplier_only else '') \
            + ('Single platform. ' if len(platforms) == 1 else '') \
            + ('Matches a search-study cluster.' if cids else 'No search-study cluster: candidate to check in search, not a content gap.')
        rows.append({
            'topic': anchor, 'topic_id': 'st-' + hashlib.sha256(anchor.encode()).hexdigest()[:8],
            'cluster_id': cids[0] if cids else None, 'cluster_ids': cids,
            'search_check': 'matched_search_cluster' if cids else 'candidate_to_check_in_search',
            'questions': [q for q, _ in sorted(qs.items(), key=lambda kv: (-kv[1], kv[0]))[:MAX_QUESTIONS]],
            'refs': [ref], 'record_count': len(rs), 'record_ids': sorted(r['evidence_id'] for r in rs),
            'platforms': sorted(platforms), 'platform_counts': dict(sorted(platforms.items())),
            'speaker_mix': dict(sorted(mix.items())), 'supplier_only': supplier_only, 'single_platform': len(platforms) == 1,
            'phrases': phrases, 'engagement': _engagement(rs), 'formats': _formats(rs),
            'first_seen': min(d for d, _ in dates) if dates else None, 'last_seen': max(d for d, _ in dates) if dates else None,
            'date_basis': sorted({b for _, b in dates}), 'label': label.strip(),
            'anchor_kind': 'bigram' if ' ' in anchor else 'word',
            'grouping_basis': f"{len(rs)} records share the {'two-word phrase' if ' ' in anchor else 'single word'} '{anchor}' (surface match, no semantics)",
            'needs_review': ' ' not in anchor or len(rs) < NEEDS_REVIEW_BELOW or supplier_only,
        })
    return {
        'schema_version': 1,
        'generated_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'method': {
            'grouping': 'shared key phrases (bigrams then single words), greedy, one topic per record',
            'min_records': MIN_RECORDS, 'max_phrase_share_when_20plus_records': MAX_DF_SHARE, 'max_topics': MAX_TOPICS,
            'cluster_match': 'every word of the topic phrase appears in a search cluster query or id',
            'note': 'Engagement measures attention, not need or demand, and is never compared or summed across platforms. '
                    'Creator and supplier posts are kept apart from customer posts (speaker_mix). Single-platform topics are flagged. '
                    'Topics with no search-study cluster are candidates to check in search, not content gaps. '
                    'Grouping is surface-phrase based: no German stemming or compound splitting (kind/kinder are separate), partial de/en/es stopword lists, no paraphrase. '
                    'Topics with needs_review true (single-word anchor, under 5 records or supplier-only) do not count as a keyword-map input.',
        },
        'records_considered': len(recs), 'records_assigned': len(assigned), 'records_unassigned': len(recs) - len(assigned),
        'records_skipped': dict(skipped), 'topics_dropped': max(0, len(ordered) - MAX_TOPICS), 'rows': rows,
    }


def render(doc: dict) -> str:
    out = ['# Social discussion topics', '', f"Records: {doc['records_considered']} considered, {doc['records_assigned']} in topics, "
           f"{doc['records_unassigned']} unassigned; skipped: {doc['records_skipped'] or 'none'}.", '']
    for r in doc['rows']:
        out += [f"## {r['topic']} ({r['record_count']} records)", '', f"- {r['label']}",
                f"- Platforms: {', '.join(f'{p} {n}' for p, n in r['platform_counts'].items())}",
                f"- Speakers: {', '.join(f'{k} {v:g}' for k, v in r['speaker_mix'].items())}",
                f"- Seen: {r['first_seen']} to {r['last_seen']}",
                f"- Search clusters: {', '.join(r['cluster_ids']) or 'none'}"]
        for p, e in r['engagement'].items():
            bits = [f"{m} median {e[m]['median']:g} / top {e[m]['top']}" for m in METRICS if m in e]
            out.append(f"- Attention on {p} (platform-specific, not comparable): {'; '.join(bits) or 'none recorded'}")
        out.append('- Formats: ' + ', '.join(f"{f} ({sum(v['records'] for v in per.values())})" for f, per in r['formats'].items()))
        if r['questions']:
            out += ['- Recurring questions:'] + [f'  - {q}' for q in r['questions']]
        if r['phrases']:
            out += ['- Language people use:'] + [f"  - \"{p['text']}\" ({p['speaker']}, {p['record_id']})" for p in r['phrases']]
        out.append('')
    out += ['---', doc['method']['note'], '']
    return '\n'.join(out)


def load_records(path: Path) -> tuple[list[dict], dict]:
    files = sorted(path.rglob('*.jsonl')) if path.is_dir() else [path]
    records, h = [], hashlib.sha256()
    for f in files:
        raw = f.read_bytes()
        h.update(raw)
        text = raw.decode('utf-8')
        if f.suffix == '.json':
            data = json.loads(text)
            records += data if isinstance(data, list) else data.get('records', [])
        else:
            for line in text.splitlines():
                try:
                    records.append(json.loads(line))
                except ValueError:
                    pass
    return [r for r in records if isinstance(r, dict) and 'source' in r], {'path': str(path), 'sha256': h.hexdigest()}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description='Build social-topics.json/.md from evidence records.')
    ap.add_argument('--records', type=Path, required=True, help='evidence jsonl file or directory of them')
    ap.add_argument('--clusters', type=Path, help='content-opportunities.json')
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args(argv)
    records, ref = load_records(a.records)
    clusters = json.loads(a.clusters.read_text())['rows'] if a.clusters else None
    doc = build_social_topics(records, clusters, source_ref=ref)
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / 'social-topics.json').write_text(json.dumps(doc, indent=2, ensure_ascii=False) + '\n')
    (a.out / 'social-topics.md').write_text(render(doc))
    print(f"{len(doc['rows'])} topics from {doc['records_considered']} records -> {a.out}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
