"""All records in these tests are fabricated software fixtures, not reviews."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from mhc import DIMENSIONS
from project import RISK_FIELDS
from rating_response import validate_response

ROOT = Path(__file__).parents[1]


def blank():
    return dict(schema_version=1, synthetic=True, case_id='synthetic-fixture',
                scope='Fabricated test only', dataset_sha256='0'*64,
                repository_commit='0'*40, reviewer_alias=None, assessed_on=None,
                exposure='Fabricated fixture; no reviewer participated',
                **{g: {d: dict(state='unanswered', value=None, confidence=None,
                              rationale=None, evidence_note=None) for d in dims}
                   for g, dims in (('control', DIMENSIONS), ('risk', RISK_FIELDS))})


class ResponseTests(unittest.TestCase):
    def test_blank_is_not_unknown_and_is_not_mutated(self):
        r = blank()
        before = copy.deepcopy(r)
        self.assertEqual(validate_response(r), dict(unanswered=11, unknown=0, rated=0))
        self.assertEqual(r, before)

    def test_mixed_states_and_zero(self):
        r = blank()
        r.update(reviewer_alias='TEST FIXTURE ONLY', assessed_on='2000-01-01')
        r['control']['audit'].update(state='unknown', rationale='Fixture gap',
                                     confidence='unknown', evidence_note='No source; fixture')
        r['risk']['autonomy'].update(state='rated', value=0, rationale='Fixture zero',
                                     confidence='low', evidence_note='Synthetic assumption')
        self.assertEqual(validate_response(r), dict(unanswered=9, unknown=1, rated=1))

    def test_inconsistent_states_and_bad_values_rejected(self):
        for group, dim, value in [('control', 'audit', True), ('control', 'audit', float('nan')),
                                  ('control', 'audit', 1.1), ('risk', 'autonomy', .5),
                                  ('risk', 'autonomy', True), ('risk', 'autonomy', 4)]:
            r = blank()
            r.update(reviewer_alias='FIXTURE', assessed_on='2000-01-01')
            r[group][dim].update(state='rated', value=value, confidence='low',
                                rationale='Fixture', evidence_note='Fixture')
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_response(r)
        for patch in [dict(value=0), dict(state='unknown'), dict(state=[])]:
            r = blank()
            r['control']['audit'].update(patch)
            with self.assertRaises(ValueError):
                validate_response(r)

    def test_schema_metadata_and_dimensions_rejected(self):
        for key, value in [('schema_version', True), ('synthetic', False),
                           ('dataset_sha256', 'bad'), ('repository_commit', 'abc'),
                           ('assessed_on', '2000-02-30'), ('exposure', ''),
                           ('control', {}), ('reviewer_alias', '')]:
            r = blank()
            r[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_response(r)
        r = blank()
        r['extra'] = 1
        with self.assertRaises(ValueError):
            validate_response(r)

    def test_answer_requires_actual_metadata_and_explanation(self):
        r = blank()
        r['control']['audit'].update(state='unknown', confidence='unknown',
                                     rationale='Fixture', evidence_note='No source; fixture')
        with self.assertRaises(ValueError):
            validate_response(r)
        r.update(reviewer_alias='FIXTURE', assessed_on='2000-01-01')
        for field in ('rationale', 'evidence_note'):
            bad = copy.deepcopy(r)
            bad['control']['audit'][field] = ''
            with self.assertRaises(ValueError):
                validate_response(bad)

    def test_cli_read_only_and_strict_json(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'response.json'
            for content, status in [(json.dumps(blank()), 0),
                                    ('{"schema_version":1,"schema_version":1}', 2),
                                    ('{"value":NaN}', 2)]:
                path.write_text(content)
                result = subprocess.run([sys.executable, str(ROOT/'rating_response.py'), str(path)],
                                        capture_output=True, text=True, cwd=folder)
                self.assertEqual(result.returncode, status, result.stderr)
                self.assertEqual(path.read_text(), content)
                self.assertEqual(list(Path(folder).iterdir()), [path])


class ResponseDatasetTests(unittest.TestCase):
    def setUp(self):
        self.cases = json.loads((ROOT/'data/case_records.json').read_text())
        self.manifest = json.loads((ROOT/'data/synthetic_manifest.json').read_text())
        self.record = blank()
        self.record.update(case_id=self.cases[0]['id'], scope=self.cases[0]['scope'],
                           dataset_sha256=self.manifest['dataset_sha256'])

    def check(self):
        from rating_response import validate_response_dataset
        return validate_response_dataset(self.record, self.cases, self.manifest)

    def test_match_preserves_all_inputs_and_unanswered(self):
        before = copy.deepcopy((self.record, self.cases, self.manifest))
        self.assertEqual(self.check(), dict(unanswered=11, unknown=0, rated=0))
        self.assertEqual((self.record, self.cases, self.manifest), before)

    def test_response_identity_mismatches_rejected(self):
        for key, bad in [('case_id', 'absent'), ('scope', self.record['scope']+' '),
                         ('dataset_sha256', '0'*64)]:
            original = self.record[key]
            self.record[key] = bad
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.check()
            self.record[key] = original

    def test_dataset_must_match_manifest(self):
        self.cases[0]['scope'] += ' changed'
        self.record['scope'] = self.cases[0]['scope']
        with self.assertRaisesRegex(ValueError, 'fingerprint'):
            self.check()

    def test_cli_pair_success_failure_and_no_writes(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            paths = [folder/n for n in ('response.json', 'cases.json', 'manifest.json')]
            for path, value in zip(paths, (self.record, self.cases, self.manifest)):
                path.write_text(json.dumps(value))
            before = {p.name: p.read_bytes() for p in paths}
            base = [sys.executable, str(ROOT/'rating_response.py'), str(paths[0])]
            for options, status in [
                (['--dataset', str(paths[1])], 2),
                (['--manifest', str(paths[2])], 2),
                (['--dataset', str(paths[1]), '--manifest', str(paths[2])], 0)]:
                result = subprocess.run(base+options, cwd=folder, capture_output=True, text=True)
                self.assertEqual(result.returncode, status, result.stderr)
                if status == 0:
                    self.assertIn('exact scope match', result.stdout)
            self.assertEqual({p.name: p.read_bytes() for p in folder.iterdir()}, before)
