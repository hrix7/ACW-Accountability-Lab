import copy
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile
from unittest.mock import patch

from case_io import load_cases
from evaluation_bundle import build_bundle, export_bundle, SOURCE_FILES
from strict_json import load_json

ROOT = Path(__file__).parents[1]


class BundleTests(unittest.TestCase):
    def setUp(self):
        self.cases = load_cases(ROOT / 'data/case_records.json')
        self.manifest = load_json(ROOT / 'data/synthetic_manifest.json')

    def test_deterministic_complete_and_checksummed(self):
        before = copy.deepcopy((self.cases, self.manifest))
        content = build_bundle(self.cases, self.manifest)
        self.assertEqual(content, build_bundle(self.cases, self.manifest))
        self.assertEqual(before, (self.cases, self.manifest))
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            index = json.loads(archive.read('BUNDLE.json'))
            self.assertEqual(set(archive.namelist()), set(index['files_sha256']) | {'BUNDLE.json'})
            self.assertTrue(set(SOURCE_FILES) <= set(archive.namelist()))
            for name, digest in index['files_sha256'].items():
                self.assertEqual(digest, hashlib.sha256(archive.read(name)).hexdigest())
            self.assertEqual(json.loads(archive.read('data/case_records.json')), self.cases)
            self.assertIn('unvalidated', index['notice'])

    def test_extracted_source_reproduces_default_and_configured_reports(self):
        for config in ({}, load_json(ROOT / 'data/example_config.json')):
            with self.subTest(config=config), tempfile.TemporaryDirectory() as directory:
                directory = Path(directory)
                with zipfile.ZipFile(io.BytesIO(build_bundle(self.cases, self.manifest, config))) as archive:
                    archive.extractall(directory)  # Only our freshly generated, fixed-name ZIP.
                subprocess.run([sys.executable, 'dataset_manifest.py'], cwd=directory,
                               check=True, capture_output=True)
                for script, report in [('project.py', 'assessment'), ('compare.py', 'comparison')]:
                    subprocess.run([sys.executable, script, '--config', 'data/config.json',
                                    '--output', f'rerun/{report}.json', '--html', f'rerun/{report}.html'],
                                   cwd=directory, check=True, capture_output=True)
                    self.assertEqual(load_json(directory / f'reports/{report}.json'),
                                     load_json(directory / f'rerun/{report}.json'))
                    self.assertEqual((directory / f'reports/{report}.html').read_bytes(),
                                     (directory / f'rerun/{report}.html').read_bytes())

    def test_invalid_input_or_config_creates_nothing(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'bundle.zip'
            for config in ({'unexpected': 1}, {'threshold': 2}):
                with self.assertRaises(ValueError):
                    export_bundle(self.cases, self.manifest, config, target)
                self.assertFalse(target.exists())
            self.cases[0]['title'] += ' changed'
            with self.assertRaisesRegex(ValueError, 'fingerprint'):
                export_bundle(self.cases, self.manifest, {}, target)
            self.assertFalse(target.exists())

    def test_existing_file_and_symlink_are_protected(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'existing.zip'
            target.write_bytes(b'keep')
            link = Path(directory) / 'link.zip'
            link.symlink_to(target)
            for output in (target, link):
                with self.assertRaises(FileExistsError):
                    export_bundle(self.cases, self.manifest, {}, output)
            self.assertEqual(target.read_bytes(), b'keep')

    def test_disagreement_between_reports_fails(self):
        from compare import build_comparison
        comparison = build_comparison(self.cases)
        comparison['cases'][0]['control_score'] = -1
        with patch('evaluation_bundle.build_comparison', return_value=comparison):
            with self.assertRaisesRegex(ValueError, 'disagree'):
                build_bundle(self.cases, self.manifest)

    def test_cli_outside_repo_and_duplicate_input_rejection(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            command = [sys.executable, str(ROOT / 'evaluation_bundle.py'), '--output', 'bundle.zip']
            result = subprocess.run(command, cwd=directory, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((directory / 'bundle.zip').is_file())
            bad = directory / 'bad.json'
            bad.write_text('{"threshold":0.5,"threshold":0.6}')
            result = subprocess.run(command + ['--config', str(bad)], cwd=directory,
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn('Duplicate JSON key', result.stderr)
