"""Routing and saved-profile contracts; these do not assess generated image quality."""
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts.route_workflow import route_request

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('prompt,expected', [
    ('use supplied photos as is', 'brand-asset'),
    ('use my photos as AI guidance', 'brand-asset'),
    ('stock photo as inspiration', 'brand-asset'),
    ('inspect reference websites', 'brand-research'),
])
def test_photo_and_reference_routes(prompt, expected):
    assert route_request(prompt)['route_id'] == expected


def test_saved_reference_and_photo_preferences_fit_existing_schema():
    profile = json.loads((ROOT / 'templates/brand/website-preferences.json').read_text())
    validator = Draft202012Validator(json.loads((ROOT / 'schemas/website-preferences.schema.json').read_text()))
    validator.validate(profile)
    profile['choices'].update({
        'reference_sites_status': 'supplied',
        'reference_sites': ['https://example.com'],
        'reference_review': 'design/reference-review.md',
        'supplied_photo_assets': ['photo-direct', 'photo-guidance'],
        'image_asset_manifest': 'assets/image-assets.json',
    })
    profile['provenance']['supplied_photo_assets'] = 'user_stated'
    validator.validate(profile)


def test_shared_image_reference_links_resolve():
    for relative in [
        'brand-designer/references/workflow.md',
        'brand-website-designer-builder/references/reference-sites.md',
    ]:
        source = ROOT / '.agents/skills' / relative
        target = source.parent / '../../brand-asset-producer/references/image-sourcing.md'
        assert target.resolve().is_file()
        assert '../../brand-asset-producer/references/image-sourcing.md' in source.read_text()


def test_explicit_website_scope_keeps_photo_work_in_website_flow():
    packet = route_request('build a website and use attached photos for website', intent='website-build')
    assert packet['route_id'] == 'website-build'
