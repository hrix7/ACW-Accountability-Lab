import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from case_io import load_cases
from dataset_manifest import validate_manifest, verify_dataset
from provenance import fingerprint
from strict_json import load_json

ROOT = Path(__file__).parents[1]


class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.cases = load_cases(ROOT / 'data/case_records.json')
        self.manifest = load_json(ROOT / 'data/synthetic_manifest.json')

    def test_published_manifest_matches_without_mutation(self):
        before = copy.deepcopy((self.cases, self.manifest))
        result = verify_dataset(self.cases, self.manifest)
        self.assertEqual(result['case_count'], 3)
        self.assertEqual((self.cases, self.manifest), before)

    def test_changed_rating_unknown_or_evidence_fails(self):
        for field, value in [('value', None), ('rationale', 'Changed rationale'),
                             ('confidence', 'low')]:
            cases = copy.deepcopy(self.cases)
            cases[0]['control']['predict'][field] = value
            with self.assertRaisesRegex(ValueError, 'fingerprint'):
                verify_dataset(cases, self.manifest)

    def test_reordering_and_missing_cases_fail(self):
        for cases in (list(reversed(self.cases)), self.cases[:2]):
            with self.assertRaisesRegex(ValueError, 'IDs or order'):
                verify_dataset(cases, self.manifest)

    def test_real_case_rejected_even_with_matching_hash(self):
        self.cases[0]['synthetic'] = False
        for group in ('control', 'risk'):
            for rating in self.cases[0][group].values():
                rating['value'] = None
        self.manifest['dataset_sha256'] = fingerprint(self.cases)
        with self.assertRaisesRegex(ValueError, 'explicitly synthetic'):
            verify_dataset(self.cases, self.manifest)

    def test_invalid_manifest_fields_fail(self):
        for key, value in [('schema_version', True), ('schema_version', 2),
                           ('dataset_version', '01.0.0'), ('dataset_version', None),
                           ('dataset_id', '../private'), ('fingerprint_format', 'unknown'),
                           ('dataset_sha256', 'x'*64), ('synthetic', 1),
                           ('case_ids', ['same', 'same']), ('case_ids', [{}])]:
            manifest = dict(self.manifest, **{key: value})
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                validate_manifest(manifest)
        for manifest in (None, {}, dict(self.manifest, unexpected=True)):
            with self.assertRaises(ValueError):
                validate_manifest(manifest)

    def test_formatting_only_change_passes(self):
        reformatted = json.loads(json.dumps(self.cases, sort_keys=True, indent=4))
        verify_dataset(reformatted, self.manifest)

    def test_cli_success_and_failure_are_read_only(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            cases = directory / 'cases.json'
            manifest = directory / 'manifest.json'
            cases.write_text(json.dumps(self.cases))
            manifest.write_text(json.dumps(self.manifest))
            command = [sys.executable, str(ROOT / 'dataset_manifest.py'),
                       '--input', str(cases), '--manifest', str(manifest)]
            before = {p.name: p.read_bytes() for p in directory.iterdir()}
            result = subprocess.run(command, cwd=directory, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('remain unvalidated', result.stdout)
            self.assertEqual(before, {p.name: p.read_bytes() for p in directory.iterdir()})
            manifest.write_text('{"schema_version":1,"schema_version":1}')
            before = {p.name: p.read_bytes() for p in directory.iterdir()}
            result = subprocess.run(command, cwd=directory, capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn('Duplicate JSON key', result.stderr)
            self.assertEqual(before, {p.name: p.read_bytes() for p in directory.iterdir()})

    def test_cli_default_paths_work_outside_repository(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run([sys.executable, str(ROOT / 'dataset_manifest.py')],
                                    cwd=directory, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('v1.0.0', result.stdout)
