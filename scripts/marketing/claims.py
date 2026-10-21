"""Check declared marketing claim markers. Unmarked claims still require editorial review."""
from __future__ import annotations
import argparse
from datetime import date
import re
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from scripts.marketing import campaign as c

MARKER=re.compile(r'\[\[claim:([a-z0-9-]+)\]\]')
NUMBERS=re.compile(r'(?<![A-Za-z])\d+(?:[.,]\d+)?%?')


def registry_errors(registry):
    errors=c.schema_errors('marketing-claims.schema.json',registry)
    if errors:return ['invalid marketing claims registry']
    ids=[claim['id'] for claim in registry['claims']]
    if len(ids)!=len(set(ids)):errors.append('duplicate claim IDs')
    for claim in registry['claims']:
        if date.fromisoformat(claim['expires_at'])<date.fromisoformat(claim['reviewed_at']):errors.append('claim expires before its review')
    return errors


def check(text,registry,today=None):
    errors=registry_errors(registry)
    if errors:return errors
    today=today or date.today(); known={claim['id']:claim for claim in registry['claims']}
    for line in text.splitlines():
        ids=MARKER.findall(line)
        if not ids:continue
        for ident in ids:
            claim=known.get(ident)
            if claim is None:errors.append('unknown declared claim: '+ident);continue
            if not date.fromisoformat(claim['reviewed_at'])<=today<=date.fromisoformat(claim['expires_at']):errors.append('claim review is not current: '+ident)
        permitted={n for ident in ids if ident in known for n in NUMBERS.findall(known[ident]['text'])}
        if set(NUMBERS.findall(MARKER.sub('',line)))-permitted:errors.append('numeric text differs from declared claim registry')
    if '[[claim:' in MARKER.sub('',text):errors.append('malformed claim marker')
    return sorted(set(errors))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--project',required=True);p.add_argument('--campaign',required=True);p.add_argument('--draft',required=True,type=Path);args=p.parse_args()
    try:
        root=c.resolve_project(args.project);c.load(root,args.campaign)
        registry=c.read_json(c.safe(c.marketing(root),f'campaigns/{args.campaign}/approved-claims.json'))
        errors=check(args.draft.read_text(),registry)
        print(c.encoded({'declared_claim_checks':'failed' if errors else 'passed','errors':errors,
            'unmarked_claim_review':'required','publishing_authorized':False}));return 2 if errors else 0
    except (ValueError,OSError,KeyError):
        print(c.encoded({'status':'error','message':'Cannot validate this campaign draft'}));return 2

if __name__=='__main__':raise SystemExit(main())
