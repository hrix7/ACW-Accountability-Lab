"""HTML regression checks using fabricated software fixtures only."""
import copy
from html.parser import HTMLParser
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from response_compare import compare_responses
from response_report import render_html
from response_template import build_template
from strict_json import load_json

ROOT = Path(__file__).resolve().parents[1]


class Structure(HTMLParser):
    def __init__(self, content):
        super().__init__()
        self.ids, self.links, self.tags = [], [], []
        self.feed(content)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.tags.append((tag, attrs))
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        if tag == 'a':
            self.links.append(attrs['href'])


class ResponseReportTests(unittest.TestCase):
    def setUp(self):
        self.cases = load_json(ROOT / 'data/case_records.json')
        self.manifest = load_json(ROOT / 'data/synthetic_manifest.json')
        self.left = build_template(self.cases, self.manifest, self.cases[0]['id'],
                                   '0' * 40, 'Synthetic fixture only')
        self.right = copy.deepcopy(self.left)

    def report(self):
        return compare_responses(self.left, self.right, self.cases, self.manifest)

    def test_navigation_and_table_structure(self):
        html = render_html(self.report())
        parsed = Structure(html)
        self.assertEqual(len(parsed.ids), len(set(parsed.ids)))
        self.assertEqual(len(parsed.links), 12)
        for link in parsed.links:
            self.assertTrue(link.startswith('#'))
            self.assertIn(link[1:], parsed.ids)
        for tag, attrs in parsed.tags:
            if tag == 'th':
                self.assertIn(attrs.get('scope'), ('row', 'col'))
        self.assertEqual(sum(tag == 'table' for tag, _ in parsed.tags), 14)
        self.assertEqual(sum(tag == 'caption' for tag, _ in parsed.tags), 14)
        self.assertNotIn('<script', html)
        self.assertIn('Thresholds remain unvalidated', html)

    def test_escaping_and_input_preservation(self):
        payload = '<script>alert("fixture")</script>&'
        self.left['exposure'] = payload
        result = self.report()
        before = copy.deepcopy(result)
        html = render_html(result)
        self.assertNotIn(payload, html)
        self.assertIn('&lt;script&gt;alert(&quot;fixture&quot;)&lt;/script&gt;&amp;', html)
        self.assertEqual(result, before)

    def test_states_zero_and_v1_citations(self):
        self.left['schema_version'] = 1
        for group in ('control', 'risk'):
            for item in self.left[group].values():
                del item['source_ids']
        for record, state, value in ((self.left, 'unknown', None), (self.right, 'rated', 0)):
            record.update(reviewer_alias='fixture', assessed_on='2000-01-01')
            record['control']['understand'].update(state=state, value=value,
                confidence='unknown', rationale='Fixture rationale', evidence_note='Fixture only')
        html = render_html(self.report())
        for text in ('<td>Unknown</td>', '<td>Unanswered</td>', '<td>0</td>',
                     'Unknown Vs Rated', 'Not available (schema v1)',
                     'None supplied', 'Fixture rationale', 'Not checked (schema v1)'):
            self.assertIn(text, html)

    def test_cli_html_and_invalid_input_read_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            for name, value in (('left', self.left), ('right', self.right),
                                ('cases', self.cases), ('manifest', self.manifest)):
                (folder / (name + '.json')).write_text(json.dumps(value))
            command = [sys.executable, str(ROOT / 'response_compare.py'), 'left.json',
                'right.json', '--dataset', 'cases.json', '--manifest', 'manifest.json',
                '--format', 'html']
            before = {p.name: p.read_bytes() for p in folder.iterdir()}
            run = subprocess.run(command, cwd=tmp, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(run.stdout.rstrip(), render_html(self.report()))
            self.assertEqual(before, {p.name: p.read_bytes() for p in folder.iterdir()})
            self.right['repository_commit'] = '1' * 40
            (folder / 'right.json').write_text(json.dumps(self.right))
            run = subprocess.run(command, cwd=tmp, capture_output=True, text=True)
            self.assertEqual(run.returncode, 2)
            self.assertEqual(run.stdout, '')
