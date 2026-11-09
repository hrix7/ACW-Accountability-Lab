"""Synthetic software fixtures only; no reviewer responses."""
import copy
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from rating_response import validate_response_dataset
from response_template import build_template, export_template
from strict_json import load_json

ROOT = Path(__file__).resolve().parents[1]


class TemplateTests(unittest.TestCase):
    def setUp(self):
        self.cases = load_json(ROOT / 'data/case_records.json')
        self.manifest = load_json(ROOT / 'data/synthetic_manifest.json')
        self.args = (self.cases, self.manifest, self.cases[0]['id'],
                     '0' * 40, 'Preparation only; no reviewer exposure recorded.')

    def test_all_cases_blank_and_inputs_unchanged(self):
        before = copy.deepcopy((self.cases, self.manifest))
        for case in self.cases:
            record = build_template(self.cases, self.manifest, case['id'], *self.args[3:])
            self.assertEqual(validate_response_dataset(record, self.cases, self.manifest),
                             dict(unanswered=11, unknown=0, rated=0))
            self.assertIsNone(record['reviewer_alias'])
            self.assertIsNone(record['assessed_on'])
            self.assertEqual(record['scope'], case['scope'])
            self.assertIs(record['synthetic'], True)
            self.assertEqual(record['schema_version'], 2)
            for group in ('control', 'risk'):
                for item in record[group].values():
                    self.assertEqual(item, dict(state='unanswered', value=None,
                        confidence=None, rationale=None, evidence_note=None, source_ids=[]))
        self.assertEqual((self.cases, self.manifest), before)

    def test_rows_are_independent(self):
        record = build_template(*self.args)
        record['control']['understand']['source_ids'].append('fixture')
        self.assertEqual(record['control']['predict']['source_ids'], [])
        self.assertEqual(build_template(*self.args)['control']['understand']['source_ids'], [])

    def test_invalid_inputs_create_nothing(self):
        variants = []
        for index, value in ((2, 'absent'), (3, 'bad'), (4, ' ')):
            args = list(self.args)
            args[index] = value
            variants.append(args)
        changed = copy.deepcopy(self.args)
        changed[0][0]['scope'] += ' changed'
        variants.append(changed)
        nonsynthetic = copy.deepcopy(self.args)
        nonsynthetic[0][0]['synthetic'] = False
        variants.append(nonsynthetic)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'response.json'
            for args in variants:
                with self.assertRaises(ValueError):
                    export_template(*args, path)
                self.assertFalse(path.exists())

    def test_export_protects_files_and_symlinks(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'response.json'
            export_template(*self.args, path)
            content = path.read_bytes()
            self.assertEqual(load_json(path), build_template(*self.args))
            link = Path(tmp) / 'link.json'
            link.symlink_to(path)
            dangling = Path(tmp) / 'dangling.json'
            target = Path(tmp) / 'missing.json'
            dangling.symlink_to(target)
            for protected in (path, link, dangling):
                with self.assertRaises(FileExistsError):
                    export_template(*self.args, protected)
            self.assertEqual(path.read_bytes(), content)
            self.assertFalse(target.exists())

    def test_cli_round_trip_and_rejections(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / 'response.json'
            command = [sys.executable, str(ROOT / 'response_template.py'),
                '--dataset', str(ROOT / 'data/case_records.json'),
                '--manifest', str(ROOT / 'data/synthetic_manifest.json'),
                '--case-id', self.args[2], '--repository-commit', self.args[3],
                '--exposure', self.args[4], '--output', str(output)]
            run = subprocess.run(command, cwd=tmp, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertIn('11 unanswered', run.stdout)
            check = subprocess.run([sys.executable, str(ROOT / 'rating_response.py'),
                str(output), '--dataset', command[3], '--manifest', command[5]],
                cwd=tmp, capture_output=True, text=True)
            self.assertEqual(check.returncode, 0, check.stderr)
            before = output.read_bytes()
            self.assertEqual(subprocess.run(command, capture_output=True).returncode, 2)
            self.assertEqual(output.read_bytes(), before)
            output.unlink()
            bad = Path(tmp) / 'bad.json'
            bad.write_text('{"duplicate":1,"duplicate":2}')
            command[3] = str(bad)
            self.assertEqual(subprocess.run(command, capture_output=True).returncode, 2)
            self.assertFalse(output.exists())
