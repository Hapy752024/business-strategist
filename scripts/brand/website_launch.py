"""Website launch evidence completeness gate; does not certify evidence truth."""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path

CHECKS = (
    'custom_404', 'meta_title', 'meta_description', 'above_fold_cta',
    'favicon_integration', 'robots', 'https_enforcement', 'sitemap',
    'open_graph', 'image_alt',
    'mobile_breakpoints', 'sticky_mobile_cta', 'loading_states', 'form_errors',
    'spam_protection', 'thank_you', 'privacy_policy', 'terms', 'cookie_consent',
    'analytics', 'contact_address', 'compressed_images', 'seo_geo',
    'broken_links', 'performance', 'browser_tests',
)


def pending() -> dict:
    return {'version': 1, 'commit': '', 'url': '', 'deployment_id': '',
            'checks': {key: {'status': 'pending', 'evidence': ''} for key in CHECKS}}


def errors(assessment, *, commit: str, url: str, deployment_id: str) -> list[str]:
    if not isinstance(assessment, dict):
        return ['launch assessment missing or invalid; initialize and complete launch checks']
    result = []
    if type(assessment.get('version')) is not int or assessment['version'] != 1:
        result.append('unsupported launch assessment version')
    if not re.fullmatch(r'[a-f0-9]{40}', commit) or assessment.get('commit') != commit:
        result.append('launch assessment must match full release commit')
    if not url or assessment.get('url') != url:
        result.append('launch assessment must match tested production URL')
    if not isinstance(deployment_id, str) or not deployment_id.strip() or assessment.get('deployment_id') != deployment_id:
        result.append('launch assessment must match deployment/configuration identifier')
    checks = assessment.get('checks')
    if not isinstance(checks, dict):
        return result + ['launch checks missing or invalid']
    if set(checks) != set(CHECKS):
        result.append('launch checks must contain exactly the canonical check IDs')
    for key in CHECKS:
        row = checks.get(key)
        if not isinstance(row, dict) or row.get('status') not in ({'pass', 'not_requested'} if key == 'analytics' else {'pass'}):
            result.append(f'{key}: requires pass')
        elif not isinstance(row.get('evidence'), str) or not row['evidence'].strip():
            result.append(f'{key}: evidence locator and explanation required')
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--commit', required=True)
    parser.add_argument('--url', required=True)
    parser.add_argument('--deployment-id', required=True)
    args = parser.parse_args()
    try:
        data = json.loads(args.manifest.read_text())
        failures = errors(data.get('launch'), commit=args.commit, url=args.url, deployment_id=args.deployment_id)
    except (OSError, ValueError, AttributeError) as exc:
        failures = [str(exc)]
    print(json.dumps({'status': 'fail' if failures else 'pass', 'boundary': 'evidence completeness only', 'errors': failures}, indent=2))
    return bool(failures)


if __name__ == '__main__':
    raise SystemExit(main())
