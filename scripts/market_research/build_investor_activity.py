"""Render a dated VC overview with separately checked primary-source examples."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.business_plan_render import table
from scripts.market_research.scan_vc_topics import investor_identity


def checked_examples(reviews, base):
    seen, rows = set(), []
    for row in reviews:
        ident = row['round_id']
        if ident in seen:
            raise ValueError('Primary review round IDs must be unique')
        seen.add(ident)
        if row.get('status') != 'accepted':
            continue
        if row.get('source_role') not in {'company_announcement', 'fund_announcement', 'filing'}:
            raise ValueError('Material round examples require a primary source')
        path = (base / row['capture_path']).resolve()
        if not path.is_relative_to(base.resolve()) or not path.is_file():
            raise ValueError('Primary-source capture is missing or outside its review packet')
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != row['sha256'] or row['supporting_passage'] not in raw.decode():
            raise ValueError('Primary-source capture or passage changed')
        if not all(row.get(field) for field in ('source_url', 'source_date', 'reviewer', 'rationale')):
            raise ValueError('Primary review requires URL, date, reviewer and rationale')
        if not row['source_url'].startswith('https://'):
            raise ValueError('Primary review requires an HTTPS source URL')
        rows.append(row)
    return rows


def render(scan, examples):
    lines = ['# Venture-capital activity overview', '', 'Market as of: ' + scan['as_of_date_utc'],
             'Captured: ' + scan['collected_at'], '',
             'Geography: ' + str(scan['query_scope'].get('country') or 'Provider global sample'), '',
             'This overview describes observed capital allocation. Company outcomes and local customer evidence require separate investigation.', '',
             table(['Topic', 'Current rounds', 'Previous rounds', 'Change', 'Current disclosed USD', 'Coverage'], [
                 (row['industry_tag'], row['current_rounds'], row['previous_rounds'],
                  'Unresolved' if row['round_count_change_fraction'] is None else str(round(row['round_count_change_fraction'] * 100, 1)) + '%',
                  row['current_disclosed_amount_sum_usd_sample'], 'Lower bounds / unresolved identities' if row['sample_capped'] else 'Complete within queried provider sample')
                 for row in scan['topics']]), '',
             'Topic categories may overlap. Do not add these rows into a global funding total.', '']
    for topic in scan['topics']:
        current = topic['periods']['current']
        lines += ['## ' + topic['industry_tag'], '',
                  'Activity: ' + topic['activity_hint'] + '. Disclosure coverage: ' + str(current['amount_disclosure_count']) + '/' + str(topic['current_rounds']) + ' rounds.', '',
                  'Stage labels: ' + json.dumps(current['stage_counts'], ensure_ascii=False) + '.', '',
                  'Largest round share of disclosed sample: ' + str(current['largest_round_share_of_disclosed_sample']) + '.', '',
                  table(['Company', 'Provider round ID', 'Stage', 'USD amount', 'Market date', 'Detected'], [
                      ((row.get('subject') or {}).get('name') or 'Unknown', (row.get('object') or {}).get('id'),
                       row.get('series') or row.get('label'), row.get('amount'), row.get('occurredAt'), row.get('detectedAt'))
                      for row in current['rounds']]), '']
        investor_rows = [row for query in current['queries'] for page in query.get('pages', [])
                         if page['type'] == 'investor.joined_round' for row in page['signals']]
        names = sorted({(investor_identity(row) or {}).get('name') or 'Unresolved investor identity'
                        for row in investor_rows})
        lines += ['Observed investor names: ' + ', '.join(names or ['Unresolved']) + '.', '',
                  'Case implications to review: category attention, financing stage/model fit, funded competition, comparable customer outcomes and transfer conditions.', '']
    lines += ['## Verified primary-source examples', '']
    if not examples:
        lines += ['Primary verification is pending. Provider examples remain attributed to Parsers VC.', '']
    for row in examples:
        lines += ['- Round `' + row['round_id'] + '`: [' + row['source_role'] + '](' + row['source_url'] + ') — source dated ' + row['source_date'] + '. ' + row['rationale']]
    lines += ['', '## Coverage and limits', '', *['- ' + limit for limit in scan['evidence_limits']],
              '- Stop reason: ' + str(scan.get('stop_reason') or 'None; individual page caps remain visible.'),
              '', '## Next research', '',
              'Investigate paying customers, repeat use, economics, failures and failed expansions for relevant companies. Compare those observations with the target customer market before recommending a business or financing strategy.', '']
    return '\n'.join(lines)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--scan', type=Path, required=True)
    p.add_argument('--reviews', type=Path)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    if args.out.exists():
        p.error('--out must be a fresh directory')
    try:
        scan = json.loads(args.scan.read_text())
        examples = checked_examples(json.loads(args.reviews.read_text()), args.reviews.parent) if args.reviews else []
        known = {(row.get('object') or {}).get('id') for topic in scan['topics'] for period in topic['periods'].values() for row in period['rounds']}
        if any(row['round_id'] not in known for row in examples):
            raise ValueError('Primary example does not belong to this scan')
        body = render(scan, examples)
    except (ValueError, KeyError) as exc:
        p.exit(2, str(exc) + '\n')
    args.out.mkdir(parents=True)
    for index, row in enumerate(examples):
        source = args.reviews.parent / row['capture_path']
        destination = args.out / 'primary-captures' / (str(index) + source.suffix)
        destination.parent.mkdir(exist_ok=True)
        destination.write_bytes(source.read_bytes())
        row['capture_path'] = str(destination.relative_to(args.out))
    (args.out / 'overview.md').write_text(body)
    (args.out / 'scan.json').write_bytes(args.scan.read_bytes())
    (args.out / 'overview.json').write_text(json.dumps({'scan_sha256': hashlib.sha256(args.scan.read_bytes()).hexdigest(),
        'overview_sha256': hashlib.sha256(body.encode()).hexdigest(), 'verification_status': 'examples_reviewed' if examples else 'pending',
        'reviewed_examples': examples}, indent=2))
    print(json.dumps({'output': str(args.out), 'verified_examples': len(examples)}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
