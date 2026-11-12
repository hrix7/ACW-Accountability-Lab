"""Response fingerprint checks using synthetic software fixtures only."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from response_compare import compare_responses
from response_report import render_html
from response_template import build_template
from strict_json import load_json

ROOT = Path(__file__).resolve().parents[1]


class ResponseProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.cases = load_json(ROOT / 'data/case_records.json')
        self.manifest = load_json(ROOT / 'data/synthetic_manifest.json')
        self.left = build_template(self.cases, self.manifest, self.cases[0]['id'],
                                   '0' * 40, 'Synthetic fixture – no actual review')
        self.right = copy.deepcopy(self.left)
        self.right['exposure'] += ' (right)'

    def compare(self, left=None, right=None):
        return compare_responses(self.left if left is None else left,
                                 self.right if right is None else right,
                                 self.cases, self.manifest)

    def test_exact_convention_order_and_no_mutation(self):
        before = copy.deepcopy((self.left, self.right))
        result = self.compare()
        for side, record in zip(('left', 'right'), before):
            encoded = json.dumps(record, sort_keys=True, separators=(',', ':'),
                                 ensure_ascii=False, allow_nan=False).encode('utf-8')
            self.assertEqual(result['response_provenance'][side + '_sha256'],
                             hashlib.sha256(encoded).hexdigest())
        reordered = json.loads(json.dumps(self.left, sort_keys=True, indent=4))
        self.assertEqual(self.compare(reordered)['response_provenance'], result['response_provenance'])
        swapped = self.compare(self.right, self.left)['response_provenance']
        self.assertEqual(swapped['left_sha256'], result['response_provenance']['right_sha256'])
        self.assertEqual((self.left, self.right), before)

    def test_metadata_and_answer_changes_affect_only_their_side(self):
        baseline = self.compare()['response_provenance']
        for field, value in (('exposure', 'Different fixture exposure'),
                             ('reviewer_alias', 'fixture'), ('assessed_on', '2000-01-01')):
            record = copy.deepcopy(self.left)
            record[field] = value
            changed = self.compare(record)['response_provenance']
            self.assertNotEqual(changed['left_sha256'], baseline['left_sha256'])
            self.assertEqual(changed['right_sha256'], baseline['right_sha256'])
        record = copy.deepcopy(self.left)
        record.update(reviewer_alias='fixture', assessed_on='2000-01-01')
        item = record['control']['understand']
        item.update(state='unknown', rationale='Fixture only', evidence_note='No evidence', confidence='unknown')
        unknown = self.compare(record)['response_provenance']['left_sha256']
        self.assertNotEqual(unknown, baseline['left_sha256'])
        item.update(state='rated', value=0)
        zero = self.compare(record)['response_provenance']['left_sha256']
        self.assertNotEqual(zero, unknown)
        item['value'] = 0.0
        self.assertNotEqual(self.compare(record)['response_provenance']['left_sha256'], zero)
        for field, value in (('rationale', 'Revised fixture'), ('confidence', 'low'),
                             ('evidence_note', 'Revised note')):
            changed = copy.deepcopy(record)
            changed['control']['understand'][field] = value
            self.assertNotEqual(self.compare(changed)['response_provenance'],
                                self.compare(record)['response_provenance'])

    def test_v1_and_html_match_json(self):
        for group in ('control', 'risk'):
            for item in self.left[group].values():
                del item['source_ids']
        self.left['schema_version'] = 1
        result = self.compare()
        html = render_html(result)
        for side in ('left', 'right'):
            self.assertIn(result['response_provenance'][side + '_sha256'], html)
        self.assertIn('not original file bytes', html)
        self.assertIn('sha256-python-json-sort-keys-compact-utf8-v1', html)
        legacy = copy.deepcopy(result)
        del legacy['response_provenance']
        self.assertNotIn('Reproducibility metadata', render_html(legacy))

    def test_cli_formats_and_read_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            for name, data in (('left', self.left), ('right', self.right),
                               ('cases', self.cases), ('manifest', self.manifest)):
                (folder / (name + '.json')).write_text(json.dumps(data, ensure_ascii=True))
            before = {p.name: p.read_bytes() for p in folder.iterdir()}
            command = [sys.executable, str(ROOT / 'response_compare.py'), 'left.json',
                       'right.json', '--dataset', 'cases.json', '--manifest', 'manifest.json']
            outputs = []
            for fmt in ('json', 'html'):
                run = subprocess.run(command + ['--format', fmt], cwd=tmp, capture_output=True, text=True)
                self.assertEqual(run.returncode, 0, run.stderr)
                outputs.append(run.stdout)
            provenance = json.loads(outputs[0])['response_provenance']
            self.assertEqual(provenance, self.compare()['response_provenance'])
            for side in ('left', 'right'):
                self.assertIn(provenance[side + '_sha256'], outputs[1])
            self.assertEqual(before, {p.name: p.read_bytes() for p in folder.iterdir()})
