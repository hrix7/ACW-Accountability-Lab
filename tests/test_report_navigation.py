"""Structural regressions, not a substitute for assistive-technology review."""
import copy
from html.parser import HTMLParser
import json
from pathlib import Path
import unittest

from project import evaluate, render_report, RISK_FIELDS


class Document(HTMLParser):
    def __init__(self, markup):
        super().__init__()
        self.nodes = []
        self.stack = []
        self.feed(markup)

    def handle_starttag(self, tag, attrs):
        node = {'tag': tag, 'attrs': dict(attrs), 'text': '', 'parent': self.stack[-1] if self.stack else None}
        self.nodes.append(node)
        if tag not in ('meta',):
            self.stack.append(node)

    def handle_endtag(self, tag):
        if self.stack and self.stack[-1]['tag'] == tag:
            self.stack.pop()

    def handle_data(self, data):
        for node in self.stack:
            node['text'] += data

    def tagged(self, tag):
        return [node for node in self.nodes if node['tag'] == tag]


class ReportNavigationTests(unittest.TestCase):
    def setUp(self):
        self.cases = json.loads((Path(__file__).parents[1] / 'data/case_records.json').read_text())

    def render(self):
        self.report = {'results': [evaluate(case) for case in self.cases]}
        before = copy.deepcopy(self.report)
        doc = Document(render_report(self.report))
        self.assertEqual(before, self.report)
        return doc

    def test_navigation_resolves_and_labels_duplicate_titles(self):
        for case in self.cases:
            case['title'] = 'Same <title> & "quoted"'
        self.cases[0]['id'] = 'unsafe " <id>'
        doc = self.render()
        ids = [node['attrs']['id'] for node in doc.nodes if 'id' in node['attrs']]
        self.assertEqual(len(ids), len(set(ids)))
        targets = {node['attrs']['id']: node for node in doc.nodes if 'id' in node['attrs']}
        for link in doc.tagged('a'):
            target = targets[link['attrs']['href'][1:]]
            self.assertEqual(target['tag'], 'h2')
            self.assertEqual(target['attrs']['tabindex'], '-1')
        self.assertEqual(len(doc.tagged('main')), 1)
        self.assertEqual(len(doc.tagged('section')), len(self.cases))
        links = doc.tagged('a')[:len(self.cases)]
        for case, link in zip(self.cases, links):
            self.assertIn(case['id'], link['text'])
            self.assertIn(case['title'], link['text'])
        self.assertEqual(len(doc.tagged('title')), 1)

    def test_tables_have_case_captions_and_scoped_headers(self):
        self.cases[0]['risk']['autonomy']['value'] = None
        doc = self.render()
        for case, table in zip(self.cases, doc.tagged('table')):
            children = [node for node in doc.nodes if node['parent'] is table]
            self.assertEqual([node['tag'] for node in children], ['caption', 'thead', 'tbody'])
            self.assertIn(case['id'], children[0]['text'])
        headers = doc.tagged('th')
        self.assertEqual(sum(n['attrs'].get('scope') == 'col' for n in headers), 2 * len(self.cases))
        row_headers = [n for n in headers if n['attrs'].get('scope') == 'row']
        self.assertEqual([n['text'] for n in row_headers], list(RISK_FIELDS) * len(self.cases))
        self.assertIn('Unknown', doc.tagged('table')[0]['text'])

    def test_evidence_remains_complete_and_case_identifiable(self):
        doc = self.render()
        for result, detail in zip(self.report['results'], doc.tagged('details')):
            children = [n for n in doc.nodes if n['parent'] is detail]
            self.assertEqual([n['tag'] for n in children], ['summary', 'pre'])
            self.assertIn(result['id'], children[0]['text'])
            self.assertEqual(json.loads(children[1]['text']), result)
        self.assertIn('thresholds are unvalidated', ''.join(n['text'] for n in doc.tagged('p')))
        self.assertEqual(sum(n['text'] == 'Synthetic example' for n in doc.tagged('p')), len(self.cases))


class ComparisonNavigationTests(unittest.TestCase):
    def setUp(self):
        from compare import build_comparison
        from viewer import build_payload
        root = Path(__file__).parents[1]
        self.cases = json.loads((root / 'data/case_records.json').read_text())
        for case in self.cases:
            case['title'] = 'Shared <title> & "quoted"'
        self.cases[0]['id'] = 'unsafe "<id>'
        self.comparison = build_comparison(self.cases)
        self.payload = build_payload(self.cases)

    def assert_navigation(self, doc):
        ids = [node['attrs']['id'] for node in doc.nodes if 'id' in node['attrs']]
        self.assertEqual(len(ids), len(set(ids)))
        targets = {n['attrs']['id']: n for n in doc.nodes if 'id' in n['attrs']}
        for link in doc.tagged('a'):
            target = targets[link['attrs']['href'][1:]]
            self.assertIn(target['tag'], ('h2', 'main'))
            self.assertEqual(target['attrs']['tabindex'], '-1')
        self.assertEqual(len(doc.tagged('main')), 1)
        self.assertEqual(len(doc.tagged('title')), 1)
        return targets

    def test_comparison_table_navigation_and_case_identity(self):
        from compare import render_comparison
        before = copy.deepcopy(self.comparison)
        doc = Document(render_comparison(self.comparison))
        targets = self.assert_navigation(doc)
        self.assertEqual(self.comparison, before)
        tables = doc.tagged('table')
        self.assertEqual(len(tables), 3)
        for anchor, table in zip(('assessment-summary', 'human-control', 'risk-profile'), tables):
            # Each target heading is immediately followed by its table.
            heading_index = next(i for i, n in enumerate(doc.nodes) if n is targets[anchor])
            self.assertIs(doc.nodes[heading_index + 1], table)
            children = [n for n in doc.nodes if n['parent'] is table]
            self.assertEqual([n['tag'] for n in children], ['caption', 'thead', 'tbody'])
            self.assertTrue(children[0]['text'])
        case_headers = [n['text'] for n in doc.tagged('th') if n['attrs'].get('scope') == 'col']
        for case in self.cases:
            self.assertEqual(case_headers.count(f'{case["title"]} ({case["id"]})'), 3)
        self.assertIn('Unknown', tables[0]['text'])
        self.assertIn('unvalidated', targets['comparison']['text'])

    def test_viewer_comparison_target_precedes_tables_and_evidence(self):
        from viewer import render_dashboard
        before = copy.deepcopy(self.payload)
        doc = Document(render_dashboard(self.payload))
        targets = self.assert_navigation(doc)
        main = targets['comparison']
        self.assertEqual(main['tag'], 'main')
        # The old target was an empty div before evidence, with tables at the end.
        self.assertTrue(all(t['parent'] is main for t in doc.tagged('table')[:3]))
        sequence = [n['tag'] for n in doc.nodes if n['parent'] is main]
        self.assertLess(max(i for i, tag in enumerate(sequence) if tag == 'table'),
                        sequence.index('section'))
        self.assertIn('No draft loaded', targets['draft']['parent']['text'])
        self.assertEqual(self.payload, before)
        evidence = targets['evidence']['parent']
        details = [n for n in doc.tagged('details') if n['parent'] is evidence]
        self.assertEqual(len(details), len(self.cases))
        for case, detail in zip(self.cases, details):
            children = [n for n in doc.nodes if n['parent'] is detail]
            self.assertIn(case['id'], children[0]['text'])
            self.assertIn('Synthetic example', children[0]['text'])
            record = json.loads(children[-1]['text'])
            self.assertEqual(record, {k: case[k] for k in ('sources', 'control', 'risk')})

    def test_viewer_draft_target_contains_unchanged_audit(self):
        from viewer import build_payload, render_dashboard
        root = Path(__file__).parents[1]
        cases = json.loads((root / 'data/case_records.json').read_text())
        changes = json.loads((root / 'data/example_draft.json').read_text())
        payload = build_payload(cases, changes=changes)
        doc = Document(render_dashboard(payload))
        targets = self.assert_navigation(doc)
        section = targets['draft']['parent']
        audit = next(n for n in doc.tagged('pre') if n['parent'] is section)
        self.assertEqual(json.loads(audit['text']), payload['draft_audit'])
