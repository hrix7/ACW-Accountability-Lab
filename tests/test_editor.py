import copy
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from case_io import export_cases, load_cases
from editor import apply_rating_edit, edit_interactively, parse_value


ROOT = Path(__file__).parents[1]


class EditorTests(unittest.TestCase):
    def setUp(self):
        self.cases = load_cases(ROOT / 'data/case_records.json')
        self.before = copy.deepcopy(self.cases)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.output = Path(self.temp.name) / 'edited.json'

    def test_control_edit_preserves_input_and_evidence_links(self):
        edited = apply_rating_edit(self.cases, self.cases[0]['id'], 'control',
                                   'override', '0.75', 'Synthetic rationale', 'low')
        self.assertEqual(self.cases, self.before)
        self.assertEqual(edited[0]['control']['override']['value'], .75)
        self.assertEqual(edited[0]['control']['override']['source_ids'],
                         self.before[0]['control']['override']['source_ids'])

    def test_unknown_is_explicit_null(self):
        edited = apply_rating_edit(self.cases, self.cases[0]['id'], 'risk',
                                   'autonomy', 'unknown', 'Evidence unavailable', 'unknown')
        self.assertIsNone(edited[0]['risk']['autonomy']['value'])

    def test_value_validation(self):
        for group, value in (('control', '-.1'), ('control', 'nan'),
                             ('control', '1.1'), ('risk', '1.5'),
                             ('risk', '4'), ('other', '1')):
            with self.subTest(group=group, value=value), self.assertRaises(ValueError):
                parse_value(group, value)
        self.assertEqual(parse_value('risk', '+3'), 3)

    def test_non_synthetic_case_cannot_be_edited(self):
        cases = copy.deepcopy(self.cases)
        cases[0]['synthetic'] = False
        cases[0]['sources'] = [{'id': 's1', 'title': 'Source',
                                'url': 'https://example.org', 'locator': 'section 1'}]
        for rating in (*cases[0]['control'].values(), *cases[0]['risk'].values()):
            rating['source_ids'] = ['s1']
        with self.assertRaisesRegex(ValueError, 'limited to synthetic'):
            apply_rating_edit(cases, cases[0]['id'], 'control', 'audit', '.5',
                              'Would otherwise be valid', 'medium')

    def test_cancel_at_each_prompt_returns_no_changes(self):
        answers = [self.cases[0]['id'], 'control', 'audit', '.5',
                   'Synthetic rationale', 'medium']
        for stop in range(6):
            sequence = iter(answers[:stop] + ['cancel'])
            self.assertIsNone(edit_interactively(
                self.cases, lambda _: next(sequence), lambda _: None))
            self.assertEqual(self.cases, self.before)

    def test_unconfirmed_preview_returns_no_changes(self):
        answers = iter([self.cases[0]['id'], 'control', 'audit', '.5',
                        'Synthetic rationale', 'medium', 'no'])
        self.assertIsNone(edit_interactively(
            self.cases, lambda _: next(answers), lambda _: None))
        self.assertEqual(self.cases, self.before)

    def test_confirmed_edit_exports_valid_dataset(self):
        answers = iter([self.cases[0]['id'], 'risk', 'civilian_exposure', '2',
                        'Synthetic changed scenario', 'unknown', 'yes'])
        edited = edit_interactively(self.cases, lambda _: next(answers), lambda _: None)
        export_cases(edited, self.output)
        loaded = load_cases(self.output)
        self.assertEqual(loaded[0]['risk']['civilian_exposure']['value'], 2)
        self.assertTrue(loaded[0]['synthetic'])

    def test_existing_output_is_never_overwritten(self):
        self.output.write_text('keep this')
        with self.assertRaises(FileExistsError):
            export_cases(self.cases, self.output)
        self.assertEqual(self.output.read_text(), 'keep this')

    def test_empty_rationale_and_bad_confidence_are_rejected(self):
        for rationale, confidence in (('', 'low'), ('valid', 'certain')):
            with self.assertRaises(ValueError):
                apply_rating_edit(self.cases, self.cases[0]['id'], 'control',
                                  'understand', '.5', rationale, confidence)

    def test_cli_confirm_and_cancel(self):
        confirmed = '\n'.join([self.cases[0]['id'], 'control', 'override', '.55',
                               'Synthetic CLI verification', 'unknown', 'yes', ''])
        result = subprocess.run([sys.executable, str(ROOT / 'editor.py'), '--input',
                                 str(ROOT / 'data/case_records.json'), '--output',
                                 str(self.output)], input=confirmed,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(load_cases(self.output)[0]['control']['override']['value'], .55)
        cancelled = Path(self.temp.name) / 'cancelled.json'
        result = subprocess.run([sys.executable, str(ROOT / 'editor.py'), '--output',
                                 str(cancelled)], input='cancel\n',
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(cancelled.exists())


if __name__ == '__main__':
    unittest.main()
