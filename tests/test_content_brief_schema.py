import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_content_brief_schema_accepts_minimal_brief_and_rejects_missing_kpi():
    import jsonschema
    schema = json.loads((ROOT / 'schemas/content-brief.schema.json').read_text())
    brief = {"brief_id": "CB-001", "platform": "youtube", "format": "video_8min", "pillar": "pain_education",
             "audience_segment": "expats in Germany choosing PKV", "hook": "Three checks before switching",
             "key_message": "Three checks before you switch", "proof": "walkthrough of a real tariff comparison",
             "cta": "Book a 20-minute check", "conversion_bridge": "validation page /pkv-check",
             "kpi": {"name": "qualified calls booked", "target": 5, "window_days": 30},
             "owner": "founder", "evidence_refs": ["pain_points/runs/2026-09-20/evidence.jsonl#E12"],
             "brand_voice_ref": "branding/voice/voice.json", "status": "planned"}
    jsonschema.validate(brief, schema)
    del brief['kpi']
    try:
        jsonschema.validate(brief, schema)
    except jsonschema.ValidationError:
        return
    raise AssertionError('kpi must be required')
