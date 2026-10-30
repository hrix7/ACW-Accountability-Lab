"""Read-only consistency verification; never extract or execute bundled files."""
import argparse
import hashlib
from pathlib import Path
import re
import stat
import zipfile

from dataset_manifest import verify_dataset
from strict_json import loads_json

# Frozen schema v1 inventory, independent of source files in the archive.
FILES = {'project.py', 'compare.py', 'mhc.py', 'provenance.py', 'strict_json.py',
         'case_io.py', 'dataset_manifest.py', 'README.txt',
         'data/case_records.json', 'data/synthetic_manifest.json', 'data/config.json',
         'reports/assessment.json', 'reports/assessment.html',
         'reports/comparison.json', 'reports/comparison.html'}
MAX_FILE_BYTES = 8 * 1024 * 1024
MAX_TOTAL_BYTES = 32 * 1024 * 1024
NOTICE = ('Consistency verified only. Bundled code was not executed; source truth, '
          'ratings and thresholds remain unvalidated. Changed files and a changed '
          'inventory can agree without establishing authenticity.')


def verify_bundle(path):
    with zipfile.ZipFile(path) as archive:
        entries = archive.infolist()
        names = [entry.filename for entry in entries]
        if len(names) != len(set(names)):
            raise ValueError('Duplicate archive member')
        if set(names) != FILES | {'BUNDLE.json'}:
            raise ValueError('Missing or unexpected archive members')
        if sum(entry.file_size for entry in entries) > MAX_TOTAL_BYTES:
            raise ValueError('Bundle exceeds total size limit')
        for entry in entries:
            kind = stat.S_IFMT(entry.external_attr >> 16)
            if entry.is_dir() or kind not in (0, stat.S_IFREG):
                raise ValueError('Only regular file members are supported')
            if entry.flag_bits & 1:
                raise ValueError('Encrypted members are unsupported')
            if entry.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
                raise ValueError('Unsupported compression method')
            if entry.file_size > MAX_FILE_BYTES:
                raise ValueError('Member exceeds size limit')
        contents = {}
        for entry in entries:
            with archive.open(entry) as source:
                content = source.read(MAX_FILE_BYTES + 1)
            if len(content) > MAX_FILE_BYTES or len(content) != entry.file_size:
                raise ValueError('Member size mismatch or limit exceeded')
            contents[entry.filename] = content
    index = loads_json(contents['BUNDLE.json'].decode('utf-8'))
    if not isinstance(index, dict) or set(index) != {
            'bundle_schema_version', 'dataset', 'model_version', 'notice', 'files_sha256'}:
        raise ValueError('Invalid bundle inventory fields')
    if type(index['bundle_schema_version']) is not int or index['bundle_schema_version'] != 1:
        raise ValueError('Unsupported bundle schema version')
    for key in ('model_version', 'notice'):
        if not isinstance(index[key], str) or not index[key].strip():
            raise ValueError(f'Invalid inventory {key}')
    hashes = index['files_sha256']
    if not isinstance(hashes, dict) or set(hashes) != FILES:
        raise ValueError('Missing or unexpected checksum entries')
    for name, digest in hashes.items():
        if not isinstance(digest, str) or not re.fullmatch(r'[0-9a-f]{64}', digest):
            raise ValueError(f'Invalid checksum for {name}')
        if hashlib.sha256(contents[name]).hexdigest() != digest:
            raise ValueError(f'Checksum mismatch: {name}')
    cases = loads_json(contents['data/case_records.json'].decode('utf-8'))
    manifest = loads_json(contents['data/synthetic_manifest.json'].decode('utf-8'))
    identity = verify_dataset(cases, manifest)
    # Compare serialized types as well as values (True must not equal count 1).
    from provenance import fingerprint
    if fingerprint(identity) != fingerprint(index['dataset']):
        raise ValueError('Inventory dataset identity disagrees with manifest')
    return {'dataset': identity, 'file_count': len(FILES), 'notice': NOTICE}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('bundle', type=Path)
    args = parser.parse_args()
    try:
        result = verify_bundle(args.bundle)
        print(f"Verified {result['file_count']} file checksums for synthetic dataset "
              f"{result['dataset']['dataset_id']} v{result['dataset']['dataset_version']}.")
        print(NOTICE)
    except (ValueError, KeyError, TypeError, AttributeError, OSError,
            zipfile.BadZipFile, RuntimeError, NotImplementedError) as error:
        parser.error(str(error))


if __name__ == '__main__':
    main()
