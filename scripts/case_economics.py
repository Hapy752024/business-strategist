"""Bounded case arithmetic, with explicit unknowns; no market forecasts or eval()."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from decimal import Decimal
from pathlib import Path

INPUT_KEYS = set('model unit currency period revenue_basis acquisition_basis revenue_per_unit service_per_unit partner_per_unit refund_per_unit acquisition_per_new_customer fixed_per_month owner_cash_per_month capacity_per_month provenance lead_to_customer acquisition_in_service_cost horizon_months opening_cash startup_cash_cost receipt_lag_months service_payment_lag_months acquisition_payment_lag_months sales_per_month new_customers_per_month opening_customers monthly_retention new_customer_billing owner_cash_in_service_cost imputed_owner_labor_per_month scenario_limit_reason sensitivity_limit_reason scenarios sensitivities'.split())


def input_digest(inputs):
    return hashlib.sha256(json.dumps(inputs, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def number(inputs, name, missing, *, maximum=None):
    value = inputs.get(name)
    if value is None:
        missing.append(name)
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        raise ValueError(name + ' must be a finite nonnegative number or null')
    if maximum is not None and value > maximum:
        raise ValueError(name + ' is out of range')
    return value


def _calculate_base(inputs):
    if not isinstance(inputs, dict):
        raise ValueError('economics inputs must be an object')
    if set(inputs) - INPUT_KEYS:
        raise ValueError('unsupported economics inputs: ' + ', '.join(sorted(set(inputs) - INPUT_KEYS)))
    for key in ('acquisition_in_service_cost', 'owner_cash_in_service_cost'):
        if key in inputs and type(inputs[key]) is not bool:
            raise ValueError(key + ' must be boolean')
    if inputs.get('model') not in {'transactional', 'recurring'}:
        raise ValueError('supported models: transactional, recurring')
    if inputs.get('period') != 'month' or not isinstance(inputs.get('currency'), str) or len(inputs['currency']) != 3:
        raise ValueError('explicit monthly period and three-letter currency required')
    if inputs.get('revenue_basis') != 'venture_receipt':
        raise ValueError('revenue must exclude pass-through customer spend')
    if not isinstance(inputs.get('unit'), str) or not inputs['unit'].strip():
        raise ValueError('unit must explicitly define the completed sale or served customer')
    statuses = inputs.get('provenance', {})
    if not isinstance(statuses, dict):
        raise ValueError('provenance must be an object')
    for key, entry in statuses.items():
        if not isinstance(entry, dict) or entry.get('status') not in {'evidence_backed', 'assumption', 'unresolved', 'user_confirmed'}:
            raise ValueError('invalid input provenance: ' + key)
        if entry['status'] == 'evidence_backed' and (not isinstance(entry.get('source_refs'), list) or not entry['source_refs'] or any(not isinstance(ref, str) or not ref.strip() for ref in entry['source_refs'])):
            raise ValueError('evidence-backed input needs source references: ' + key)
        if entry['status'] == 'unresolved' and inputs.get(key) is not None:
            raise ValueError('unresolved input must be null: ' + key)
    missing = []
    vals = {k: number(inputs, k, missing) for k in ('revenue_per_unit', 'service_per_unit', 'partner_per_unit',
             'refund_per_unit', 'acquisition_per_new_customer', 'fixed_per_month', 'owner_cash_per_month', 'capacity_per_month')}
    vals = {k: Decimal(str(v)) if v is not None else None for k, v in vals.items()}
    if inputs.get('acquisition_basis') == 'lead':
        conversion = number(inputs, 'lead_to_customer', missing, maximum=1)
        if conversion == 0:
            missing.append('positive_lead_to_customer')
        if conversion and vals['acquisition_per_new_customer'] is not None:
            vals['acquisition_per_new_customer'] /= Decimal(str(conversion))
    elif inputs.get('acquisition_basis') != 'customer':
        raise ValueError('acquisition_basis must be lead or customer')
    if inputs.get('acquisition_in_service_cost') and vals['acquisition_per_new_customer']:
        raise ValueError('acquisition labor/cost counted twice')
    if inputs.get('owner_cash_in_service_cost') and vals['owner_cash_per_month']:
        raise ValueError('owner cash counted twice; owner_cash_per_month is additional cash only')
    labor_missing = []
    labor = number(inputs, 'imputed_owner_labor_per_month', labor_missing)
    labor = Decimal(str(labor)) if labor is not None else None
    assumptions = [k for k in vals if statuses.get(k, {}).get('status', 'assumption') == 'assumption']
    result = {'status': 'unresolved' if missing else 'conditional', 'unresolved_inputs': missing,
              'assumption_inputs': assumptions, 'contribution_per_unit': None, 'required_sales': None,
              'capacity_meets_target': None, 'cash': {'status': 'unresolved'}, 'payback_month': None}
    result['labor_accounting'] = {'owner_cash_basis': 'additional cash, excluding amounts already in service cost',
        'service_allocation_status': 'declared' if 'owner_cash_in_service_cost' in inputs else 'unresolved',
        'imputed_labor_status': 'declared noncash' if labor is not None else 'unresolved'}
    if missing:
        return {'schema_version': '1.0', 'inputs': inputs, 'input_digest': input_digest(inputs), 'results': result}
    unit_margin = vals['revenue_per_unit'] - vals['service_per_unit'] - vals['partner_per_unit'] - vals['refund_per_unit']
    net = unit_margin - vals['acquisition_per_new_customer'] if inputs['model'] == 'transactional' else unit_margin
    result['contribution_per_unit'] = float(round(net, 8))
    if inputs['model'] == 'transactional':
        if net > 0:
            volume = math.ceil((vals['fixed_per_month'] + vals['owner_cash_per_month']) / net)
            result.update(required_sales=volume, capacity_meets_target=volume <= vals['capacity_per_month'])
        else:
            result['capacity_meets_target'] = False
            result['status'] = 'nonpositive_contribution'
    horizon = inputs.get('horizon_months')
    if horizon is None:
        result['cash']['reason'] = 'horizon_months required'
    elif type(horizon) is not int or not 1 <= horizon <= 60:
        raise ValueError('horizon_months must be 1..60')
    else:
        cash_missing = []
        opening = number(inputs, 'opening_cash', cash_missing)
        startup = number(inputs, 'startup_cash_cost', cash_missing)
        lags = {}
        for name in ('receipt_lag_months', 'service_payment_lag_months', 'acquisition_payment_lag_months'):
            value = inputs.get(name)
            if type(value) is not int or not 0 <= value <= 60:
                cash_missing.append(name)
            else:
                lags[name] = value
        monthly = inputs.get('sales_per_month' if inputs['model'] == 'transactional' else 'new_customers_per_month')
        if not isinstance(monthly, list) or len(monthly) != horizon:
            cash_missing.append('monthly_sales_or_customers')
        elif any(type(v) is not int or v < 0 for v in monthly):
            raise ValueError('monthly new sales/customers must be nonnegative integers')
        retained, active = 1, 0
        if inputs['model'] == 'recurring':
            active = number(inputs, 'opening_customers', cash_missing)
            retained = number(inputs, 'monthly_retention', cash_missing, maximum=1)
            if inputs.get('new_customer_billing') not in {'immediate', 'next_month'}:
                cash_missing.append('new_customer_billing')
        if cash_missing:
            result['cash'] = {'status': 'unresolved', 'missing': cash_missing}
        else:
            # The same receipts/payments engine serves both models. Accrual revenue
            # is recorded separately; receipts beyond horizon are not lost.
            receipts, payments = [Decimal(0)] * (horizon + 61), [Decimal(0)] * (horizon + 61)
            opening, startup = Decimal(str(opening)), Decimal(str(startup))
            retained, active = Decimal(str(retained)), Decimal(str(active))
            revenue, workloads, contributions = [], [], []
            for month, new in enumerate(monthly):
                if inputs['model'] == 'transactional':
                    units = new
                else:
                    retained_active = active * retained
                    units = retained_active + (new if inputs['new_customer_billing'] == 'immediate' else 0)
                    active = retained_active + new
                workloads.append(active if inputs['model'] == 'recurring' else units)
                earned = units * vals['revenue_per_unit']
                revenue.append(earned)
                receipts[month + lags['receipt_lag_months']] += earned
                # Service begins on acquisition even when billing starts later.
                service_units = active if inputs['model'] == 'recurring' else units
                contributions.append(earned - service_units * vals['service_per_unit']
                    - units * (vals['partner_per_unit'] + vals['refund_per_unit']) - new * vals['acquisition_per_new_customer'])
                payments[month + lags['service_payment_lag_months']] += service_units * vals['service_per_unit'] + units * (vals['partner_per_unit'] + vals['refund_per_unit'])
                payments[month + lags['acquisition_payment_lag_months']] += new * vals['acquisition_per_new_customer']
                payments[month] += vals['fixed_per_month'] + vals['owner_cash_per_month']
                if month == 0:
                    payments[month] += startup
            rows, cash, sufficient = [], opening, True
            for month in range(horizon):
                cash += receipts[month] - payments[month]
                sufficient = sufficient and cash >= 0
                rows.append({'month': month + 1, 'recognized_revenue': float(round(revenue[month], 2)),
                             'contribution': float(round(contributions[month], 2)),
                             'surplus_after_imputed_labor': float(round(contributions[month] - vals['fixed_per_month'] - vals['owner_cash_per_month'] - labor, 2)) if labor is not None else None,
                             'cash_receipts': float(round(receipts[month], 2)), 'cash_payments': float(round(payments[month], 2)),
                             'closing_cash': float(round(cash, 2)), 'workload': float(workloads[month]),
                             'within_capacity': workloads[month] <= vals['capacity_per_month']})
            result['cash'] = {'status': 'conditional', 'months': rows,
                              'sufficient_within_horizon': sufficient,
                              'receipts_after_horizon': float(sum(receipts[horizon:])), 'payments_after_horizon': float(sum(payments[horizon:]))}
            if inputs['model'] == 'recurring':
                result['capacity_meets_target'] = all(r['within_capacity'] for r in rows)
            result['payback_reason'] = 'No lifetime or mature-cohort payback inferred from a conditional schedule.'
    return {'schema_version': '1.0', 'inputs': inputs, 'input_digest': input_digest(inputs), 'results': result}


def calculate(inputs):
    if not isinstance(inputs, dict):
        raise ValueError('economics inputs must be an object')
    if set(inputs) - INPUT_KEYS:
        raise ValueError('unsupported economics inputs: ' + ', '.join(sorted(set(inputs) - INPUT_KEYS)))
    base = {k: v for k, v in inputs.items() if k not in {'scenarios', 'sensitivities'}}
    record = _calculate_base(base)
    scenarios = inputs.get('scenarios', {})
    if not isinstance(scenarios, dict) or set(scenarios) - {'downside', 'upside'}:
        raise ValueError('optional scenarios are downside and upside input overrides')
    if scenarios:
        record['results']['scenarios'] = {}
        for name, overrides in scenarios.items():
            if not isinstance(overrides, dict) or {'scenarios', 'sensitivities'} & set(overrides):
                raise ValueError('scenario overrides must be bounded input objects')
            scenario = {**base, **overrides}
            provenance = dict(base.get('provenance', {}))
            for key in overrides:
                if key != 'provenance':
                    provenance[key] = {'status': 'assumption'}
            provenance.update(overrides.get('provenance', {}))
            scenario['provenance'] = provenance
            record['results']['scenarios'][name] = _calculate_base(scenario)
    sensitivities = inputs.get('sensitivities', {})
    numeric_keys = {'revenue_per_unit', 'service_per_unit', 'acquisition_per_new_customer', 'lead_to_customer', 'monthly_retention', 'capacity_per_month'}
    if not isinstance(sensitivities, dict) or len(sensitivities) > 3 or set(sensitivities) - numeric_keys:
        raise ValueError('sensitivities must name at most three supported numeric drivers')
    if sensitivities:
        record['results']['sensitivities'] = {}
        for key, values in sensitivities.items():
            if not isinstance(values, list) or not 1 <= len(values) <= 3:
                raise ValueError('sensitivity driver requires one to three explicit values')
            record['results']['sensitivities'][key] = [_calculate_base({**base, key: value,
                'provenance': {**base.get('provenance', {}), key: {'status': 'assumption' if value is not None else 'unresolved'}}}) for value in values]
    record['results']['coverage'] = {
        'downside': {'status': 'conditional' if 'downside' in scenarios else 'unresolved',
                     'reason': '' if 'downside' in scenarios else inputs.get('scenario_limit_reason') or 'Downside assumptions have not been supplied.'},
        'sensitivity': {'status': 'conditional' if sensitivities else 'unresolved',
                     'reason': '' if sensitivities else inputs.get('sensitivity_limit_reason') or 'Decision-changing driver ranges have not been supplied.'}}
    record['inputs'], record['input_digest'] = inputs, input_digest(inputs)
    return record


def validate(record):
    if record != calculate(record.get('inputs')):
        raise ValueError('stale or altered economics results; recalculate before publication')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('inputs', type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(calculate(json.loads(args.inputs.read_text())), indent=2, allow_nan=False))
    except (ValueError, TypeError, KeyError) as exc:
        parser.exit(2, str(exc) + '\n')
