import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from case_io import export_cases, load_cases
from draft import apply_draft


ROOT = Path(__file__).parents[1]


class DraftTests(unittest.TestCase):
    def setUp(self):
        self.cases = load_cases(ROOT / 'data/case_records.json')
        self.before = copy.deepcopy(self.cases)
        self.changes = json.loads((ROOT / 'data/example_draft.json').read_text())
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.output = Path(self.temp.name) / 'drafted.json'

    def test_multiple_changes_and_audit(self):
        edited, audit = apply_draft(self.cases, self.changes)
        self.assertEqual(len(audit), 2)
        self.assertEqual(audit[0]['before']['value'], .1)
        self.assertEqual(audit[0]['after']['value'], .25)
        self.assertIsNone(audit[1]['after']['value'])
        self.assertEqual(edited[0]['control']['override']['value'], .25)

    def test_input_is_unchanged(self):
        apply_draft(self.cases, self.changes)
        self.assertEqual(self.cases, self.before)

    def test_duplicate_target_is_rejected(self):
        changes = self.changes + [copy.deepcopy(self.changes[0])]
        with self.assertRaisesRegex(ValueError, 'repeats target'):
            apply_draft(self.cases, changes)

    def test_exact_change_fields_are_required(self):
        for mutation in ('missing', 'extra'):
            changes = copy.deepcopy(self.changes)
            if mutation == 'missing':
                del changes[0]['confidence']
            else:
                changes[0]['note'] = 'not allowed'
            with self.assertRaisesRegex(ValueError, 'requires exactly'):
                apply_draft(self.cases, changes)

    def test_invalid_later_change_leaves_input_unchanged(self):
        changes = copy.deepcopy(self.changes)
        changes[1]['value'] = 4
        with self.assertRaises(ValueError):
            apply_draft(self.cases, changes)
        self.assertEqual(self.cases, self.before)

    def test_non_synthetic_case_is_rejected(self):
        cases = copy.deepcopy(self.cases)
        cases[0]['synthetic'] = False
        cases[0]['sources'] = [{'id': 's1', 'title': 'Source',
                                'url': 'https://example.org', 'locator': 'section 1'}]
        for rating in (*cases[0]['control'].values(), *cases[0]['risk'].values()):
            rating['source_ids'] = ['s1']
        with self.assertRaisesRegex(ValueError, 'limited to synthetic'):
            apply_draft(cases, [self.changes[0]])

    def test_preview_without_confirmation_writes_nothing(self):
        result = subprocess.run([
            sys.executable, str(ROOT / 'draft.py'), '--draft',
            str(ROOT / 'data/example_draft.json'), '--output', str(self.output)],
            capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Preview only', result.stdout)
        self.assertIn('"before"', result.stdout)
        self.assertFalse(self.output.exists())

    def test_confirmed_cli_exports_all_changes(self):
        result = subprocess.run([
            sys.executable, str(ROOT / 'draft.py'), '--draft',
            str(ROOT / 'data/example_draft.json'), '--output', str(self.output),
            '--confirm'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        loaded = load_cases(self.output)
        self.assertEqual(loaded[0]['control']['override']['value'], .25)
        self.assertIsNone(loaded[2]['risk']['civilian_exposure']['value'])
        self.assertTrue(all(case['synthetic'] for case in loaded))

    def test_existing_output_is_protected(self):
        edited, _ = apply_draft(self.cases, self.changes)
        self.output.write_text('preserve')
        with self.assertRaises(FileExistsError):
            export_cases(edited, self.output)
        self.assertEqual(self.output.read_text(), 'preserve')


if __name__ == '__main__':
    unittest.main()
