"""Loopback-only, read-only browser viewer for ACW research records."""
import argparse
import html
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from case_io import load_cases
from compare import build_comparison, render_comparison
from draft import apply_draft
from strict_json import load_json


LOOPBACK_HOSTS = {'127.0.0.1', 'localhost', '::1'}


def validate_host(host):
    if host not in LOOPBACK_HOSTS:
        raise ValueError('Viewer host must be loopback: 127.0.0.1, localhost, or ::1')
    return host


def build_payload(cases, config=None, changes=None):
    comparison = build_comparison(cases, config)
    audit = None
    if changes is not None:
        _, audit = apply_draft(cases, changes)
    return {
        'notice': ('Read-only local view. Sources are supplied, not independently '
                   'verified; weights, floors and thresholds are unvalidated.'),
        'cases': cases,
        'comparison': comparison,
        'draft_audit': audit,
    }


def render_dashboard(payload):
    esc = lambda value: html.escape(str(value), quote=True)
    evidence = []
    for case in payload['cases']:
        label = 'Synthetic example' if case['synthetic'] else 'Evidence supplied; not independently verified'
        evidence_record = {
            'sources': case['sources'],
            'control': case['control'],
            'risk': case['risk'],
        }
        evidence.append(
            f'<details><summary>{esc(case["title"])} — {esc(label)}</summary>'
            f'<p><strong>Scope:</strong> {esc(case["scope"])}</p>'
            f'<pre>{esc(json.dumps(evidence_record, indent=2, ensure_ascii=False))}'
            '</pre></details>')
    if payload['draft_audit'] is None:
        draft = '<p>No draft loaded. Start with <code>--draft data/example_draft.json</code> to preview one.</p>'
    else:
        draft = f'<pre>{esc(json.dumps(payload["draft_audit"], indent=2, ensure_ascii=False))}</pre>'
    additions = (
        '<nav aria-label="Viewer sections"><a href="#comparison">Comparison</a> · '
        '<a href="#evidence">Evidence</a> · <a href="#draft">Draft audit</a></nav>'
        '<section id="evidence"><h2>Evidence records</h2>' + ''.join(evidence) + '</section>'
        '<section id="draft"><h2>Draft audit</h2>' + draft + '</section>'
        '<footer><p>Read-only local viewer; no write endpoint is available.</p></footer>')
    page = render_comparison(payload['comparison'])
    page = page.replace('<h1>ACW case comparison</h1>',
                        '<h1>ACW Accountability Lab viewer</h1><div id="comparison"></div>' + additions)
    return page


def make_handler(payload):
    html_page = render_dashboard(payload).encode('utf-8')
    json_pages = {
        '/api/cases': json.dumps(payload['cases'], indent=2, ensure_ascii=False,
                                 allow_nan=False).encode('utf-8'),
        '/api/comparison': json.dumps(payload['comparison'], indent=2,
                                      ensure_ascii=False, allow_nan=False).encode('utf-8'),
        '/api/draft': json.dumps(payload['draft_audit'], indent=2,
                                 ensure_ascii=False, allow_nan=False).encode('utf-8'),
    }

    class ReadOnlyHandler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            return

        def send_content(self, status, content_type, body=b''):
            self.send_response(status)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Security-Policy',
                             "default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; frame-ancestors 'none'")
            self.end_headers()
            if self.command != 'HEAD':
                self.wfile.write(body)

        def do_GET(self):
            path = urlsplit(self.path).path
            if path == '/':
                self.send_content(200, 'text/html; charset=utf-8', html_page)
            elif path in json_pages:
                self.send_content(200, 'application/json; charset=utf-8', json_pages[path])
            elif path == '/favicon.ico':
                self.send_content(204, 'image/x-icon')
            else:
                self.send_content(404, 'text/plain; charset=utf-8', b'Not found\n')

        def do_HEAD(self):
            self.do_GET()

        def mutation_not_allowed(self):
            self.send_response(405)
            self.send_header('Allow', 'GET, HEAD')
            self.send_header('Content-Length', '0')
            self.end_headers()

        do_POST = mutation_not_allowed
        do_PUT = mutation_not_allowed
        do_PATCH = mutation_not_allowed
        do_DELETE = mutation_not_allowed

    return ReadOnlyHandler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path,
                        default=Path(__file__).parent / 'data/case_records.json')
    parser.add_argument('--config', type=Path)
    parser.add_argument('--draft', type=Path)
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--check', action='store_true',
                        help='Validate and render in memory, then exit without serving')
    args = parser.parse_args()
    try:
        validate_host(args.host)
        if not 0 <= args.port <= 65535:
            raise ValueError('Port must be between 0 and 65535')
        payload = build_payload(
            load_cases(args.input),
            load_json(args.config) if args.config else None,
            load_json(args.draft) if args.draft else None)
        render_dashboard(payload)
        if args.check:
            print(f'Viewer check passed for {len(payload["cases"])} cases; no server started.')
            return
        server = ThreadingHTTPServer((args.host, args.port), make_handler(payload))
        print(f'Read-only viewer: http://{args.host}:{server.server_port} (Ctrl+C to stop)')
        server.serve_forever()
    except (ValueError, KeyError, TypeError, AttributeError, OSError) as error:
        parser.error(str(error))


if __name__ == '__main__':
    main()
