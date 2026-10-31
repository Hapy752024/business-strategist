import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_voice_stage_is_registered_everywhere():
    for script in ['manage-brand-workspace.py', 'workspace_cli.py']:
        text = (ROOT / '.agents/skills/brand-identity/scripts' / script).read_text()
        assert '"voice"' in text
    schema = json.loads((ROOT / 'schemas/brand-manifest.schema.json').read_text())
    stage = schema['$defs']['stage']
    assert 'enum' not in stage or 'voice' in stage['enum']
    assert 'voice' in (ROOT / '.agents/skills/brand-identity/references/orchestration.md').read_text()
    assert (ROOT / '.agents/skills/brand-identity/references/verbal-identity.md').exists()
    assert 'voice.json' in (ROOT / '.agents/skills/brand-identity/references/export.md').read_text()
