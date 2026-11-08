"""Fabricated software fixtures only; no reviewer responses."""
import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest
from test_rating_response import blank, ROOT
from provenance import fingerprint
from rating_response import validate_response, validate_response_dataset


class SourceResponseTests(unittest.TestCase):
    def setUp(self):
        self.cases = json.loads((ROOT/'data/case_records.json').read_text())
        self.manifest = json.loads((ROOT/'data/synthetic_manifest.json').read_text())
        self.cases[0]['sources'] = [dict(id='fixture', title='Synthetic fixture',
            url='https://example.invalid/fixture', locator='Fixture section')]
        self.cases[1]['sources'] = [dict(id='other-case', title='Synthetic fixture',
            url='https://example.invalid/other', locator='Fixture section')]
        self.manifest['dataset_sha256'] = fingerprint(self.cases)
        self.record = blank()
        self.record.update(schema_version=2, case_id=self.cases[0]['id'],
            scope=self.cases[0]['scope'], dataset_sha256=self.manifest['dataset_sha256'])
        for group in ('control', 'risk'):
            for item in self.record[group].values():
                item['source_ids'] = []

    def answer(self, state='unknown', refs=None):
        self.record.update(reviewer_alias='FIXTURE ONLY', assessed_on='2000-01-01')
        self.record['control']['audit'].update(state=state,
            value=0 if state == 'rated' else None, confidence='unknown',
            rationale='Fixture only', evidence_note='Fixture only',
            source_ids=[] if refs is None else refs)

    def test_valid_sources_and_empty_citations_preserve_inputs(self):
        for state in ('unknown', 'rated'):
            for refs in ([], ['fixture']):
                self.answer(state, refs)
                before = copy.deepcopy((self.record, self.cases, self.manifest))
                counts = validate_response_dataset(self.record, self.cases, self.manifest)
                self.assertEqual(counts[state], 1)
                self.assertEqual((self.record, self.cases, self.manifest), before)

    def test_missing_or_other_case_reference_rejected(self):
        for ref in ('missing', 'other-case'):
            self.answer(refs=[ref])
            validate_response(self.record)  # Structure alone cannot resolve IDs.
            with self.assertRaisesRegex(ValueError, 'absent from selected case'):
                validate_response_dataset(self.record, self.cases, self.manifest)

    def test_malformed_duplicate_and_unanswered_references(self):
        for refs in (None, 'fixture', [1], [{}], [' '], ['fixture', 'fixture'], ['fixture']):
            self.record['control']['audit']['source_ids'] = refs
            with self.subTest(refs=refs), self.assertRaises(ValueError):
                validate_response(self.record)
        del self.record['control']['audit']['source_ids']
        with self.assertRaises(ValueError):
            validate_response(self.record)

    def test_v1_not_silently_upgraded(self):
        r = blank()
        self.assertEqual(validate_response(r)['unanswered'], 11)
        r['control']['audit']['source_ids'] = []
        with self.assertRaises(ValueError):
            validate_response(r)

    def test_cli_linkage_and_read_only(self):
        with tempfile.TemporaryDirectory() as folder:
            paths = [Path(folder)/name for name in ('r.json', 'd.json', 'm.json')]
            self.answer(refs=['fixture'])
            for path, obj in zip(paths, (self.record, self.cases, self.manifest)):
                path.write_text(json.dumps(obj))
            before = [p.read_bytes() for p in paths]
            base = [sys.executable, str(ROOT/'rating_response.py'), str(paths[0])]
            r = subprocess.run(base, capture_output=True, text=True)
            self.assertEqual(r.returncode, 0)
            self.assertIn('Source linkage not checked', r.stdout)
            r = subprocess.run(base+['--dataset', str(paths[1]), '--manifest', str(paths[2])],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn('source IDs match', r.stdout)
            self.assertEqual([p.read_bytes() for p in paths], before)
            self.assertEqual(len(list(Path(folder).iterdir())), 3)
