"""Readable evidence is a faithful view of supplied records, not validation."""
import copy
import json
from pathlib import Path
import unittest

from test_report_navigation import Document
from viewer import render_case_evidence, build_payload, render_dashboard


class EvidenceViewTests(unittest.TestCase):
    def setUp(self):
        self.cases = json.loads((Path(__file__).parents[1] / 'data/case_records.json').read_text())
        self.case = self.cases[0]

    def test_each_rating_retains_value_confidence_rationale_and_refs(self):
        self.case['control']['predict']['value'] = None
        before = copy.deepcopy(self.case)
        doc = Document(render_case_evidence(self.case))
        self.assertEqual(self.case, before)
        self.assertEqual(len(doc.tagged('table')), 2)
        rows = [n for n in doc.tagged('tr') if n['parent']['tag'] == 'tbody']
        ratings = list(self.case['control'].items()) + list(self.case['risk'].items())
        self.assertEqual(len(rows), len(ratings))
        for row, (dimension, rating) in zip(rows, ratings):
            cells = [n for n in doc.nodes if n['parent'] is row]
            self.assertEqual(cells[0]['attrs']['scope'], 'row')
            self.assertEqual([n['text'] for n in cells], [
                dimension, 'Unknown' if rating['value'] is None else str(rating['value']),
                rating['confidence'], rating['rationale'],
                ', '.join(rating['source_ids']) or 'No sources cited'])
        self.assertTrue(all(n['attrs'].get('scope') == 'col'
                            for n in doc.tagged('th') if n['parent']['parent']['tag'] == 'thead'))
        self.assertIn('No sources supplied.', ''.join(n['text'] for n in doc.tagged('p')))

    def test_catalog_displays_exact_supplied_sources_without_active_markup(self):
        # Fabricated fixture only; never added to the project dataset.
        self.case['sources'] = [{
            'id': 'fixture-"<id>', 'title': '<script>fixture</script>',
            'url': 'https://example.invalid/?q="<test>&x=1',
            'locator': 'Synthetic fixture <page> & "section"',
        }]
        self.case['control']['audit']['source_ids'] = ['fixture-"<id>']
        self.case['control']['audit']['rationale'] = '<img src=x onerror=alert(1)>'
        doc = Document(render_case_evidence(self.case))
        source = self.case['sources'][0]
        self.assertEqual(doc.tagged('dt')[0]['text'], source['id'] + ' — ' + source['title'])
        self.assertIn(source['url'], doc.tagged('dd')[0]['text'])
        self.assertIn(source['locator'], doc.tagged('dd')[0]['text'])
        self.assertFalse(doc.tagged('script'))
        self.assertFalse(doc.tagged('img'))
        self.assertFalse(doc.tagged('a'))
        self.assertIn(source['id'], doc.tagged('table')[0]['text'])

    def test_dashboard_includes_supplied_date_and_preserves_raw_record(self):
        payload = build_payload(self.cases)
        before = copy.deepcopy(payload)
        doc = Document(render_dashboard(payload))
        evidence_section = next(n for n in doc.tagged('section')
                                if n['attrs'].get('aria-labelledby') == 'evidence')
        details = [n for n in doc.tagged('details') if n['parent'] is evidence_section]
        for case, detail in zip(self.cases, details):
            self.assertIn(case['assessed_on'], detail['text'])
            self.assertIn('not independently verified', detail['text'])
            self.assertIn('unvalidated', detail['text'])
            raw = next(n for n in doc.tagged('pre') if n['parent'] is detail)
            self.assertEqual(json.loads(raw['text']),
                             {k: case[k] for k in ('sources', 'control', 'risk')})
        self.assertEqual(payload, before)

    def test_gaps_distinguish_unknown_from_uncited(self):
        # A source in the catalog only counts for ratings that actually cite it.
        self.case['sources'] = [dict(id='fixture', title='Fixture', locator='example',
                                     url='https://example.invalid/fixture')]
        for group in ('control', 'risk'):
            for item in self.case[group].values():
                item.update(value=0, source_ids=['fixture'])
        self.case['control']['audit']['value'] = None
        self.case['control']['predict']['source_ids'] = []
        self.case['risk']['propagation'].update(value=None, source_ids=[])
        doc = Document(render_dashboard(build_payload(self.cases)))
        lines = [n['text'] for n in doc.tagged('li')]
        self.assertEqual(lines[:4], [
            'Unknown rating (1 of 5): audit', 'No cited source (1 of 5): predict',
            'Unknown rating (1 of 6): propagation', 'No cited source (1 of 6): propagation'])

    def test_synthetic_example_gap_counts_and_empty_list(self):
        doc = Document(render_case_evidence(self.cases[2]))
        lines = [n['text'] for n in doc.tagged('li')]
        self.assertEqual(lines[0], 'Unknown rating (3 of 5): predict, override, audit')
        self.assertTrue(lines[1].startswith('No cited source (5 of 5):'))
        self.assertTrue(lines[2].startswith('Unknown rating (6 of 6):'))
        self.assertTrue(lines[3].startswith('No cited source (6 of 6):'))
        complete_ratings = Document(render_case_evidence(self.cases[0]))
        self.assertIn('Unknown rating (0 of 5): None',
                      [n['text'] for n in complete_ratings.tagged('li')])
