import copy
import json
from pathlib import Path
import unittest

from compare import build_comparison, render_comparison


ROOT = Path(__file__).parents[1]


class ComparisonTests(unittest.TestCase):
    def setUp(self):
        self.cases = json.loads((ROOT / 'data/case_records.json').read_text())
        self.before = copy.deepcopy(self.cases)

    def test_requires_two_cases(self):
        with self.assertRaises(ValueError):
            build_comparison(self.cases[:1])

    def test_preserves_inputs_and_synthetic_labels(self):
        result = build_comparison(self.cases)
        self.assertEqual(self.cases, self.before)
        self.assertTrue(all(case['synthetic'] for case in result['cases']))

    def test_control_difference_uses_first_case_only_when_known(self):
        result = build_comparison(self.cases[:2])
        row = next(row for row in result['control_dimensions'] if row['dimension'] == 'understand')
        self.assertAlmostEqual(row['difference_from_first'][0], 0)
        self.assertAlmostEqual(row['difference_from_first'][1], .5)

    def test_unknown_control_has_no_score_or_delta(self):
        result = build_comparison([self.cases[2], self.cases[0]])
        first = result['cases'][0]
        self.assertEqual(first['status'], 'insufficient_evidence')
        self.assertIsNone(first['control_score'])
        row = next(row for row in result['control_dimensions'] if row['dimension'] == 'predict')
        self.assertIsNone(row['values'][0])
        self.assertEqual(row['difference_from_first'], [None, None])

    def test_risk_remains_dimension_level_not_aggregated(self):
        result = build_comparison(self.cases)
        self.assertNotIn('risk_score', result)
        self.assertNotIn('risk_score', result['cases'][0])
        self.assertEqual(len(result['risk_dimensions']), 6)
        self.assertIn('not aggregated', result['notice'])

    def test_configured_threshold_is_marked_as_comparison(self):
        config = json.loads((ROOT / 'data/example_config.json').read_text())
        result = build_comparison(self.cases[:2], config)
        self.assertIn(result['cases'][0]['threshold_comparison'],
                      ('at_or_above_design_threshold', 'below_design_threshold'))
        self.assertIn('unvalidated', result['notice'])

    def test_duplicate_case_ids_rejected(self):
        with self.assertRaisesRegex(ValueError, 'unique'):
            build_comparison([self.cases[0], copy.deepcopy(self.cases[0])])

    def test_html_escapes_titles_and_marks_unknown(self):
        self.cases[0]['title'] = '<script>alert(1)</script>'
        self.cases[0]['control']['predict']['value'] = None
        page = render_comparison(build_comparison(self.cases[:2]))
        self.assertNotIn('<script>', page)
        self.assertIn('&lt;script&gt;', page)
        self.assertIn('Unknown', page)
        self.assertIn('scope="col"', page)


if __name__ == '__main__':
    unittest.main()
