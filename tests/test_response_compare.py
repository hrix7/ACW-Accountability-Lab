"""Fabricated software fixtures only, not actual reviewer responses."""
import copy
import itertools
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from response_compare import compare_responses
from response_template import build_template
from strict_json import load_json

ROOT = Path(__file__).resolve().parents[1]


class ResponseComparisonTests(unittest.TestCase):
    def setUp(self):
        self.cases = load_json(ROOT / 'data/case_records.json')
        self.manifest = load_json(ROOT / 'data/synthetic_manifest.json')
        self.left = build_template(self.cases, self.manifest, self.cases[0]['id'],
                                   '0' * 40, 'Fabricated test fixture only')
        self.right = copy.deepcopy(self.left)

    def compare(self):
        return compare_responses(self.left, self.right, self.cases, self.manifest)

    def answer(self, record, state, value=None, group='control', dimension='understand'):
        if state == 'unanswered':
            return
        record['reviewer_alias'] = 'software-fixture'
        record['assessed_on'] = '2000-01-01'  # Fixture date, not a review event.
        record[group][dimension].update(state=state, value=value, confidence='unknown',
            rationale='Synthetic test fixture', evidence_note='No actual reviewer or evidence')

    def test_all_state_pairs_and_symmetry(self):
        for a, b in itertools.product(('unanswered', 'unknown', 'rated'), repeat=2):
            with self.subTest(a=a, b=b):
                self.setUp()
                self.answer(self.left, a, 0 if a == 'rated' else None)
                self.answer(self.right, b, 0 if b == 'rated' else None)
                expected = ('both_unanswered' if a == b == 'unanswered' else
                            'one_unanswered' if 'unanswered' in (a, b) else
                            'both_unknown' if a == b == 'unknown' else
                            'unknown_vs_rated' if 'unknown' in (a, b) else 'equal_rated')
                row = self.compare()['control']['rows'][0]
                self.assertEqual(row['status'], expected)
                self.assertEqual(row['left'], self.left['control']['understand'])
                reverse = compare_responses(self.right, self.left, self.cases, self.manifest)
                self.assertEqual(reverse['control']['rows'][0]['status'], expected)

    def test_numeric_differences_and_no_mutation(self):
        for group, dimension, a, b in (('control', 'understand', 0, 0.01),
                                       ('risk', 'autonomy', 0, 3)):
            self.answer(self.left, 'rated', a, group, dimension)
            self.answer(self.right, 'rated', b, group, dimension)
        before = copy.deepcopy((self.left, self.right, self.cases, self.manifest))
        result = self.compare()
        for group, total in (('control', 5), ('risk', 6)):
            self.assertEqual(result[group]['counts']['different_rated'], 1)
            self.assertEqual(sum(result[group]['counts'].values()), total)
        self.assertEqual((self.left, self.right, self.cases, self.manifest), before)
        result['control']['rows'][0]['left']['source_ids'].append('fixture')
        self.assertEqual(self.left['control']['understand']['source_ids'], [])

    def test_packet_mismatches_rejected(self):
        original = copy.deepcopy(self.right)
        for field, value in (('repository_commit', '1' * 40), ('scope', 'different'),
                             ('dataset_sha256', '1' * 64), ('case_id', 'missing')):
            self.right = copy.deepcopy(original)
            self.right[field] = value
            with self.assertRaises(ValueError):
                self.compare()
        self.right = build_template(self.cases, self.manifest, self.cases[1]['id'],
                                    '0' * 40, 'Fixture')
        with self.assertRaises(ValueError):
            self.compare()

    def test_invalid_rating_and_catalog_rejected(self):
        self.answer(self.right, 'rated', True)
        with self.assertRaises(ValueError):
            self.compare()
        self.right['control']['understand']['value'] = 0
        self.right['control']['understand']['source_ids'] = ['absent-source']
        with self.assertRaises(ValueError):
            self.compare()

    def test_mixed_versions_and_blank_records(self):
        self.left['schema_version'] = 1
        for group in ('control', 'risk'):
            for item in self.left[group].values():
                del item['source_ids']
        result = self.compare()
        self.assertEqual(result['source_linkage_checked'], dict(left=False, right=True))
        self.assertEqual(result['risk']['counts']['both_unanswered'], 6)
        self.assertIsNone(result['responses']['left']['reviewer_alias'])
        self.assertIn('do not establish consensus', result['limitations'])

    def test_cli_read_only_and_strict_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            for name, data in (('left', self.left), ('right', self.right),
                               ('cases', self.cases), ('manifest', self.manifest)):
                (folder / (name + '.json')).write_text(json.dumps(data))
            command = [sys.executable, str(ROOT / 'response_compare.py'), 'left.json',
                       'right.json', '--dataset', 'cases.json', '--manifest', 'manifest.json']
            before = {p.name: p.read_bytes() for p in folder.iterdir()}
            run = subprocess.run(command, cwd=tmp, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(json.loads(run.stdout)['control']['counts']['both_unanswered'], 5)
            self.assertEqual(before, {p.name: p.read_bytes() for p in folder.iterdir()})
            (folder / 'right.json').write_text('{"duplicate":1,"duplicate":2}')
            run = subprocess.run(command, cwd=tmp, capture_output=True, text=True)
            self.assertEqual(run.returncode, 2)
            self.assertEqual(run.stdout, '')
