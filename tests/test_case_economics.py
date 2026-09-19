import copy
import pytest
from scripts.case_economics import calculate, validate


def inputs():
    return dict(model='transactional', unit='completed sale', currency='EUR', period='month', revenue_basis='venture_receipt',
                acquisition_basis='customer', revenue_per_unit=100, service_per_unit=25, partner_per_unit=10,
                refund_per_unit=0, acquisition_per_new_customer=15, fixed_per_month=1500,
                owner_cash_per_month=2500, capacity_per_month=60)


def test_contribution_is_not_capacity_or_cash_proof():
    result = calculate(inputs())['results']
    assert result['contribution_per_unit'] == 50
    assert result['required_sales'] == 80
    assert result['capacity_meets_target'] is False
    assert result['cash']['status'] == 'unresolved'


def test_unknowns_rounding_and_stale_results():
    d = inputs(); d['fixed_per_month'] = 1501
    record = calculate(d)
    assert record['results']['required_sales'] == 81
    record['inputs']['fixed_per_month'] = 0
    with pytest.raises(ValueError, match='stale'):
        validate(record)
    d['acquisition_per_new_customer'] = None
    assert calculate(d)['results']['status'] == 'unresolved'


def test_cash_delay_despite_positive_margin():
    d = inputs()
    d.update(horizon_months=2, startup_cash_cost=0, opening_cash=1000, sales_per_month=[100, 100], receipt_lag_months=1,
             service_payment_lag_months=0, acquisition_payment_lag_months=0)
    r = calculate(d)['results']
    assert r['contribution_per_unit'] > 0
    assert not r['cash']['sufficient_within_horizon']
    assert r['cash']['months'][0]['recognized_revenue'] == 10000
    assert r['cash']['months'][0]['cash_receipts'] == 0


def test_rejects_pass_through_double_count_and_nonfinite():
    for field, value in [('revenue_basis', 'premium'), ('acquisition_in_service_cost', True), ('revenue_per_unit', float('nan'))]:
        d = inputs(); d[field] = value
        with pytest.raises(ValueError):
            calculate(d)


def test_unknown_startup_cash_and_deferred_service_costs():
    d = inputs()
    d.update(model='recurring', unit='served customer-month', horizon_months=1, opening_cash=0, startup_cash_cost=None,
             new_customers_per_month=[1], opening_customers=0, monthly_retention=1, new_customer_billing='next_month',
             fixed_per_month=0, owner_cash_per_month=0, acquisition_per_new_customer=0, receipt_lag_months=0,
             service_payment_lag_months=0, acquisition_payment_lag_months=0)
    assert calculate(d)['results']['cash']['status'] == 'unresolved'
    d['startup_cash_cost'] = 0
    cash = calculate(d)['results']['cash']
    assert cash['months'][0]['recognized_revenue'] == 0
    assert cash['months'][0]['cash_payments'] == 25
    assert not cash['sufficient_within_horizon']
    d['service_per_unit'] = .004
    assert not calculate(d)['results']['cash']['sufficient_within_horizon']


def test_lead_units_refunds_scenarios_and_nonpositive_margin():
    d = inputs(); d.update(acquisition_basis='lead', lead_to_customer=.5, refund_per_unit=5)
    assert calculate(d)['results']['contribution_per_unit'] == 30
    d['scenarios'] = {'downside': {'lead_to_customer': .25}}
    assert calculate(d)['results']['scenarios']['downside']['results']['status'] == 'nonpositive_contribution'
    d['lead_to_customer'] = None
    assert calculate(d)['results']['status'] == 'unresolved'


@pytest.mark.parametrize('revenue,service,target,expected', [(100.1,100,1,10),(.7,.2,1,2), (100.1,100,1.0001,11)])
def test_decimal_contribution_ceiling(revenue, service, target, expected):
    d=inputs(); d.update(revenue_per_unit=revenue,service_per_unit=service,partner_per_unit=0,
                         acquisition_per_new_customer=0,fixed_per_month=target,owner_cash_per_month=0,capacity_per_month=10)
    assert calculate(d)['results']['required_sales'] == expected
