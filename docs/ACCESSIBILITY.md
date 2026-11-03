# Report accessibility review

## Assessment export: 2026-11-01

Code inspection found that assessment HTML had no case navigation, no table
captions and risk-dimension cells marked as ordinary data cells. The update adds:

- Case navigation linked to focusable headings, using generated positional
  anchors so arbitrary case IDs/titles cannot create invalid or duplicate IDs.
  Titles and case IDs distinguish records with identical titles.
- A main landmark and visible focus outlines. Each case has a return link.
- A case-specific caption and explicit column/row header scopes for risk tables.
- Case-specific native disclosure summaries for complete evidence/calculations.
  Text is escaped, unknowns stay explicit, and scoring/data are unchanged.

The table choices follow W3C WAI guidance reviewed on 2026-11-01:
[header cells and scope](https://www.w3.org/WAI/tutorials/tables/one-header/)
and [table captions](https://www.w3.org/WAI/tutorials/tables/caption-summary/).
Captions identify tables; scope identifies header direction. These are structural
improvements, not evidence of full WCAG conformance.

## Verified and pending

Automated tests parse rendered HTML to check link targets, unique IDs, case
labels, caption/header structure, unknown display and complete evidence JSON.
They also check untrusted/duplicate titles and input preservation. Existing
bundle tests rerun extracted source and compare generated HTML bytes.

Manual evaluation is pending: use keyboard-only navigation to follow case and
return links, open/close disclosures, inspect focus visibility, and read each
table with a screen reader. Check zoom and narrow screens with long titles.
Record actual browser/assistive-technology versions and observations when this
is performed; no user testing or assistive-technology results are asserted here.

## Comparison and viewer follow-up: 2026-11-01

Code inspection confirmed that the viewer's Comparison link targeted an empty
element before evidence, while comparison tables appeared after the draft.
The viewer now renders comparison tables first, followed by evidence and draft
sections inside one main landmark. Comparison navigation targets that landmark;
evidence/draft links target their headings. Table navigation targets each
comparison heading. Targets are focusable, with visible focus styling.

Comparison tables now have descriptive captions and include case IDs alongside
titles in column headers; existing row/column scopes are retained. Viewer
evidence summaries also include IDs. Long evidence text wraps. The table changes
apply the W3C guidance linked above.

Three additional structural tests verify target resolution and content order,
caption/header identity with duplicate and untrusted titles, preservation of
unknowns and complete evidence, and unchanged draft audit JSON. Existing live
server tests check read-only endpoints and security headers; bundle tests check
reproducible HTML. These do not establish browser or screen-reader usability.
The manual checks above remain pending for all three report surfaces.

Next software work: make per-case evidence inspection easier without requiring
users to read the complete raw JSON disclosure. Research validation remains
pending independent ratings and reviewed scoring decisions.

## Structured viewer evidence: 2026-11-02

Each case disclosure now includes separate captioned control/risk evidence
tables with scoped dimension and column headers. The source catalog uses a
description list, retaining source IDs, titles, URLs and locators. Empty
citations/catalogs and unknown ratings are explicit. Supplied confidence and
assessment dates are labeled as such. The original raw record remains present.

Tests compare rendered fields with the inputs, cover escaped source text and
unknowns, and retain raw-record checks. Source fixtures are explicitly synthetic
and are not added to the dataset. No external source is fetched or verified.
Keyboard, zoom and assistive-technology evaluation remains pending, including
the wider evidence tables with long rationales.
