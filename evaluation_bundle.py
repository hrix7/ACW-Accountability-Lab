"""Build a reproducible evaluation ZIP for a verified synthetic dataset."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import zipfile

from case_io import load_cases
from compare import build_comparison, render_comparison
from dataset_manifest import verify_dataset
from project import evaluate, render_report
from provenance import build_provenance
from strict_json import load_json

ROOT = Path(__file__).parent
SOURCE_FILES = ('project.py', 'compare.py', 'mhc.py', 'provenance.py',
                'strict_json.py', 'case_io.py', 'dataset_manifest.py')
NOTICE = ('Synthetic software demonstration. Sources, ratings, weights, floors and '
          'thresholds remain unvalidated. Checksums establish file consistency, '
          'not authenticity or research validity.')


def json_bytes(value):
    return (json.dumps(value, indent=2, ensure_ascii=False,
                       allow_nan=False) + '\n').encode('utf-8')


def build_bundle(cases, manifest, config=None):
    """Validate and render everything in memory before any destination is created."""
    identity = verify_dataset(cases, manifest)
    config = {} if config is None else config
    comparison = build_comparison(cases, config)
    assessment = {
        'model_version': comparison['model_version'],
        'results': [evaluate(case, config.get('threshold'), config.get('weights'),
                             config.get('floors')) for case in cases],
        'provenance': build_provenance(cases, config),
    }
    if assessment['provenance'] != comparison['provenance']:
        raise ValueError('Assessment and comparison provenance disagree')
    for result, summary in zip(assessment['results'], comparison['cases']):
        for key in ('id', 'synthetic', 'status', 'control_score',
                    'missing_evidence_bounds', 'component_floors'):
            if result.get(key) != summary.get(key):
                raise ValueError(f'Assessment and comparison disagree on {key}')
    files = {
        'data/case_records.json': json_bytes(cases),
        'data/synthetic_manifest.json': json_bytes(manifest),
        'data/config.json': json_bytes(config),
        'reports/assessment.json': json_bytes(assessment),
        'reports/assessment.html': render_report(assessment).encode('utf-8'),
        'reports/comparison.json': json_bytes(comparison),
        'reports/comparison.html': render_comparison(comparison).encode('utf-8'),
    }
    for name in SOURCE_FILES:
        files[name] = (ROOT / name).read_bytes()
    files['README.txt'] = (NOTICE + '\n\n'
        'Python 3.10+; standard library only. From the extracted directory:\n'
        'python dataset_manifest.py\n'
        'python project.py --config data/config.json --output rerun/assessment.json '
        '--html rerun/assessment.html\n'
        'python compare.py --config data/config.json --output rerun/comparison.json '
        '--html rerun/comparison.html\n\n'
        'Compare parsed JSON objects between reports/ and rerun/; whitespace and '
        'object key order may differ. HTML should match byte for byte.\n'
        'BUNDLE.json lists SHA-256 hashes of exact file bytes, including the '
        'source snapshot. It excludes itself. Keep the original ZIP and its '
        'trusted repository revision; changing files and checksums together '
        'can produce a consistent but unauthenticated bundle.\n').encode('utf-8')
    files['BUNDLE.json'] = json_bytes({
        'bundle_schema_version': 1, 'dataset': identity,
        'model_version': assessment['model_version'], 'notice': NOTICE,
        'files_sha256': {name: hashlib.sha256(content).hexdigest()
                         for name, content in sorted(files.items())},
    })
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_STORED) as archive:
        for name, content in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, content)
    return buffer.getvalue()


def export_bundle(cases, manifest, config, output):
    content = build_bundle(cases, manifest, config)
    with Path(output).open('xb') as destination:
        destination.write(content)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=ROOT / 'data/case_records.json')
    parser.add_argument('--manifest', type=Path, default=ROOT / 'data/synthetic_manifest.json')
    parser.add_argument('--config', type=Path)
    parser.add_argument('--output', type=Path, required=True,
                        help='New ZIP path; parent directory must exist')
    args = parser.parse_args()
    try:
        export_bundle(load_cases(args.input), load_json(args.manifest),
                      load_json(args.config) if args.config else {}, args.output)
        print(f'Created synthetic evaluation bundle: {args.output}')
        print(NOTICE)
    except (ValueError, KeyError, TypeError, AttributeError, OSError) as error:
        parser.error(str(error))


if __name__ == '__main__':
    main()
