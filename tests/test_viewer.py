import copy
import json
from http.server import ThreadingHTTPServer
from pathlib import Path
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from case_io import load_cases
from strict_json import load_json
from viewer import build_payload, make_handler, render_dashboard, validate_host


ROOT = Path(__file__).parents[1]


class ViewerTests(unittest.TestCase):
    def setUp(self):
        self.cases = load_cases(ROOT / 'data/case_records.json')
        self.before = copy.deepcopy(self.cases)
        self.payload = build_payload(
            self.cases, changes=load_json(ROOT / 'data/example_draft.json'))
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), make_handler(self.payload))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.base = f'http://127.0.0.1:{self.server.server_port}'

    def fetch(self, path, method='GET'):
        return urlopen(Request(self.base + path, method=method), timeout=2)

    def test_payload_preserves_inputs_synthetic_labels_and_unknowns(self):
        self.assertEqual(self.cases, self.before)
        self.assertTrue(all(case['synthetic'] for case in self.payload['cases']))
        self.assertIsNone(self.payload['cases'][2]['control']['predict']['value'])

    def test_draft_audit_is_read_only_preview(self):
        self.assertEqual(len(self.payload['draft_audit']), 2)
        self.assertEqual(self.payload['draft_audit'][0]['before']['value'], .1)
        self.assertEqual(self.cases, self.before)

    def test_dashboard_escapes_case_content(self):
        cases = copy.deepcopy(self.cases)
        cases[0]['title'] = '<script>alert(1)</script>'
        page = render_dashboard(build_payload(cases))
        self.assertNotIn('<script>', page)
        self.assertIn('&lt;script&gt;', page)
        self.assertIn('Evidence records', page)

    def test_root_has_security_headers_and_evidence(self):
        with self.fetch('/') as response:
            page = response.read().decode()
            self.assertEqual(response.status, 200)
            self.assertIn("default-src 'none'", response.headers['Content-Security-Policy'])
            self.assertEqual(response.headers['Cache-Control'], 'no-store')
            self.assertIn('Draft audit', page)

    def test_cases_api_preserves_unknown(self):
        with self.fetch('/api/cases') as response:
            cases = json.loads(response.read())
            self.assertIsNone(cases[2]['control']['predict']['value'])

    def test_comparison_api_has_no_aggregate_risk_score(self):
        with self.fetch('/api/comparison') as response:
            comparison = json.loads(response.read())
            self.assertNotIn('risk_score', comparison)
            self.assertEqual(len(comparison['risk_dimensions']), 6)

    def test_draft_api_returns_audit_not_edited_dataset(self):
        with self.fetch('/api/draft') as response:
            audit = json.loads(response.read())
            self.assertEqual(audit[0]['case_id'], 'synthetic-limited-control')
            self.assertIn('before', audit[0])
            self.assertIn('after', audit[0])

    def test_mutation_methods_are_rejected(self):
        for method in ('POST', 'PUT', 'PATCH', 'DELETE'):
            with self.subTest(method=method), self.assertRaises(HTTPError) as caught:
                self.fetch('/api/cases', method)
            self.assertEqual(caught.exception.code, 405)
        self.assertEqual(self.cases, self.before)

    def test_unknown_path_is_404(self):
        with self.assertRaises(HTTPError) as caught:
            self.fetch('/unknown')
        self.assertEqual(caught.exception.code, 404)

    def test_only_loopback_hosts_are_allowed(self):
        for host in ('127.0.0.1', 'localhost', '::1'):
            self.assertEqual(validate_host(host), host)
        for host in ('0.0.0.0', '192.168.1.5', 'example.org'):
            with self.assertRaises(ValueError):
                validate_host(host)


if __name__ == '__main__':
    unittest.main()
