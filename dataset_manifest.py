"""Verify a versioned synthetic dataset against a reviewed manifest; never write files."""
import argparse
from pathlib import Path
import re

from case_io import load_cases, validate_cases
from provenance import fingerprint
from strict_json import load_json

FORMAT = 'sha256-python-json-sort-keys-compact-utf8-v1'
FIELDS = {'schema_version', 'dataset_id', 'dataset_version', 'fingerprint_format',
          'dataset_sha256', 'case_ids', 'synthetic'}


def validate_manifest(manifest):
    if not isinstance(manifest, dict) or set(manifest) != FIELDS:
        raise ValueError('Manifest requires exactly the supported schema fields')
    if type(manifest['schema_version']) is not int or manifest['schema_version'] != 1:
        raise ValueError('Unsupported manifest schema version')
    if not isinstance(manifest['dataset_id'], str) or not re.fullmatch(
            r'[a-z0-9]+(?:-[a-z0-9]+)*', manifest['dataset_id']):
        raise ValueError('dataset_id must be a lowercase hyphenated identifier')
    if not isinstance(manifest['dataset_version'], str) or not re.fullmatch(
            r'(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)', manifest['dataset_version']):
        raise ValueError('dataset_version must be major.minor.patch')
    if manifest['fingerprint_format'] != FORMAT:
        raise ValueError('Unsupported fingerprint format')
    if not isinstance(manifest['dataset_sha256'], str) or not re.fullmatch(
            r'[0-9a-f]{64}', manifest['dataset_sha256']):
        raise ValueError('dataset_sha256 must be a lowercase SHA-256 digest')
    ids = manifest['case_ids']
    if (not isinstance(ids, list) or not ids or
            any(not isinstance(item, str) or not item.strip() for item in ids) or
            len(set(ids)) != len(ids)):
        raise ValueError('case_ids must contain unique nonempty strings in dataset order')
    if manifest['synthetic'] is not True:
        raise ValueError('This manifest schema supports synthetic datasets only')
    return manifest


def verify_dataset(cases, manifest):
    validate_manifest(manifest)
    validate_cases(cases)
    if any(case['synthetic'] is not True for case in cases):
        raise ValueError('Dataset must contain only explicitly synthetic cases')
    if [case['id'] for case in cases] != manifest['case_ids']:
        raise ValueError('Dataset case IDs or order do not match the manifest')
    if fingerprint(cases) != manifest['dataset_sha256']:
        raise ValueError('Dataset fingerprint does not match the manifest')
    return {'dataset_id': manifest['dataset_id'],
            'dataset_version': manifest['dataset_version'],
            'case_count': len(cases), 'dataset_sha256': manifest['dataset_sha256']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    root = Path(__file__).parent
    parser.add_argument('--input', type=Path, default=root / 'data/case_records.json')
    parser.add_argument('--manifest', type=Path, default=root / 'data/synthetic_manifest.json')
    args = parser.parse_args()
    try:
        result = verify_dataset(load_cases(args.input), load_json(args.manifest))
        print(f"Verified synthetic dataset {result['dataset_id']} "
              f"v{result['dataset_version']} ({result['case_count']} cases).")
        print('Integrity match only; sources, ratings and thresholds remain unvalidated.')
    except (ValueError, KeyError, TypeError, AttributeError, OSError) as error:
        parser.error(str(error))


if __name__ == '__main__':
    main()
