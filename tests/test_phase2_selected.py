import csv
import json
from pathlib import Path
import pytest
from scripts.chart_case_economics import export
from scripts.case_economics import calculate
from scripts.strategy_review import validate_plan
from test_case_economics import cash_inputs
from test_strategy_review import plan, position


def decision_review():
    return {'premortem': [dict(trigger_category=category, trigger='Observed trigger', transmission='Costs exceed margin',
                              failed_defense='No pricing power', leading_indicator='Renewals fall', probability_basis='Unknown: no comparable base rate')
                         for category in ('demand', 'delivery')],
            'stop_rules': [dict(kpi='pilot conversion', operator='below', threshold=.1, window='Four weeks', action='Pause acquisition', owner='Founder')],
            'precommitments': [dict(bias='Sunk cost', disconfirmation_trigger='Stop threshold reached', action='Pause', verification='Review cohort ledger')]}


def test_commit_review_required_but_position_selection_stays_provisional():
    p = plan(); p['positioning'] = position()
    assert validate_plan(p) == []
    p['verdict'] = 'commit'
    assert any('decision_review' in e for e in validate_plan(p))
    p['decision_review'] = decision_review()
    assert validate_plan(p) == []
    p['decision_review']['stop_rules'][0]['kpi'] = 'invented'
    assert any('unknown KPI' in e for e in validate_plan(p))
    p['decision_review']['premortem'][1]['trigger_category'] = 'Demand '
    assert any('distinct trigger' in e for e in validate_plan(p))
    p['decision_review'] = []
    assert validate_plan(p)


def test_charts_validate_source_and_export_exact_values(tmp_path):
    record = calculate(cash_inputs()); source = tmp_path / 'economics.json'
    source.write_text(json.dumps(record))
    out = export(source, tmp_path / 'charts', csv_only=True)
    rows = list(csv.DictReader((out / 'monthly.csv').open()))
    assert len(rows) == 6
    assert float(rows[0]['closing_cash']) == 0  # 5000 opening - 2000 startup + 20*50 margin - 4000 overhead
    assert rows[0]['currency'] == 'EUR'
    assert json.loads((out / 'assumptions.json').read_text()) == record['inputs']
    assert 'not supplied' in (out / 'README.md').read_text()
    with pytest.raises(ValueError, match='fresh'):
        export(source, out, csv_only=True)
    record['inputs']['fixed_per_month'] += 1; source.write_text(json.dumps(record))
    with pytest.raises(ValueError, match='stale'):
        export(source, tmp_path / 'invalid', csv_only=True)
    assert not (tmp_path / 'invalid').exists()


def test_chart_pngs_and_sensitivity_points(tmp_path):
    pytest.importorskip('matplotlib')
    d = cash_inputs(); d['sensitivities'] = {'revenue_per_unit':[80,120]}
    source = tmp_path / 'economics.json'; source.write_text(json.dumps(calculate(d)))
    out = export(source, tmp_path / 'charts')
    for name in ('cash','contribution','sensitivities'):
        assert (out / (name+'.png')).read_bytes().startswith(b'\x89PNG\r\n\x1a\n')
    points = list(csv.DictReader((out / 'sensitivities.csv').open()))
    assert [float(p['input_value']) for p in points] == [80,120]
    assert [float(p["final_closing_cash"]) for p in points] == [-12000, 0]


def test_csv_export_without_matplotlib_and_png_failure_before_writing(tmp_path, monkeypatch):
    import builtins
    real_import = builtins.__import__
    def without_matplotlib(name, *args, **kwargs):
        if name == 'matplotlib' or name.startswith('matplotlib.'):
            raise ImportError('synthetic unavailable dependency')
        return real_import(name, *args, **kwargs)
    monkeypatch.setattr(builtins, '__import__', without_matplotlib)
    source = tmp_path / 'economics.json'; source.write_text(json.dumps(calculate(cash_inputs())))
    assert (export(source, tmp_path / 'csv', csv_only=True) / 'monthly.csv').is_file()
    with pytest.raises(ValueError, match='--csv-only'):
        export(source, tmp_path / 'png')
    assert not (tmp_path / 'png').exists()


def test_chart_case_exports_bind_source_and_reject_outside_case(tmp_path):
    from scripts import case_workspace as cases
    root = tmp_path / 'project'; cases.initialize(root, 'Synthetic')
    scope = cases.add_case(root, 'a', 'A')
    source = scope / 'economics.json'; source.write_text(json.dumps(calculate(cash_inputs())))
    out = scope / 'market_research/economics/runs/charts'
    export(source, out, csv_only=True)
    bindings = json.loads((out / '.case-context.json').read_text())['source_bindings']
    assert len(bindings) == 1 and bindings[0]['path'] == 'cases/a/economics.json'
    assert bindings[0] == cases.source_binding(root, bindings[0]['path'], locator=bindings[0]['locator'], applicability=bindings[0]['applicability'])
    with pytest.raises(ValueError, match='authority'):
        export(source, tmp_path / 'outside', csv_only=True)
    with pytest.raises(ValueError, match='immutable research runs'):
        export(source, scope / 'charts', csv_only=True)
