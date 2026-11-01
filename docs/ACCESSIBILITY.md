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

Comparison HTML and the read-only viewer need a separate navigation/table
review. These notes do not mark that work complete. Research validation remains
pending independent ratings and reviewed scoring decisions.
