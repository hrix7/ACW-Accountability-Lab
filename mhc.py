"""Exploratory human-control assessment. No legal or empirical certification."""
import argparse
import json
import math
from pathlib import Path

DIMENSIONS = ('understand', 'predict', 'override', 'time', 'audit')
DEFAULT_WEIGHTS = dict(zip(DIMENSIONS, (.25, .25, .30, .10, .10)))


def unit(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError('Expected a finite number between 0 and 1')
    return value


def vector(values):
    if set(values) != set(DIMENSIONS):
        raise ValueError('Exactly five named dimensions are required')
    return {key: unit(values[key]) for key in DIMENSIONS}


def weights(values):
    values = vector(values)
    if not math.isclose(sum(values.values()), 1, abs_tol=1e-9, rel_tol=0):
        raise ValueError('Weights must sum to 1')
    return values


def score(values, weighting=None):
    values = vector(values)
    weighting = weights(DEFAULT_WEIGHTS if weighting is None else weighting)
    return sum(values[key] * weighting[key] for key in DIMENSIONS)


def formula_threshold(civilian_probability, ratio=15):
    unit(civilian_probability)
    if isinstance(ratio, bool) or not isinstance(ratio, (int, float)) or not math.isfinite(ratio) or ratio < 1:
        raise ValueError('Ratio must be finite and at least 1')
    return 1 - civilian_probability / ratio


def sensitivity(values):
    values = vector(values)
    rows = []
    for override in (.15, .20, .25, .30, .35, .40, .45):
        weighting = {key: value * (1-override)/.70 for key, value in DEFAULT_WEIGHTS.items()}
        weighting['override'] = override
        rows.append({'override_weight': override, 'mhc': score(values, weighting)})
    return rows


def assess(case, threshold):
    unit(threshold)
    values = case['scores']
    if set(values) != set(DIMENSIONS):
        raise ValueError('Exactly five named dimensions are required')
    for value in values.values():
        if value is not None:
            unit(value)
    missing = [key for key, value in values.items() if value is None]
    base = {'id': case['id'], 'status': 'insufficient_evidence' if missing else 'scored', 'missing': missing}
    if missing:
        return base
    result = score(values)
    return {**base, 'mhc': result, 'threshold': threshold,
            'comparison': 'at_or_above_design_threshold' if result >= threshold else 'below_design_threshold',
            'simplex_score_range': [min(values.values()), max(values.values())],
            'override_sweep': sensitivity(values)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=Path(__file__).parent/'data/synthetic_cases.json')
    parser.add_argument('--threshold', type=float, default=.87, help='Illustrative design setting, not a legal standard')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        cases = json.loads(args.input.read_text())
        report = {'model_version': '0.1.0', 'notice': 'Synthetic demonstration; unvalidated design threshold. No legal conclusions.',
                  'results': [assess(case, args.threshold) for case in cases]}
        output = json.dumps(report, indent=2, allow_nan=False) + '\n'
        if args.output:
            args.output.write_text(output)
        else:
            print(output, end='')
    except (ValueError, KeyError, TypeError, OSError) as error:
        parser.error(str(error))


if __name__ == '__main__':
    main()
