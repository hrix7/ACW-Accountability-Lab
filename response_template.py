"""Generate an unanswered v2 template for a verified synthetic case."""
import argparse
import json
from pathlib import Path

from dataset_manifest import verify_dataset
from mhc import DIMENSIONS
from project import RISK_FIELDS
from rating_response import validate_response_dataset
from strict_json import load_json


def build_template(cases, manifest, case_id, repository_commit, exposure):
    """Copy packet identity only; never infer reviewer answers or exposure."""
    identity = verify_dataset(cases, manifest)
    case = next((case for case in cases if case['id'] == case_id), None)
    if case is None:
        raise ValueError('Case ID is absent from verified dataset')
    record = dict(schema_version=2, synthetic=True, case_id=case_id,
                  scope=case['scope'], dataset_sha256=identity['dataset_sha256'],
                  repository_commit=repository_commit, exposure=exposure,
                  reviewer_alias=None, assessed_on=None)
    for group, dimensions in (('control', DIMENSIONS), ('risk', RISK_FIELDS)):
        record[group] = {
            dimension: dict(state='unanswered', value=None, confidence=None,
                            rationale=None, evidence_note=None, source_ids=[])
            for dimension in dimensions
        }
    validate_response_dataset(record, cases, manifest)
    return record


def export_template(cases, manifest, case_id, repository_commit, exposure, path):
    """Validate fully before exclusive creation; existing paths are protected."""
    record = build_template(cases, manifest, case_id, repository_commit, exposure)
    content = json.dumps(record, indent=2, ensure_ascii=False, allow_nan=False) + '\n'
    with Path(path).open('x', encoding='utf-8') as output:
        output.write(content)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--case-id', required=True)
    parser.add_argument('--repository-commit', required=True)
    parser.add_argument('--exposure', required=True,
                        help='Explicit preparation/exposure description; no reviewer exposure inferred')
    parser.add_argument('--output', type=Path, required=True,
                        help='New file; parent directory must exist')
    args = parser.parse_args()
    try:
        export_template(load_json(args.dataset), load_json(args.manifest),
                        args.case_id, args.repository_commit, args.exposure, args.output)
    except (ValueError, TypeError, KeyError, AttributeError, OSError) as error:
        parser.error(str(error))
    print('Created synthetic v2 template: 11 unanswered, no reviewer identity or date.')
    print('Commit syntax only checked; exposure is supplied text. No review or scoring validation claimed.')


if __name__ == '__main__':
    main()
