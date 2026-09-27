#!/usr/bin/env python3
"""Export validated conditional economics as CSV and optional PNG charts."""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.case_economics import validate
from scripts.evidence_scout.workspace import cases, prepare_research_output


def export(economics: Path, out: Path, *, csv_only=False):
    economics, out = economics.absolute(), out.absolute()
    record = json.loads(economics.read_text())
    validate(record)
    result, inputs = record['results'], record['inputs']
    months = result['cash'].get('months', [])
    if not months:
        raise ValueError('a conditional monthly cash schedule is required')
    if out.exists():
        raise ValueError('choose a fresh output directory')
    if cases.locate(economics) != cases.locate(out):
        raise ValueError('economics and output must share the same project authority')
    plt = None
    if not csv_only:
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
        except ImportError as exc:
            raise ValueError('matplotlib is optional; install it or use --csv-only') from exc
    prepare_research_output(out, input_paths=[economics])
    out.mkdir(parents=True, exist_ok=True)
    (out / 'assumptions.json').write_text(json.dumps(inputs, indent=2) + '\n')
    currency = inputs['currency']
    fixed = inputs['fixed_per_month'] + inputs['owner_cash_per_month']
    with (out / 'monthly.csv').open('w', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(['month', 'currency', 'closing_cash', 'contribution', 'fixed_and_owner_cash'])
        writer.writerows([m['month'], currency, m['closing_cash'], m['contribution'], fixed] for m in months)
    points = []
    for driver, records in result.get('sensitivities', {}).items():
        for scenario in records:
            rows = scenario['results']['cash'].get('months', [])
            points.append([driver, scenario['inputs'][driver], currency, rows[-1]['closing_cash'] if rows else None])
    with (out / 'sensitivities.csv').open('w', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(['driver', 'input_value', 'currency', 'final_closing_cash'])
        writer.writerows(points)
    (out / 'README.md').write_text(
        '# Conditional economics export\n\n'
        f'Source: {economics}\nInput digest: {record["input_digest"]}\nCurrency: {currency}\n\n'
        'Exact supplied inputs are in assumptions.json; not demand evidence or a forecast.\n'
        + ('Sensitivity points supplied; missing cash outcomes remain blank.\n' if points else 'Sensitivity ranges not supplied; no tornado inferred.\n'))
    if plt is not None:
        x = [m['month'] for m in months]
        for name, series in [('cash', {'Closing cash': [m['closing_cash'] for m in months]}),
                             ('contribution', {'Contribution': [m['contribution'] for m in months],
                                               'Fixed and owner cash': [fixed] * len(months)})]:
            fig, ax = plt.subplots()
            for label, values in series.items():
                ax.plot(x, values, marker='o', label=label)
            ax.axhline(0, color='gray', linewidth=.5)
            ax.set(xlabel='Month', ylabel=currency, title='Conditional ' + name)
            ax.legend(); fig.tight_layout(); fig.savefig(out / (name + '.png')); plt.close(fig)
        ranges = []
        for driver in result.get('sensitivities', {}):
            values = [p[3] for p in points if p[0] == driver and p[3] is not None]
            if values:
                ranges.append((driver, min(values), max(values)))
        if ranges:
            fig, ax = plt.subplots()
            for i, (driver, low, high) in enumerate(ranges):
                ax.plot([low, high], [i, i], marker='o', linewidth=8)
            ax.set_yticks(range(len(ranges)), [r[0] for r in ranges])
            ax.axvline(months[-1]['closing_cash'], color='gray', linestyle='--', label='Base case')
            ax.set(xlabel=f'Final closing cash ({currency})', title='Supplied sensitivity ranges')
            ax.legend(); fig.tight_layout(); fig.savefig(out / 'sensitivities.png'); plt.close(fig)
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--economics', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--csv-only', action='store_true')
    args = parser.parse_args()
    try:
        print(export(args.economics, args.out, csv_only=args.csv_only))
    except (ValueError, OSError) as exc:
        parser.exit(1, f'error: {exc}\n')


if __name__ == '__main__':
    main()
