"""Guarded terminal editor for one synthetic ACW rating at a time.

The input file is never modified. Confirmed changes use protected export and
therefore require a new output path. This tool does not validate evidence truth
or numeric scoring conventions.
"""
import argparse
import copy
import json
import math
from pathlib import Path

from case_io import export_cases, load_cases
from mhc import DIMENSIONS
from project import RISK_FIELDS, validate_case


CANCEL = {'cancel', 'quit', 'q'}
CONFIDENCE = ('low', 'medium', 'high', 'unknown')


def parse_value(group, raw):
    raw = raw.strip().lower()
    if raw in ('unknown', 'null'):
        return None
    if group == 'control':
        value = float(raw)
        if not math.isfinite(value) or not 0 <= value <= 1:
            raise ValueError('Control value must be 0..1 or unknown')
        return value
    if group != 'risk':
        raise ValueError('Rating group must be control or risk')
    if raw.startswith('+'):
        raw = raw[1:]
    if not raw.isdigit():
        raise ValueError('Risk value must be an integer 0..3 or unknown')
    value = int(raw)
    if not 0 <= value <= 3:
        raise ValueError('Risk value must be an integer 0..3 or unknown')
    return value


def apply_rating_edit(cases, case_id, group, dimension, raw_value, rationale,
                      confidence):
    """Return a validated deep copy containing one synthetic rating edit."""
    edited = copy.deepcopy(cases)
    matches = [case for case in edited if case['id'] == case_id]
    if len(matches) != 1:
        raise ValueError('Choose exactly one existing case ID')
    case = matches[0]
    if not case['synthetic']:
        raise ValueError('Interactive editing is limited to synthetic cases')
    fields = DIMENSIONS if group == 'control' else RISK_FIELDS if group == 'risk' else ()
    if dimension not in fields:
        raise ValueError(f'Unknown {group or "rating"} dimension')
    rationale = rationale.strip()
    if not rationale:
        raise ValueError('Rationale must be nonempty text')
    if confidence not in CONFIDENCE:
        raise ValueError('Confidence must be low, medium, high, or unknown')
    rating = case[group][dimension]
    rating['value'] = parse_value(group, raw_value)
    rating['rationale'] = rationale
    rating['confidence'] = confidence
    validate_case(case)
    return edited


def edit_interactively(cases, ask=input, tell=print):
    synthetic = [case for case in cases if case['synthetic']]
    if not synthetic:
        raise ValueError('No synthetic cases are available to edit')
    tell('Synthetic cases: ' + ', '.join(case['id'] for case in synthetic))
    case_id = ask("Case ID (or 'cancel'): ").strip()
    if case_id.lower() in CANCEL:
        return None
    if case_id not in {case['id'] for case in synthetic}:
        raise ValueError('Choose a listed synthetic case ID')
    group = ask("Rating group, control or risk (or 'cancel'): ").strip().lower()
    if group in CANCEL:
        return None
    fields = DIMENSIONS if group == 'control' else RISK_FIELDS if group == 'risk' else ()
    if not fields:
        raise ValueError('Rating group must be control or risk')
    tell('Dimensions: ' + ', '.join(fields))
    dimension = ask("Dimension (or 'cancel'): ").strip()
    if dimension.lower() in CANCEL:
        return None
    raw_value = ask("Value, or 'unknown' (or 'cancel'): ").strip()
    if raw_value.lower() in CANCEL:
        return None
    rationale = ask("Rationale (or 'cancel'): ").strip()
    if rationale.lower() in CANCEL:
        return None
    confidence = ask("Confidence: low, medium, high, or unknown (or 'cancel'): ").strip().lower()
    if confidence in CANCEL:
        return None
    edited = apply_rating_edit(cases, case_id, group, dimension, raw_value,
                               rationale, confidence)
    old = next(case for case in cases if case['id'] == case_id)[group][dimension]
    new = next(case for case in edited if case['id'] == case_id)[group][dimension]
    tell('Preview: ' + json.dumps({'case_id': case_id, 'group': group,
                                   'dimension': dimension, 'before': old,
                                   'after': new}, indent=2, ensure_ascii=False))
    confirm = ask("Export this edit? Type 'yes' to confirm: ").strip().lower()
    return edited if confirm == 'yes' else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path,
                        default=Path(__file__).parent / 'data/case_records.json')
    parser.add_argument('--output', type=Path, required=True,
                        help='New JSON file; existing files are never replaced')
    args = parser.parse_args()
    try:
        cases = load_cases(args.input)
        edited = edit_interactively(cases)
        if edited is None:
            print('Cancelled; no file was written.')
            return
        export_cases(edited, args.output)
        print(f'Exported validated synthetic edit to {args.output}.')
    except (ValueError, KeyError, TypeError, AttributeError, OSError) as error:
        parser.error(str(error))


if __name__ == '__main__':
    main()
