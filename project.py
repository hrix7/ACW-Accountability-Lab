"""Evidence-aware research profiles; all scoring conventions are exploratory."""
import argparse
import html
import json
from pathlib import Path
from mhc import DIMENSIONS, DEFAULT_WEIGHTS, unit, weights, score, sensitivity

RISK_FIELDS = ('autonomy', 'propagation', 'target_selection', 'irreversibility',
               'attribution_difficulty', 'civilian_exposure')

def text_field(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{name} must be nonempty text')
    return value

def validate_case(case):
    if not isinstance(case, dict):
        raise ValueError('Each case must be an object')
    for field in ('id', 'title', 'scope', 'assessed_on'):
        text_field(case.get(field), field)
    from datetime import date
    date.fromisoformat(case['assessed_on'])
    if type(case.get('synthetic')) is not bool:
        raise ValueError('synthetic must be a boolean')
    sources = case.get('sources')
    if not isinstance(sources, list):
        raise ValueError('sources must be a list')
    ids = []
    for source in sources:
        for field in ('id', 'title', 'url', 'locator'):
            text_field(source.get(field), f'source.{field}')
        if not source['url'].startswith(('https://', 'http://')):
            raise ValueError('Source URL must use HTTP(S)')
        ids.append(source['id'])
    if len(set(ids)) != len(ids):
        raise ValueError('Source IDs must be unique')
    for group, fields in (('control', DIMENSIONS), ('risk', RISK_FIELDS)):
        ratings = case.get(group)
        if not isinstance(ratings, dict) or set(ratings) != set(fields):
            raise ValueError(f'{group} requires exactly {fields}')
        for key, rating in ratings.items():
            if not isinstance(rating, dict):
                raise ValueError(f'{key} must be a rating object')
            value = rating.get('value')
            if value is not None:
                if group == 'control':
                    unit(value)
                elif type(value) is not int or not 0 <= value <= 3:
                    raise ValueError(f'{key} requires an integer 0..3 or null')
            text_field(rating.get('rationale'), f'{key}.rationale')
            if rating.get('confidence') not in ('low', 'medium', 'high', 'unknown'):
                raise ValueError(f'{key} has invalid confidence')
            refs = rating.get('source_ids')
            if not isinstance(refs, list) or any(ref not in ids for ref in refs):
                raise ValueError(f'{key} contains invalid source references')
            if not case['synthetic'] and value is not None and not refs:
                raise ValueError(f'{key}: non-synthetic ratings require evidence references')
    return case

def evaluate(case, threshold=None, weighting=None, floors=None):
    validate_case(case)
    weighting = weights(DEFAULT_WEIGHTS if weighting is None else weighting)
    if threshold is not None:
        unit(threshold)
    floors = {} if floors is None else floors
    if not isinstance(floors, dict) or not set(floors) <= set(DIMENSIONS):
        raise ValueError('Unknown control floor')
    for value in floors.values():
        unit(value)
    values = {key: case['control'][key]['value'] for key in DIMENSIONS}
    missing = [key for key, value in values.items() if value is None]
    floor_results = {key: ('unknown' if values[key] is None else
                          'met' if values[key] >= minimum else 'below_floor')
                     for key, minimum in floors.items()}
    result = {
        'id': case['id'], 'title': case['title'], 'synthetic': case['synthetic'],
        'status': 'insufficient_evidence' if missing else 'scored',
        'missing_control': missing, 'weights': weighting, 'threshold': threshold,
        'component_floors': floor_results,
        'risk_profile': {key: case['risk'][key]['value'] for key in RISK_FIELDS},
        'missing_risk': [key for key in RISK_FIELDS if case['risk'][key]['value'] is None],
        'evidence': case,
        'notice': 'Exploratory profile; sources are supplied, not independently verified. No legal or safety certification.'}
    # Bounds describe unknown ratings in [0,1] at the chosen fixed weights.
    lower = sum(weighting[k] * (0 if v is None else v) for k, v in values.items())
    upper = lower + sum(weighting[k] for k in missing)
    result['missing_evidence_bounds'] = [lower, upper]
    if not missing:
        result['control_score'] = score(values, weighting)
        result['comparison'] = ('not_requested' if threshold is None else
            'at_or_above_design_threshold' if result['control_score'] >= threshold else 'below_design_threshold')
        result['simplex_score_range'] = [min(values.values()), max(values.values())]
        # Sweep is explicitly relative to original baseline, not custom weights.
        result['default_baseline_override_sweep'] = sensitivity(values)
    return result

def render_report(report):
    esc = lambda value: html.escape(str(value), quote=True)
    sections = []
    for result in report['results']:
        rows = ''.join(f'<tr><td>{esc(key)}</td><td>{esc(value if value is not None else "Unknown")}</td></tr>'
                       for key, value in result['risk_profile'].items())
        sections.append(f'<section><h2>{esc(result["title"])}</h2>'
            f'<p>{"Synthetic example" if result["synthetic"] else "Evidence supplied; not independently verified"}</p>'
            f'<p>Control score: {esc(result.get("control_score", "Insufficient evidence"))}</p>'
            f'<p>Component checks: {esc(result["component_floors"])}</p>'
            f'<table><tr><th>Risk dimension (0–3)</th><th>Rating</th></tr>{rows}</table>'
            f'<details><summary>Evidence and calculation details</summary><pre>{esc(json.dumps(result, indent=2))}</pre></details></section>')
    return '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ACW Accountability Lab report</title><style>body{font:16px system-ui;background:#131018;color:#f4e9e7;max-width:1000px;margin:40px auto;padding:0 20px}section{border:1px solid #795260;border-radius:12px;padding:24px;margin:20px 0}h1,h2{color:#efb7ca}td,th{text-align:left;padding:8px 20px 8px 0}pre{white-space:pre-wrap;overflow-wrap:anywhere}summary{cursor:pointer;margin-top:20px}</style><h1>ACW Accountability Lab</h1><p>Exploratory research profiles. Ratings and thresholds are unvalidated; risk dimensions are not combined into a probability or compliance verdict.</p>'+''.join(sections)+'</html>'

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=Path(__file__).parent/'data/case_records.json')
    parser.add_argument('--config', type=Path, help='JSON: optional weights, threshold, floors')
    parser.add_argument('--output', type=Path, default=Path('reports/assessment.json'))
    parser.add_argument('--html', type=Path, default=Path('reports/assessment.html'))
    args = parser.parse_args()
    try:
        cases = json.loads(args.input.read_text())
        if not isinstance(cases, list) or not cases:
            raise ValueError('Input must be a nonempty case list')
        config = json.loads(args.config.read_text()) if args.config else {}
        if not isinstance(config, dict) or not set(config) <= {'weights', 'threshold', 'floors'}:
            raise ValueError('Unknown configuration keys')
        results = [evaluate(case, config.get('threshold'), config.get('weights'), config.get('floors')) for case in cases]
        if len({r['id'] for r in results}) != len(results):
            raise ValueError('Case IDs must be unique')
        report = {'model_version': '0.2.0', 'results': results}
        for path, content in ((args.output, json.dumps(report, indent=2, allow_nan=False)+'\n'),
                              (args.html, render_report(report))):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
        print(f'Generated {args.output} and {args.html}')
    except (ValueError, KeyError, TypeError, AttributeError, OSError) as error:
        parser.error(str(error))

if __name__ == '__main__':
    main()
