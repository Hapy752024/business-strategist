"""Shared readable financial presentation over the existing calculator authority."""
from __future__ import annotations

SECTIONS = ('business', 'customer_market', 'competitive_choice', 'product_revenue', 'acquisition_sales',
            'delivery_team', 'finances', 'milestones_risks', 'funding_legal_ip')


def value(item):
    if item is None:
        return 'Unresolved'
    if isinstance(item, bool):
        return 'Yes' if item else 'No'
    return str(item).replace('|', '\\|').replace('\n', ' ')


def table(headers, rows):
    return '\n'.join(['| ' + ' | '.join(headers) + ' |', '|' + '|'.join('---' for _ in headers) + '|',
                      *['| ' + ' | '.join(value(cell) for cell in row) + ' |' for row in rows]])


def financial_tables(economics):
    if not economics:
        return '## Financial assumptions and scenarios\n\nFinancial inputs are unresolved. Supply costs, prices, capacity and a cash schedule before calculating viability.\n'
    from scripts.case_economics import validate
    validate(economics)
    inputs, results = economics['inputs'], economics['results']
    lines = ['## Financial assumptions and scenarios', '',
             'Conditional arithmetic; this is not a demand forecast. Currency: ' + value(inputs.get('currency')) + '.', '',
             '### Assumptions', '', table(['Input', 'Value', 'Basis'], [
                 (key.replace('_', ' ').title(), inputs.get(key), inputs.get('provenance', {}).get(key, {}).get('status', 'Unresolved provenance'))
                 for key in ('revenue_per_unit', 'service_per_unit', 'acquisition_per_new_customer', 'fixed_per_month',
                             'owner_cash_per_month', 'imputed_owner_labor_per_month', 'capacity_per_month', 'opening_cash', 'startup_cash_cost')]), '',
             '### Unit economics and viability', '', table(['Metric', 'Result'], [
                 (key.replace('_', ' ').title(), results.get(key)) for key in ('contribution_per_unit', 'required_sales', 'capacity_meets_target', 'payback_month')]
                 + [('Viability', results.get('viability', {}).get('status', 'unresolved'))]), '']
    cash = results.get('cash', {})
    if cash.get('months'):
        lines += ['### Cash flow', '', table(['Month', 'Revenue', 'Contribution', 'Receipts', 'Payments', 'Closing cash', 'After imputed labor'], [
            (row['month'], row.get('recognized_revenue'), row.get('contribution'), row.get('cash_receipts'), row.get('cash_payments'),
             row.get('closing_cash'), row.get('surplus_after_imputed_labor')) for row in cash['months']]), '']
    else:
        lines += ['Cash schedule unresolved: ' + value(cash.get('reason') or cash.get('missing')), '']
    scenarios = {'base': economics, **results.get('scenarios', {})}
    lines += ['### Scenarios', '', table(['Scenario', 'Contribution per unit', 'Required sales', 'Viability'], [
        (name, row['results'].get('contribution_per_unit'), row['results'].get('required_sales'), row['results'].get('viability', {}).get('status'))
        for name, row in scenarios.items()]), '']
    if 'downside' not in scenarios:
        lines += ['Downside unresolved: ' + value(inputs.get('scenario_limit_reason') or 'Downside assumptions have not been supplied.'), '']
    sensitivity = results.get('sensitivities', {})
    lines += ['### Sensitivity', '']
    if sensitivity:
        lines += [table(['Driver', 'Value', 'Contribution per unit', 'Required sales', 'Viability'], [
            (driver, row['inputs'].get(driver), row['results'].get('contribution_per_unit'), row['results'].get('required_sales'),
             row['results'].get('viability', {}).get('status')) for driver, rows in sensitivity.items() for row in rows]), '']
    else:
        lines += ['Sensitivity unresolved: ' + value(inputs.get('sensitivity_limit_reason') or 'Decision-changing driver ranges have not been supplied.'), '']
    lines += ['Economics input digest: `' + economics['input_digest'] + '`', '']
    return '\n'.join(lines)
