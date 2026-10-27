import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from compare import build_comparison, render_comparison
from provenance import build_provenance, fingerprint

ROOT = Path(__file__).parents[1]


class ProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.cases = json.loads((ROOT / 'data/case_records.json').read_text())
        self.config = json.loads((ROOT / 'data/example_config.json').read_text())

    def test_fingerprint_ignores_object_order_and_json_whitespace(self):
        self.assertEqual(fingerprint({'a': None, 'b': 2}),
                         fingerprint(json.loads('{ "b": 2, "a": null }')))
        self.assertEqual(fingerprint(None),
                         '74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b')

    def test_dataset_change_or_reordering_changes_fingerprint(self):
        before = fingerprint(self.cases)
        self.assertNotEqual(before, fingerprint(list(reversed(self.cases))))
        changed = copy.deepcopy(self.cases)
        changed[0]['control']['predict']['value'] = None
        self.assertNotEqual(before, fingerprint(changed))

    def test_defaults_are_explicit_without_approval_threshold(self):
        result = build_provenance(self.cases)
        self.assertIsNone(result['effective_config']['threshold'])
        self.assertEqual(result['effective_config']['floors'], {})
        self.assertAlmostEqual(sum(result['effective_config']['weights'].values()), 1)
        self.assertIn('unvalidated', result['notice'])

    def test_effective_config_preserved_without_aliasing(self):
        original = copy.deepcopy(self.config)
        result = build_comparison(self.cases, self.config)
        metadata = result['provenance']
        self.assertEqual(metadata['effective_config']['floors'], self.config['floors'])
        self.assertEqual(metadata['effective_config']['threshold'], self.config['threshold'])
        self.assertNotEqual(metadata['supplied_config_sha256'], fingerprint({}))
        metadata['effective_config']['floors'].clear()
        self.assertEqual(self.config, original)

    def test_nonfinite_fingerprints_rejected(self):
        for value in (float('nan'), float('inf'), float('-inf')):
            with self.assertRaises(ValueError):
                fingerprint(value)

    def test_cli_reports_share_metadata_in_json_and_html(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            for configured in (False, True):
                reports = []
                for script in ('project.py', 'compare.py'):
                    target = output / (script + '.json')
                    page = output / (script + '.html')
                    command = [sys.executable, str(ROOT / script), '--output',
                               str(target), '--html', str(page)]
                    if configured:
                        command += ['--config', str(ROOT / 'data/example_config.json')]
                    subprocess.run(command, check=True, capture_output=True, text=True)
                    report = json.loads(target.read_text())
                    reports.append(report['provenance'])
                    self.assertIn(report['provenance']['dataset_sha256'], page.read_text())
                    self.assertIn('Reproducibility metadata', page.read_text())
                self.assertEqual(reports[0], reports[1])
                self.assertEqual(reports[0]['dataset_sha256'], fingerprint(self.cases))

    def test_html_metadata_escaped(self):
        result = build_comparison(self.cases)
        result['provenance']['notice'] = '<script>bad</script>'
        page = render_comparison(result)
        self.assertNotIn('<script>', page)
        self.assertIn('&lt;script&gt;', page)


if __name__ == '__main__':
    unittest.main()
