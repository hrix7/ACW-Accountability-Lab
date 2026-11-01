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
