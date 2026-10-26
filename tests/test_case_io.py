import copy
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from case_io import export_cases, load_cases, validate_cases
from strict_json import load_json


ROOT = Path(__file__).parents[1]


class CaseIOTests(unittest.TestCase):
    def setUp(self):
        self.cases = load_cases(ROOT / 'data/case_records.json')
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'cases.json'

    def test_round_trip_preserves_fields_unknowns_and_unicode(self):
        self.cases[0]['control']['override']['value'] = None
        self.cases[0]['risk']['autonomy']['value'] = None
        self.cases[0]['title'] = 'Synthetic – café'
        self.cases[0]['sources'] = [{'id': 's1', 'title': 'Synthetic source',
                                    'url': 'https://example.org', 'locator': 'Invented §1'}]
        self.cases[0]['control']['audit']['source_ids'] = ['s1']
        before = copy.deepcopy(self.cases)
        export_cases(self.cases, self.path)
        self.assertEqual(load_cases(self.path), before)
        self.assertEqual(self.cases, before)

    def test_existing_file_is_unchanged(self):
        self.path.write_text('existing data')
        with self.assertRaises(FileExistsError):
            export_cases(self.cases, self.path)
        self.assertEqual(self.path.read_text(), 'existing data')

    def test_same_input_output_is_unchanged(self):
        export_cases(self.cases, self.path)
        before = self.path.read_bytes()
        with self.assertRaises(FileExistsError):
            export_cases(load_cases(self.path), self.path)
        self.assertEqual(self.path.read_bytes(), before)

    def test_symlink_destination_does_not_replace_target(self):
        target = Path(self.temp.name) / 'target.json'
        target.write_text('original')
        self.path.symlink_to(target)
        with self.assertRaises(FileExistsError):
            export_cases(self.cases, self.path)
        self.assertEqual(target.read_text(), 'original')

    def test_duplicate_json_keys_are_rejected_at_any_depth(self):
        for content in ('{"x": 1, "x": 2}', '[{"nested": {"value": null, "value": 1}}]'):
            self.path.write_text(content)
            with self.assertRaisesRegex(ValueError, 'Duplicate JSON key'):
                load_json(self.path)

    def test_nonfinite_numbers_are_rejected(self):
        for number in ('NaN', 'Infinity', '-Infinity', '1e9999'):
            self.path.write_text('{"metadata": ' + number + '}')
            with self.assertRaisesRegex(ValueError, 'Non-finite'):
                load_json(self.path)

    def test_invalid_top_level(self):
        for value in ([], {}, None, 'cases', [None]):
            with self.assertRaises(ValueError):
                validate_cases(value)

    def test_duplicate_case_ids(self):
        with self.assertRaisesRegex(ValueError, 'Case IDs must be unique'):
            validate_cases([self.cases[0], copy.deepcopy(self.cases[0])])

    def test_missing_value_is_not_silently_treated_as_unknown(self):
        for group, dimension in (('control', 'override'), ('risk', 'autonomy')):
            cases = copy.deepcopy(self.cases)
            del cases[0][group][dimension]['value']
            with self.assertRaisesRegex(ValueError, 'explicit value'):
                export_cases(cases, self.path)
            self.assertFalse(self.path.exists())

    def test_malformed_source_object(self):
        for source in (None, [], 'source'):
            cases = copy.deepcopy(self.cases)
            cases[0]['sources'] = [source]
            with self.assertRaisesRegex(ValueError, 'source must be an object'):
                validate_cases(cases)

    def test_dangling_reference_creates_no_output(self):
        self.cases[0]['control']['audit']['source_ids'] = ['absent']
        with self.assertRaises(ValueError):
            export_cases(self.cases, self.path)
        self.assertFalse(self.path.exists())

    def test_non_synthetic_unbacked_rating_creates_no_output(self):
        self.cases[0]['synthetic'] = False
        with self.assertRaises(ValueError):
            export_cases(self.cases, self.path)
        self.assertFalse(self.path.exists())

    def test_cli_validation_and_export(self):
        result = subprocess.run([sys.executable, str(ROOT / 'case_io.py'), '--input',
                                 str(ROOT / 'data/case_records.json'), '--output', str(self.path)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(load_cases(self.path), self.cases)
        result = subprocess.run([sys.executable, str(ROOT / 'case_io.py'), '--input',
                                 str(self.path), '--output', str(self.path)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(load_cases(self.path), self.cases)

    def test_assessment_and_comparison_reject_ambiguous_config(self):
        self.path.write_text('{"threshold": 0.8, "threshold": 0.9}')
        for script in ('project.py', 'compare.py'):
            output = Path(self.temp.name) / f'{script}.json'
            result = subprocess.run([sys.executable, str(ROOT / script), '--config',
                                     str(self.path), '--output', str(output)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn('Duplicate JSON key', result.stderr)
            self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()
