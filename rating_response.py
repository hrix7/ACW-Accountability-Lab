"""Read-only structural validation of synthetic practice response records."""
import argparse
from datetime import date
from pathlib import Path
import re

from mhc import DIMENSIONS, unit
from project import RISK_FIELDS
from strict_json import load_json


def exact(obj, keys, label):
    if not isinstance(obj, dict) or set(obj) != set(keys):
        raise ValueError(f'{label}: missing or unexpected fields')


def text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{label}: nonempty text required')


def validate_response(record):
    exact(record, ('schema_version', 'synthetic', 'case_id', 'scope',
                   'dataset_sha256', 'repository_commit', 'reviewer_alias',
                   'assessed_on', 'exposure', 'control', 'risk'), 'response')
    if type(record['schema_version']) is not int or record['schema_version'] != 1:
        raise ValueError('Unsupported response schema')
    if record['synthetic'] is not True:
        raise ValueError('Only explicitly synthetic practice responses are supported')
    for field in ('case_id', 'scope', 'exposure'):
        text(record[field], field)
    for field, size in (('dataset_sha256', 64), ('repository_commit', 40)):
        if not isinstance(record[field], str) or not re.fullmatch('[0-9a-f]{' + str(size) + '}', record[field]):
            raise ValueError(f'{field}: lowercase hexadecimal identifier required')
    counts = dict(unanswered=0, unknown=0, rated=0)
    for group, dimensions in (('control', DIMENSIONS), ('risk', RISK_FIELDS)):
        exact(record[group], dimensions, group)
        for dimension in dimensions:
            item = record[group][dimension]
            label = f'{group}.{dimension}'
            exact(item, ('state', 'value', 'confidence', 'rationale', 'evidence_note'), label)
            state = item['state']
            if not isinstance(state, str) or state not in counts:
                raise ValueError(f'{label}: invalid state')
            counts[state] += 1
            if state == 'unanswered':
                if any(item[k] is not None for k in ('value', 'confidence', 'rationale', 'evidence_note')):
                    raise ValueError(f'{label}: unanswered fields must all be null')
                continue
            if item['confidence'] not in ('low', 'medium', 'high', 'unknown'):
                raise ValueError(f'{label}: invalid supplied confidence')
            text(item['rationale'], label + '.rationale')
            text(item['evidence_note'], label + '.evidence_note')
            if state == 'unknown':
                if item['value'] is not None:
                    raise ValueError(f'{label}: unknown value must be null')
            elif group == 'control':
                unit(item['value'])
            elif type(item['value']) is not int or not 0 <= item['value'] <= 3:
                raise ValueError(f'{label}: ordinal integer 0..3 required')
    answered = counts['unknown'] + counts['rated']
    if answered or record['reviewer_alias'] is not None:
        text(record['reviewer_alias'], 'reviewer_alias')
    if answered or record['assessed_on'] is not None:
        text(record['assessed_on'], 'assessed_on')
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', record['assessed_on']):
            raise ValueError('assessed_on: YYYY-MM-DD required')
        date.fromisoformat(record['assessed_on'])
    return counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    args = parser.parse_args()
    try:
        counts = validate_response(load_json(args.input))
    except (ValueError, TypeError, OSError) as error:
        parser.error(str(error))
    print('Structurally valid synthetic practice response: ' +
          ', '.join(f'{key}={value}' for key, value in counts.items()))
    print('No evidence, identity, independence, dates or scoring conventions verified; no files written.')


if __name__ == '__main__':
    main()
