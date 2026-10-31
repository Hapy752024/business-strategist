"""Bounded English aggregate export import. Presets describe exact supported variants."""
from __future__ import annotations
import csv
from datetime import date, datetime
import io
import math
from pathlib import Path
import re
from urllib.parse import urlsplit, urlunsplit
from zoneinfo import ZoneInfo
from scripts.marketing.campaign import ROOT, identifier, read_json, digest, bytes_digest

MAX_BYTES=10*1024*1024
MAX_ROWS=50000
AD_PROVIDERS={'google_ads','meta_ads','tiktok_ads'}
PRIVATE=re.compile(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|\b(?:Bearer\s+\S+|sk-[A-Za-z0-9_-]{12,}|EA[A-Za-z0-9]{40,})',re.I)


def preset(name):
    identifier(name)
    path=ROOT/'config/marketing/export-presets'/ (name+'.json')
    if not path.is_file(): raise ValueError('unknown export preset; see references/marketing-execution.md')
    return read_json(path)


def number(raw):
    raw=str(raw or '').strip()
    if raw.lower() in {'','--','—','n/a','na','not available','suppressed','<10'}:
        return None, 'unavailable' if raw else 'unknown'
    # Explicit English numeric format only. Reject localized or hidden coercions.
    if not re.fullmatch(r'-?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?%?',raw):
        raise ValueError('unsupported numeric format; export English CSV without currency symbols')
    value=float(raw.rstrip('%').replace(',','')) / (100 if raw.endswith('%') else 1)
    if not math.isfinite(value) or value<0: raise ValueError('metrics must be finite nonnegative numbers')
    return value,'available'


def metadata_check(metadata, provider):
    allowed={'property','period_start','period_end','timezone','exported_at','currency','attribution','maturity','report_scope'}
    if set(metadata)-allowed or any(not isinstance(v,str) or len(v)>4000 for v in metadata.values()):
        raise ValueError('export metadata contains unsupported fields or values')
    required={'report_scope','property','period_start','period_end','timezone','exported_at'}
    if provider in AD_PROVIDERS: required|={'currency','attribution','maturity'}
    missing=sorted(k for k in required if not metadata.get(k))
    if missing: raise ValueError('confirm export metadata: '+', '.join(missing))
    start,end=date.fromisoformat(metadata['period_start']),date.fromisoformat(metadata['period_end'])
    if end<start: raise ValueError('export period ends before it starts')
    exported=datetime.fromisoformat(metadata['exported_at'].replace('Z','+00:00')) if 'T' in metadata['exported_at'] else datetime.combine(date.fromisoformat(metadata['exported_at']),datetime.min.time())
    if exported.date()<end: raise ValueError('export date precedes reporting period end')
    ZoneInfo(metadata['timezone'])
    if metadata.get('currency') and not re.fullmatch('[A-Z]{3}',metadata['currency']): raise ValueError('currency must be an uppercase three-letter code')
    if PRIVATE.search(str(metadata)): raise ValueError('metadata appears to contain private data')


def import_export(path, name, metadata):
    spec=preset(name); metadata=dict(metadata); metadata_check(metadata,spec['provider'])
    path=Path(path)
    if path.stat().st_size>MAX_BYTES: raise ValueError('export exceeds 10 MiB limit')
    raw=path.read_bytes()
    if path.suffix.lower()!='.csv': raise ValueError('presets support CSV exports only')
    text=raw.decode('utf-8-sig')
    rows=list(csv.reader(io.StringIO(text)))
    if len(rows)>MAX_ROWS+25: raise ValueError('export exceeds row limit')
    columns=lambda s:s.replace('{currency}',metadata.get('currency',''))
    required={columns(c) for c in spec['required']}
    header_index=next((i for i,r in enumerate(rows[:25]) if required <= set(r)),None)
    if header_index is None: raise ValueError('preset '+name+' requires columns: '+', '.join(sorted(required)))
    if len(rows)-header_index-1>MAX_ROWS: raise ValueError('export exceeds row limit')
    header=rows[header_index]
    if len(header)!=len(set(header)): raise ValueError('duplicate CSV headers')
    observed=[]; seen=set(); discarded=0; private_dropped=0
    for index, row in enumerate(rows[header_index+1:],header_index+2):
        if not row or not any(v.strip() for v in row) or (row[0].startswith('#')): continue
        if len(row)!=len(header): raise ValueError('CSV row '+str(index)+' does not match its header')
        item=dict(zip(header,row)); dimension=item[spec['dimension']].strip()
        if spec['provider'] in AD_PROVIDERS and dimension in {'','--'} and any(v.strip().lower().startswith('total:') for v in row[:2]):
            discarded+=1;continue
        if not dimension: raise ValueError('export row is missing its dimension')
        if PRIVATE.search(dimension) and spec.get('dimension_kind')=='query':
            private_dropped+=1;continue
        if PRIVATE.search(dimension): raise ValueError('dimension may contain private data; use a sanitized aggregate export')
        if spec['provider'] in {'gsc','ga4'} and spec.get('dimension_kind') not in {'query','event'}:
            parts=urlsplit(dimension)
            dimension=urlunsplit((parts.scheme,parts.netloc,parts.path,'',''))
        if len(dimension)>1000 or any(ord(c)<32 for c in dimension): raise ValueError('unsupported aggregate dimension')
        if dimension in seen: raise ValueError('duplicate dimensions; use an export without breakdowns or duplicate totals')
        seen.add(dimension)
        if spec['provider']=='meta_ads':
            for column,key in [('Reporting starts','period_start'),('Reporting ends','period_end')]:
                if column in item and item[column] != metadata[key]: raise ValueError('Meta row period differs from confirmed metadata')
        for metric,definition in spec['metrics'].items():
            value,availability=number(item.get(columns(definition['column'])))
            if definition['unit']!='fraction' and str(item.get(columns(definition['column'])) or '').strip().endswith('%'):
                raise ValueError('unexpected percentage in a non-percentage metric')
            observed.append({'dimension':dimension,'metric':metric,'unit':definition['unit'],'value':value,'availability':availability})
    if not observed: raise ValueError('export contains no usable aggregate rows')
    from scripts.marketing.observations import normalize_rows
    fields=['property','source','period_start','period_end','timezone','metric','unit','value','dimension','availability']
    normalized=normalize_rows(observed,{key:key for key in fields},metadata|{'source':spec['provider']},input_sha256=bytes_digest(raw))
    observed=normalized['observations']
    summary={}
    for metric,definition in spec['metrics'].items():
        cells=[r for r in observed if r['metric']==metric]
        values=[r['value'] for r in cells]
        value=None; reason='one or more values missing or suppressed'
        if all(v is not None for v in values):
            if definition['aggregate']=='sum': value=sum(values)
            elif definition['aggregate']=='non_additive':
                if len(values)==1: value=values[0]
                else: reason='distinct users across pages are not additive'
            elif definition['aggregate']=='weighted':
                weights={r['dimension']:r['value'] for r in observed if r['metric']==definition['weight']}
                if all(weights.get(r['dimension']) is not None for r in cells) and sum(weights.values())>0:
                    value=sum(r['value']*weights[r['dimension']] for r in cells)/sum(weights.values())
                else: reason='missing or zero weighting denominator'
        if value is not None and not math.isfinite(value): raise ValueError('aggregate numeric overflow')
        summary[metric]={'value':value,'unit':definition['unit'],'availability':'available' if value is not None else 'unknown','limitation':None if value is not None else reason}
    for metric,definition in spec['ratios'].items():
        a=summary[definition['numerator']]['value'];b=summary[definition['denominator']]['value']
        value=a/b if a is not None and b is not None and b>0 else None
        summary[metric]={'value':value,'unit':'fraction','availability':'available' if value is not None else 'unknown',
            'limitation':None if value is not None else 'missing or zero denominator'}
    document={'schema_version':2,'provider':spec['provider'],'preset':name,'preset_sha256':digest(spec),
        'transform_version':spec['transform_version'],'input_sha256':bytes_digest(raw),'metadata':metadata,
        'observations':observed,'summary':summary,'excluded_total_rows':discarded,
        'limitations':['Aggregate exports do not establish causal uplift.','Dimensions are limited to the selected export; missing or suppressed data is not zero.']}
    if spec.get('dimension_kind')=='query': document['excluded_private_query_rows']=private_dropped
    document['import_id']=digest(document)
    return document


def compare(before,after):
    if before is None: return {'status':'no_baseline','metrics':{},'reason':'First report; no comparable baseline supplied.'}
    fields=['provider','preset','preset_sha256','transform_version']
    mismatch=any(before.get(k)!=after.get(k) for k in fields)
    context=['property','timezone','currency','attribution','maturity','report_scope']
    mismatch |= any(before['metadata'].get(k)!=after['metadata'].get(k) for k in context)
    duration=lambda d:(date.fromisoformat(d['metadata']['period_end'])-date.fromisoformat(d['metadata']['period_start'])).days
    mismatch |= duration(before)!=duration(after)
    if before['metadata']['period_end']>=after['metadata']['period_start']: mismatch=True
    if mismatch: return {'status':'non_comparable','metrics':{},'reason':'Source, period, account, currency, attribution, maturity, filters or transform differs/overlaps.'}
    metrics={}
    for key,b in after['summary'].items():
        a=before['summary'].get(key,{})
        if a.get('value') is None or b.get('value') is None:
            metrics[key]={'status':'unknown','before':a.get('value'),'after':b.get('value'),'difference':None}
        else:
            difference=b['value']-a['value']
            if not math.isfinite(difference): raise ValueError('comparison numeric overflow')
            metrics[key]={'status':'observed_change','before':a['value'],'after':b['value'],'difference':difference}
    return {'status':'descriptive','metrics':metrics,'causal_attribution':'not_established'}
