"""Read-only comparison of two synthetic practice responses; no consensus scoring."""
import argparse
from copy import deepcopy
import json
from pathlib import Path

from mhc import DIMENSIONS
from project import RISK_FIELDS
from rating_response import validate_response_dataset
from strict_json import load_json
from response_report import render_html
from provenance import fingerprint

STATUSES = ('both_unanswered', 'one_unanswered', 'both_unknown',
            'unknown_vs_rated', 'equal_rated', 'different_rated')


def compare_responses(left, right, cases, manifest):
    """Validate both against a packet before comparing states and exact values."""
    for record in (left, right):
        validate_response_dataset(record, cases, manifest)
    for field in ('case_id', 'scope', 'dataset_sha256', 'repository_commit'):
        if left[field] != right[field]:
            raise ValueError(f'Response {field} differs; use the same handoff packet')
    result = dict(schema_version=1, synthetic=True,
                  case_id=left['case_id'], scope=left['scope'],
                  dataset_sha256=left['dataset_sha256'],
                  repository_commit=left['repository_commit'])
    result['response_provenance'] = {
        'schema_version': 1,
        'fingerprint_format': 'sha256-python-json-sort-keys-compact-utf8-v1',
        'left_sha256': fingerprint(left),
        'right_sha256': fingerprint(right),
        'notice': ('Fingerprints identify complete parsed response records, not original '
                   'file bytes, reviewer authenticity or source truth. Retain both inputs '
                   'and the software revision used to reproduce this comparison.'),
    }
    result['limitations'] = (
        'Descriptive state/value comparison only; equal values do not establish consensus. '
        'No reviewer identity, independence, dates, exposure, source truth, commit provenance '
        'or scoring conventions verified. Thresholds remain unvalidated. '
        'No aggregate risk score or agreement statistic is calculated.')
    result['responses'] = {
        side: {key: record[key] for key in
               ('schema_version', 'reviewer_alias', 'assessed_on', 'exposure')}
        for side, record in (('left', left), ('right', right))
    }
    result['source_linkage_checked'] = {
        side: record['schema_version'] == 2
        for side, record in (('left', left), ('right', right))
    }
    for group, dimensions in (('control', DIMENSIONS), ('risk', RISK_FIELDS)):
        counts = dict.fromkeys(STATUSES, 0)
        rows = []
        for dimension in dimensions:
            a, b = left[group][dimension], right[group][dimension]
            states = (a['state'], b['state'])
            if states == ('unanswered', 'unanswered'):
                status = 'both_unanswered'
            elif 'unanswered' in states:
                status = 'one_unanswered'
            elif states == ('unknown', 'unknown'):
                status = 'both_unknown'
            elif 'unknown' in states:
                status = 'unknown_vs_rated'
            else:
                status = 'equal_rated' if a['value'] == b['value'] else 'different_rated'
            counts[status] += 1
            rows.append(dict(dimension=dimension, status=status,
                             left=deepcopy(a), right=deepcopy(b)))
        result[group] = dict(counts=counts, rows=rows)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('left', type=Path)
    parser.add_argument('right', type=Path)
    parser.add_argument('--dataset', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--format', choices=('json', 'html'), default='json')
    args = parser.parse_args()
    try:
        result = compare_responses(load_json(args.left), load_json(args.right),
                                   load_json(args.dataset), load_json(args.manifest))
    except (ValueError, TypeError, KeyError, AttributeError, OSError) as error:
        parser.error(str(error))
    print(render_html(result) if args.format == 'html' else
          json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False))


if __name__ == '__main__':
    main()
