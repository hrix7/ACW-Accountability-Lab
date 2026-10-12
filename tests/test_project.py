import copy
import json
from pathlib import Path
import unittest
from project import evaluate, render_report

class ProjectTests(unittest.TestCase):
    def setUp(self):
        self.case = json.loads((Path(__file__).parents[1]/'data/case_records.json').read_text())[0]
    def test_no_implicit_threshold(self):
        self.assertEqual(evaluate(self.case)['comparison'], 'not_requested')
    def test_unknown_bounds(self):
        self.case['control']['override']['value'] = None
        result = evaluate(self.case)
        self.assertNotIn('control_score',result)
        self.assertAlmostEqual(result['missing_evidence_bounds'][1]-result['missing_evidence_bounds'][0],.3)
    def test_floors_cannot_be_masked_by_average(self):
        for rating in self.case['control'].values(): rating['value']=1
        self.case['control']['override']['value']=.5
        result=evaluate(self.case,threshold=.8,floors={'override':.9})
        self.assertEqual(result['comparison'],'at_or_above_design_threshold')
        self.assertEqual(result['component_floors']['override'],'below_floor')
    def test_non_synthetic_requires_evidence(self):
        self.case['synthetic']=False
        with self.assertRaises(ValueError): evaluate(self.case)
    def test_dangling_source(self):
        self.case['control']['audit']['source_ids']=['missing']
        with self.assertRaises(ValueError): evaluate(self.case)
    def test_ordinal_validation(self):
        for invalid in (True, .4, 4, -1, '2'):
            self.case['risk']['autonomy']['value']=invalid
            with self.assertRaises(ValueError): evaluate(self.case)
    def test_html_escapes_untrusted_text(self):
        self.case['title']='<script>alert(1)</script>'
        report=render_report({'results':[evaluate(self.case)]})
        self.assertNotIn('<script>',report)
        self.assertIn('&lt;script&gt;',report)
    def test_unknown_floor(self):
        self.case['control']['time']['value']=None
        self.assertEqual(evaluate(self.case,floors={'time':.7})['component_floors']['time'],'unknown')
    def test_known_score_inside_bounds(self):
        result=evaluate(self.case)
        for bound in result['missing_evidence_bounds']:
            self.assertAlmostEqual(bound,result['control_score'])

if __name__=='__main__': unittest.main()
