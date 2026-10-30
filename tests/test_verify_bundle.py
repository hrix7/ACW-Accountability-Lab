import hashlib
import io
import json
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import warnings
import zipfile

from case_io import load_cases
from evaluation_bundle import build_bundle
from strict_json import load_json
from verify_bundle import verify_bundle

ROOT = Path(__file__).parents[1]


class VerifyBundleTests(unittest.TestCase):
    def setUp(self):
        self.bundle = build_bundle(load_cases(ROOT / 'data/case_records.json'),
                                   load_json(ROOT / 'data/synthetic_manifest.json'))
        with zipfile.ZipFile(io.BytesIO(self.bundle)) as archive:
            self.files = {name: archive.read(name) for name in archive.namelist()}

    def archive(self, files=None, extra=None):
        output = io.BytesIO()
        with zipfile.ZipFile(output, 'w') as archive:
            for name, content in (self.files if files is None else files).items():
                archive.writestr(name, content)
            if extra:
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore', UserWarning)
                    archive.writestr(*extra)
        output.seek(0)
        return output

    def test_generated_bundle_passes(self):
        result = verify_bundle(io.BytesIO(self.bundle))
        self.assertEqual(result['file_count'], 15)
        self.assertIn('not executed', result['notice'])

    def test_missing_unexpected_and_duplicate_members_fail(self):
        files = dict(self.files)
        del files['project.py']
        for archive in (self.archive(files), self.archive(extra=('../outside', b'x')),
                        self.archive(extra=('project.py', b'x'))):
            with self.assertRaises(ValueError):
                verify_bundle(archive)

    def test_changed_file_fails_checksum(self):
        self.files['reports/assessment.html'] += b'changed'
        with self.assertRaisesRegex(ValueError, 'Checksum mismatch'):
            verify_bundle(self.archive())

    def test_malformed_and_duplicate_inventory_keys_fail(self):
        for content in (b'{"bundle_schema_version":1,"bundle_schema_version":1}', b'[]',
                        b'{"x":NaN}', b'\xff'):
            self.files['BUNDLE.json'] = content
            with self.assertRaises(ValueError):
                verify_bundle(self.archive())

    def test_invalid_schema_hash_inventory_and_identity_fail(self):
        original = json.loads(self.files['BUNDLE.json'])
        for key, value in [('bundle_schema_version', True), ('files_sha256', {}),
                           ('dataset', {}), ('notice', '')]:
            index = dict(original, **{key: value})
            self.files['BUNDLE.json'] = json.dumps(index).encode()
            with self.assertRaises(ValueError):
                verify_bundle(self.archive())

    def test_rehashed_dataset_change_still_fails_manifest(self):
        cases = json.loads(self.files['data/case_records.json'])
        cases[0]['title'] += ' changed'
        self.files['data/case_records.json'] = json.dumps(cases).encode()
        index = json.loads(self.files['BUNDLE.json'])
        index['files_sha256']['data/case_records.json'] = hashlib.sha256(
            self.files['data/case_records.json']).hexdigest()
        self.files['BUNDLE.json'] = json.dumps(index).encode()
        with self.assertRaisesRegex(ValueError, 'fingerprint'):
            verify_bundle(self.archive())

    def test_symlink_and_size_limits_fail(self):
        files = dict(self.files)
        del files['project.py']
        link = zipfile.ZipInfo('project.py')
        link.create_system = 3
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        with self.assertRaisesRegex(ValueError, 'regular'):
            verify_bundle(self.archive(files, (link, b'/tmp/target')))
        for limit in ('MAX_FILE_BYTES', 'MAX_TOTAL_BYTES'):
            with patch('verify_bundle.' + limit, 1), self.assertRaisesRegex(ValueError, 'limit'):
                verify_bundle(io.BytesIO(self.bundle))

    def test_cli_is_read_only_and_does_not_execute_source(self):
        self.files['project.py'] = b'raise RuntimeError("must not execute")'
        index = json.loads(self.files['BUNDLE.json'])
        index['files_sha256']['project.py'] = hashlib.sha256(self.files['project.py']).hexdigest()
        self.files['BUNDLE.json'] = json.dumps(index).encode()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'bundle.zip'
            path.write_bytes(self.archive().getvalue())
            before = path.read_bytes()
            result = subprocess.run([sys.executable, str(ROOT / 'verify_bundle.py'), str(path)],
                                    cwd=directory, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(list(Path(directory).iterdir()), [path])
            self.assertEqual(path.read_bytes(), before)
            path.write_bytes(b'not a zip')
            result = subprocess.run([sys.executable, str(ROOT / 'verify_bundle.py'), str(path)],
                                    cwd=directory, capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
