# Blank synthetic rating worksheet

Template only — no reviewer responses or completed review are recorded here.
Copy this file once per reviewer and case, following [the handoff procedure](REVIEW_HANDOFF.md).
Keep completed copies outside the public checkout until publication is explicitly authorized.

## Record identity

- Worksheet status: pending
- Synthetic: true
- Case ID:
- Reviewer alias:
- Actual assessment date (YYYY-MM-DD):
- Repository commit:
- Dataset ID:
- Dataset version:
- Dataset SHA-256 (parsed-input convention):
- Rating-guide commit:
- Scenario scope and system/version assumptions:
- Materials supplied (files and versions):
- Prior exposure to example ratings/rationales (describe, or explicitly state none):
- Independent rating conditions and deviations:

Do not enter names, dates or answers on another person's behalf. Blank means
unanswered, not an assessed unknown. For a considered but unsupported rating,
enter the literal word `unknown` and explain why. If later converted into a
validated case record, `unknown` becomes JSON null; unanswered rows must never
be silently converted. This Markdown worksheet is not an engine input.

## Human control

Use 0–1 or `unknown`. Confidence is low, medium, high or unknown, supplied by
the reviewer and never a numeric weight. Anchors in the rating guide are
unvalidated; explain intermediate values. No weight, floor or threshold is
selected by this worksheet.

| Dimension | Value | Confidence | Rationale / reason unknown | Source IDs and locators, or explicit no source |
|---|---|---|---|---|
| understand | | | | |
| predict | | | | |
| override | | | | |
| time | | | | |
| audit | | | | |

## Risk profile

Use an integer 0–3 or `unknown`. These ordinal dimensions must not be summed
or averaged into a probability. Automation alone does not establish AI use.

| Dimension | Value | Confidence | Rationale / reason unknown | Source IDs and locators, or explicit no source |
|---|---|---|---|---|
| autonomy | | | | |
| propagation | | | | |
| target_selection | | | | |
| irreversibility | | | | |
| attribution_difficulty | | | | |
| civilian_exposure | | | | |

## Evidence inventory

Record each cited source's ID, title, URL and exact page/section locator.
For a synthetic scenario assumption, identify the supplied file/field and label
it synthetic; do not turn that assumption into a public factual source.
If there are no sources, explicitly say so when completing the worksheet.

| Source ID | Title | URL or supplied file | Locator | Synthetic assumption or public source |
|---|---|---|---|---|
| | | | | |

## Reviewer closeout

- Unresolved evidence gaps or conflicting accounts:
- Proposed rubric clarifications (do not silently change anchors):
- Actual completion date:
- Status (incomplete / complete for review):
- Permission and scope for sharing this completed record:

Completion means the reviewer filled the record, not that the ratings are
correct or validated. Preserve the original before any discussion or revisions.
