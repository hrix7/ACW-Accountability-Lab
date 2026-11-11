"""HTML presentation for validated synthetic response comparisons."""
from html import escape


def shown(value):
    return 'Not supplied' if value is None else escape(str(value))


def render_html(result):
    """Render compare_responses output; callers must validate inputs first."""
    parts = ['''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>Synthetic response comparison</title><style>
body{font:1rem/1.6 system-ui,sans-serif;color:#222;background:#fff;margin:auto;padding:1.5rem;max-width:75rem}
a{color:#64284b}a:focus-visible{outline:3px solid #64284b;outline-offset:3px}
table{border-collapse:collapse;width:100%;margin:1rem 0}th,td{border:1px solid #777;padding:.6rem;text-align:left;vertical-align:top;overflow-wrap:anywhere}
caption{text-align:left;font-weight:bold}th{background:#f4edf1}td,dd{white-space:pre-wrap;overflow-wrap:anywhere}dt{font-weight:bold}dd{margin:0 0 .7rem}
section{margin-top:2rem}nav li{display:inline-block;margin-right:1rem}h2,h3{scroll-margin-top:1rem}
</style></head><body><a href="#main">Skip to comparison</a><main id="main">
<h1>Synthetic response comparison</h1>''']
    parts.append('<p>' + shown(result['limitations']) + '</p>')
    parts.append('<p>Left and right follow input order. Supplied metadata is not authenticated. '
                 'Keep responses and this report outside the public checkout.</p><dl>')
    for key in ('case_id', 'scope', 'dataset_sha256', 'repository_commit'):
        parts.append(f'<dt>{key.replace("_", " ").title()}</dt><dd>{shown(result[key])}</dd>')
    parts.append('</dl><table><caption>Supplied response metadata</caption><thead><tr>'
                 '<th scope="col">Field</th><th scope="col">Left</th><th scope="col">Right</th>'
                 '</tr></thead><tbody>')
    for key in ('schema_version', 'reviewer_alias', 'assessed_on', 'exposure'):
        parts.append(f'<tr><th scope="row">{key.replace("_", " ").title()}</th>' +
                     ''.join(f'<td>{shown(result["responses"][side][key])}</td>'
                             for side in ('left', 'right')) + '</tr>')
    parts.append('<tr><th scope="row">Source catalog linkage</th>' + ''.join(
        '<td>' + ('Checked; source truth unverified' if result['source_linkage_checked'][side]
                   else 'Not checked (schema v1)') + '</td>' for side in ('left', 'right')) +
        '</tr></tbody></table><nav aria-label="Comparison dimensions"><ul>')
    for group in ('control', 'risk'):
        for index, row in enumerate(result[group]['rows']):
            parts.append(f'<li><a href="#{group}-{index}">{group.title()}: '
                         f'{shown(row["dimension"].replace("_", " "))}</a></li>')
    parts.append('</ul></nav>')
    for group in ('control', 'risk'):
        parts.append(f'<section><h2>{group.title()} dimensions</h2><table>'
                     f'<caption>{group.title()} state/value counts (not an agreement score)</caption>'
                     '<thead><tr><th scope="col">Category</th><th scope="col">Count</th>'
                     '</tr></thead><tbody>')
        for status, count in result[group]['counts'].items():
            parts.append(f'<tr><th scope="row">{shown(status.replace("_", " ").title())}</th>'
                         f'<td>{count}</td></tr>')
        parts.append('</tbody></table>')
        for index, row in enumerate(result[group]['rows']):
            label = group.title() + ': ' + row['dimension'].replace('_', ' ')
            parts.append(f'<h3 id="{group}-{index}">{shown(label)}</h3>'
                         f'<p>Comparison: <strong>{shown(row["status"].replace("_", " ").title())}</strong></p>'
                         f'<table><caption>{shown(label)} supplied responses</caption><thead><tr>'
                         '<th scope="col">Field</th><th scope="col">Left</th>'
                         '<th scope="col">Right</th></tr></thead><tbody>')
            for field in ('state', 'value', 'confidence', 'rationale', 'evidence_note', 'source_ids'):
                parts.append(f'<tr><th scope="row">{field.replace("_", " ").title()}</th>')
                for side in ('left', 'right'):
                    item = row[side]
                    if field == 'source_ids':
                        value = ('Not available (schema v1)' if field not in item else
                                 ', '.join(item[field]) if item[field] else 'None supplied')
                    elif field == 'value' and item['state'] != 'rated':
                        value = 'Unanswered' if item['state'] == 'unanswered' else 'Unknown'
                    else:
                        value = item[field]
                    parts.append(f'<td>{shown(value)}</td>')
                parts.append('</tr>')
            parts.append('</tbody></table>')
        parts.append('</section>')
    parts.append('</main></body></html>')
    return '\n'.join(parts)
