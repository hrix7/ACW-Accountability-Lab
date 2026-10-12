import unittest
import random
from mhc import DIMENSIONS, DEFAULT_WEIGHTS, score, formula_threshold, sensitivity, assess

class ModelTests(unittest.TestCase):
    def test_known_calculation(self):
        self.assertAlmostEqual(score(dict(zip(DIMENSIONS, (.4,.3,.1,.2,.2)))), .245)
    def test_reject_bad_inputs(self):
        for value in (-.1, 1.1, float('nan'), float('inf'), True, '0.5'):
            with self.assertRaises(ValueError):
                score(dict.fromkeys(DIMENSIONS, value))
        with self.assertRaises(ValueError):
            score(dict.fromkeys(DIMENSIONS, .5), dict.fromkeys(DIMENSIONS, .1))
    def test_missing_is_not_zero(self):
        result = assess({'id':'unknown','scores':dict.fromkeys(DIMENSIONS, None)}, .87)
        self.assertEqual(result['status'], 'insufficient_evidence')
        self.assertNotIn('mhc', result)
    def test_threshold_discrepancy(self):
        self.assertAlmostEqual(formula_threshold(1), 14/15)
        self.assertGreater(formula_threshold(1), .87)
    def test_average_does_not_guarantee_component_floor(self):
        values = dict.fromkeys(DIMENSIONS, 1)
        values['override'] = .8
        self.assertGreater(score(values), formula_threshold(1))
        self.assertLess(values['override'], 14/15)
    def test_simplex_bounds_and_sensitivity_bound(self):
        rng = random.Random(20261011)
        for _ in range(500):
            values = {key:rng.random() for key in DIMENSIONS}
            raw = [rng.expovariate(1) for _ in DIMENSIONS]
            weighting = dict(zip(DIMENSIONS, (x/sum(raw) for x in raw)))
            result = score(values, weighting)
            self.assertTrue(min(values.values()) <= result <= max(values.values()))
            bound = .5 * sum(abs(weighting[k]-DEFAULT_WEIGHTS[k]) for k in DIMENSIONS) * (max(values.values())-min(values.values()))
            self.assertLessEqual(abs(result-score(values)), bound+1e-12)
    def test_sweep_baseline(self):
        values = dict(zip(DIMENSIONS, (.4,.3,.1,.2,.2)))
        self.assertAlmostEqual(sensitivity(values)[3]['mhc'], score(values))
    def test_boundary_is_inclusive(self):
        values = dict.fromkeys(DIMENSIONS, 1)
        self.assertEqual(assess({'id':'edge','scores':values},1)['comparison'], 'at_or_above_design_threshold')

if __name__ == '__main__':
    unittest.main()
