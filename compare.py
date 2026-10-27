"""Side-by-side exploratory comparison of ACW case records."""
import argparse
import html
import json
from pathlib import Path

from mhc import DIMENSIONS
from project import RISK_FIELDS, evaluate, validate_case
from strict_json import load_json
from provenance import build_provenance, render_provenance


def build_comparison(cases, config=None):
    """Build an auditable matrix without aggregating ordinal risk ratings."""
    if not isinstance(cases, list) or len(cases) < 2:
        raise ValueError('Comparison requires at least two cases')
    for case in cases:
        validate_case(case)
    if len({case['id'] for case in cases}) != len(cases):
        raise ValueError('Case IDs must be unique')
    config = {} if config is None else config
    if not isinstance(config, dict) or not set(config) <= {'weights', 'threshold', 'floors'}:
        raise ValueError('Unknown configuration keys')
    results = [evaluate(case, config.get('threshold'), config.get('weights'),
                        config.get('floors')) for case in cases]
    control_rows = []
    for dimension in DIMENSIONS:
        values = [case['control'][dimension]['value'] for case in cases]
        baseline = values[0]
        deltas = [None if baseline is None or value is None else value - baseline
                  for value in values]
        control_rows.append({'dimension': dimension, 'values': values,
                             'difference_from_first': deltas})
    risk_rows = [{'dimension': dimension,
                  'values': [case['risk'][dimension]['value'] for case in cases]}
                 for dimension in RISK_FIELDS]
    summaries = []
    for result in results:
        summaries.append({
            'id': result['id'], 'title': result['title'],
            'synthetic': result['synthetic'], 'status': result['status'],
            'control_score': result.get('control_score'),
            'missing_evidence_bounds': result['missing_evidence_bounds'],
            'threshold_comparison': result.get('comparison', 'not_available'),
            'component_floors': result['component_floors'],
            'missing_control': result['missing_control'],
            'missing_risk': result['missing_risk']})
    return {
        'model_version': '0.2.0',
        'provenance': build_provenance(cases, config),
        'notice': ('Exploratory comparison. Sources are supplied, not independently '
                   'verified; weights, floors and thresholds are unvalidated. Risk '
                   'dimensions remain ordinal and are not aggregated.'),
        'cases': summaries,
        'control_dimensions': control_rows,
        'risk_dimensions': risk_rows,
    }


def render_comparison(comparison):
    esc = lambda value: html.escape(str(value), quote=True)
    cases = comparison['cases']
    headings = ''.join(f'<th scope="col">{esc(case["title"])}</th>' for case in cases)

    def value(value):
        return 'Unknown' if value is None else esc(value)

    summary_rows = []
    for label, key in (('Synthetic', 'synthetic'), ('Evidence status', 'status'),
                       ('Control score', 'control_score'),
                       ('Possible score interval', 'missing_evidence_bounds')):
        cells = ''.join(f'<td>{value(case[key])}</td>' for case in cases)
        summary_rows.append(f'<tr><th scope="row">{esc(label)}</th>{cells}</tr>')
    control_rows = []
    for row in comparison['control_dimensions']:
        cells = ''.join(f'<td>{value(item)}</td>' for item in row['values'])
        control_rows.append(f'<tr><th scope="row">{esc(row["dimension"])}</th>{cells}</tr>')
    risk_rows = []
    for row in comparison['risk_dimensions']:
        cells = ''.join(f'<td>{value(item)}</td>' for item in row['values'])
        risk_rows.append(f'<tr><th scope="row">{esc(row["dimension"])}</th>{cells}</tr>')
    return ('<!doctype html><html lang="en"><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>ACW case comparison</title><style>'
            'body{font:16px system-ui;background:#131018;color:#f4e9e7;max-width:1200px;margin:40px auto;padding:0 20px}'
            'h1,h2{color:#efb7ca}table{border-collapse:collapse;width:100%;margin:18px 0 34px;overflow:auto}'
            'th,td{border:1px solid #795260;padding:10px;text-align:left}th{background:#241923}'
            '.notice{border-left:4px solid #efb7ca;padding:10px 14px;background:#241923}</style>'
            '<h1>ACW case comparison</h1><p class="notice">' + esc(comparison['notice']) + '</p>' +
            render_provenance(comparison.get('provenance')) +
            '<h2>Assessment summary</h2><table><thead><tr><th scope="col">Measure</th>' + headings +
            '</tr></thead><tbody>' + ''.join(summary_rows) + '</tbody></table>'
            '<h2>Human-control dimensions (0–1)</h2><table><thead><tr><th scope="col">Dimension</th>' +
            headings + '</tr></thead><tbody>' + ''.join(control_rows) + '</tbody></table>'
            '<h2>Risk profile (ordinal 0–3; not aggregated)</h2><table><thead><tr><th scope="col">Dimension</th>' +
            headings + '</tr></thead><tbody>' + ''.join(risk_rows) + '</tbody></table></html>')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path,
                        default=Path(__file__).parent / 'data/case_records.json')
    parser.add_argument('--config', type=Path)
    parser.add_argument('--output', type=Path, default=Path('reports/comparison.json'))
    parser.add_argument('--html', type=Path, default=Path('reports/comparison.html'))
    args = parser.parse_args()
    try:
        cases = load_json(args.input)
        config = load_json(args.config) if args.config else None
        comparison = build_comparison(cases, config)
        for path, content in ((args.output, json.dumps(comparison, indent=2, allow_nan=False) + '\n'),
                              (args.html, render_comparison(comparison))):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding='utf-8')
        print(f'Generated {args.output} and {args.html}')
    except (ValueError, KeyError, TypeError, AttributeError, OSError) as error:
        parser.error(str(error))


if __name__ == '__main__':
    main()
