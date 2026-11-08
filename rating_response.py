"""Read-only structural validation of synthetic practice response records."""
import argparse
from datetime import date
from pathlib import Path
import re

from mhc import DIMENSIONS, unit
from project import RISK_FIELDS
from strict_json import load_json
from dataset_manifest import verify_dataset


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
    if type(record['schema_version']) is not int or record['schema_version'] not in (1, 2):
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
            fields = ('state', 'value', 'confidence', 'rationale', 'evidence_note')
            if record['schema_version'] == 2:
                fields += ('source_ids',)
            exact(item, fields, label)
            if record['schema_version'] == 2:
                refs = item['source_ids']
                if (not isinstance(refs, list) or
                        any(not isinstance(ref, str) or not ref.strip() for ref in refs) or
                        len(set(refs)) != len(refs)):
                    raise ValueError(f'{label}: source_ids must be unique nonempty strings')
                if item['state'] == 'unanswered' and refs:
                    raise ValueError(f'{label}: unanswered source_ids must be empty')
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



def validate_response_dataset(record, cases, manifest):
    """Match a response to an explicitly supplied, manifest-verified dataset."""
    counts = validate_response(record)
    identity = verify_dataset(cases, manifest)
    if record['dataset_sha256'] != identity['dataset_sha256']:
        raise ValueError('Response dataset fingerprint does not match verified dataset')
    case = next((case for case in cases if case['id'] == record['case_id']), None)
    if case is None:
        raise ValueError('Response case ID is absent from verified dataset')
    if record['scope'] != case['scope']:
        raise ValueError('Response scope does not exactly match the selected case')
    if record['schema_version'] == 2:
        source_ids = {source['id'] for source in case['sources']}
        for group in ('control', 'risk'):
            for dimension, item in record[group].items():
                if any(ref not in source_ids for ref in item['source_ids']):
                    raise ValueError(f'{group}.{dimension}: source ID absent from selected case')
    return counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--dataset', type=Path, help='Explicit synthetic case dataset')
    parser.add_argument('--manifest', type=Path, help='Manifest for the selected dataset')
    args = parser.parse_args()
    if (args.dataset is None) != (args.manifest is None):
        parser.error('--dataset and --manifest must be supplied together')
    try:
        record = load_json(args.input)
        if args.dataset is None:
            counts = validate_response(record)
        else:
            counts = validate_response_dataset(record, load_json(args.dataset),
                                               load_json(args.manifest))
    except (ValueError, TypeError, KeyError, AttributeError, OSError) as error:
        parser.error(str(error))
    print('Structurally valid synthetic practice response: ' +
          ', '.join(f'{key}={value}' for key, value in counts.items()))
    if args.dataset is not None:
        print('Dataset fingerprint, case ID and exact scope match the supplied verified dataset.')
    else:
        print('Dataset identity not checked (no dataset/manifest supplied).')
    if record['schema_version'] == 2 and args.dataset is not None:
        print('Structured source IDs match the selected case catalog; source truth not verified.')
    else:
        print('Source linkage not checked (requires schema v2 and dataset/manifest).')
    print('No evidence, reviewer identity, independence, dates or scoring conventions verified; no files written.')


if __name__ == '__main__':
    main()
