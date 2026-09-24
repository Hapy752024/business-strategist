import hashlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts/monitoring'))
import change_hypothesis as change


def observation(date, value, url):
    snapshot = url + ' ' + str(value)
    return {'observed_at': date, 'url': url, 'snapshot_text': snapshot,
            'sha256': hashlib.sha256(snapshot.encode()).hexdigest(), 'value': value}


def payload():
    return {'schema_version': 1, 'event_type': 'pricing', 'company': 'Synthetic Supplier',
        'before': observation('2026-01-01T00:00:00Z', {'price': 20, 'currency': 'EUR',
            'billing_period': 'month', 'unit': 'seat', 'region': 'DE', 'customer_scope': 'small clinics'}, 'https://example.test/old'),
        'after': observation('2026-02-01T00:00:00Z', {'price': 40, 'currency': 'EUR',
            'billing_period': 'month', 'unit': 'seat', 'region': 'DE', 'customer_scope': 'small clinics'}, 'https://example.test/new'),
        'customer_segment': 'small clinics', 'workflow': 'monthly appointment administration',
        'customer_impact_hypothesis': 'The minimum monthly cost may rise for single-location clinics.',
        'customer_evidence': []}


def test_pricing_change_is_a_hypothesis_until_customer_evidence_exists():
    result = change.build(payload())
    assert result['changed_fields'] == {'price': {'before': 20, 'after': 40}}
    assert result['evidence_status'] == 'not_yet_corroborated'
    assert result['supporting_customer_evidence'] == []
    assert 'do not establish customer exposure' in result['limits'][0]


def test_noncomparable_pricing_period_blocks_claimed_increase():
    data = payload()
    data['after']['value']['billing_period'] = 'year'
    with pytest.raises(ValueError, match='billing_period'):
        change.build(data)


def test_same_observation_window_or_bad_digest_is_rejected():
    data = payload()
    data['after']['observed_at'] = data['before']['observed_at']
    with pytest.raises(ValueError, match='later'):
        change.build(data)
    data = payload()
    data['after']['sha256'] = '0' * 64
    with pytest.raises(ValueError, match='digest'):
        change.build(data)


def test_supplier_claim_is_not_customer_corroboration():
    data = payload()
    text = 'Vendor says customers are leaving because of the price.'
    data['customer_evidence'] = [{'role': 'supplier', 'relation': 'supports', 'observation': text,
        'url': 'https://example.test/claim', 'snapshot_text': text,
        'sha256': hashlib.sha256(text.encode()).hexdigest()}]
    result = change.build(data)
    assert result['evidence_status'] == 'not_yet_corroborated'
    assert len(result['supplier_assertions']) == 1
