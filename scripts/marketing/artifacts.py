"""Publication/resume validation for project-bound local marketing artifacts."""
from __future__ import annotations
import json
from pathlib import Path
from scripts.marketing import campaign as c
from scripts.marketing.link_observations import resolve_bytes

NAMES={'campaign.json','connections.json','approved-claims.json','packet.json','review.json','latest-review.json','review-history.json'}


def owns(relative):
    parts=Path(relative).parts
    return relative=='connections.json' or bool(parts and parts[0]=='campaigns' and parts[-1] in NAMES)


def errors(relative,raw,destination,staged=None):
    name=Path(relative).name
    if not owns(relative):return []
    try:
        root=next(p for p in (Path(destination),*Path(destination).parents) if (p/c.cases.PROJECT).is_file())
        doc=json.loads(raw)
        if relative=='connections.json':
            from scripts.marketing.connections import validate
            return validate(doc,root.name)
        parts=Path(relative).parts
        if len(parts)<3 or parts[0]!='campaigns':return ['campaign artifact has an invalid location']
        direct={'campaign.json','approved-claims.json','latest-review.json','review-history.json'}
        if not ((name in direct and len(parts)==3) or
                (name in {'packet.json','review.json'} and len(parts)==6 and parts[2]=='reviews')):
            return ['campaign artifact has an invalid location']
        campaign_id=c.identifier(parts[1])
        if name=='approved-claims.json':
            from scripts.marketing.claims import registry_errors
            return registry_errors(doc)
        if doc.get('project_id')!=root.name or doc.get('campaign_id')!=campaign_id:return ['campaign artifact project/ID mismatch']
        if name=='campaign.json':
            c.require_schema('marketing-campaign.schema.json',doc)
            config=json.loads(resolve_bytes(destination,'connections.json',staged))
            from scripts.marketing.connections import validate
            if validate(config,root.name):return ['campaign connections are invalid']
            if set(doc['connection_ids'])-{entry['id'] for entry in config['connections']}:return ['campaign references unknown connection']
        elif name=='packet.json':
            from scripts.marketing.review_cycle import validate_packet
            validate_packet(doc)
        elif name=='review.json':
            from scripts.marketing.review_cycle import validate_packet,validate_review
            packet=json.loads(resolve_bytes(destination,str(Path(relative).with_name('packet.json')),staged))
            validate_packet(packet);validate_review(packet,doc)
        elif name=='review-history.json':
            from scripts.marketing.review_cycle import validate_history
            validate_history(doc,destination,staged)
        elif name=='latest-review.json':
            target=c.safe(destination,doc['path'])
            if not str(target.relative_to(destination)).startswith('campaigns/'+campaign_id+'/reviews/') or target.name!='review.json':return ['latest review must refer to its own campaign']
            review=json.loads(resolve_bytes(destination,doc['path'],staged))
            if review['packet_id']!=doc['packet_id'] or review['project_id']!=doc['project_id'] or review['campaign_id']!=campaign_id:return ['latest review binding mismatch']
        return []
    except (ValueError,OSError,KeyError,TypeError,StopIteration,AttributeError):
        return ['invalid or unbound local marketing artifact: '+name]
