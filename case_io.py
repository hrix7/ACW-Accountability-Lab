"""Validate and copy ACW case records without replacing existing data."""
import argparse
import json
from pathlib import Path

from project import validate_case
from strict_json import load_json


def validate_cases(cases):
    if not isinstance(cases, list) or not cases:
        raise ValueError('Input must be a nonempty case list')
    for case in cases:
        validate_case(case)
    if len({case['id'] for case in cases}) != len(cases):
        raise ValueError('Case IDs must be unique')
    return cases


def load_cases(path):
    return validate_cases(load_json(path))


def export_cases(cases, path):
    """Validate completely, then create a new file; never replace a path."""
    validate_cases(cases)
    content = json.dumps(cases, indent=2, ensure_ascii=False, allow_nan=False) + '\n'
    with Path(path).open('x', encoding='utf-8') as output:
        output.write(content)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path,
                        help='New JSON file; parent directory must already exist')
    args = parser.parse_args()
    try:
        cases = load_cases(args.input)
        if args.output is not None:
            export_cases(cases, args.output)
        print(f'Validated {len(cases)} case records. Evidence truth and scoring remain unvalidated.')
    except (ValueError, KeyError, TypeError, AttributeError, OSError) as error:
        parser.error(str(error))


if __name__ == '__main__':
    main()
