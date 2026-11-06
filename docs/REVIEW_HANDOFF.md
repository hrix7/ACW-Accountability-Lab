# Synthetic rating handoff

This is preparation for review, not evidence that a second rater participated.
Use [the blank worksheet](RATING_WORKSHEET.md) with the project's
[draft rating guide](RATING_GUIDE.md) and [methodology](METHODOLOGY.md).
All anchors, weights, component floors and thresholds remain unvalidated.

## Pin and verify the materials

From a clean checkout of the intended repository commit:

```bash
git status --short
git rev-parse HEAD
python dataset_manifest.py
```

Resolve or record local differences before handoff: a commit ID alone does not
identify uncommitted changes. Record the full commit and the manifest fields
in every worksheet. Retain these exact files with the handoff:

- `data/case_records.json`
- `data/synthetic_manifest.json`
- `docs/RATING_GUIDE.md` and `docs/METHODOLOGY.md`
- `docs/RATING_WORKSHEET.md` and this procedure

The currently verified manifest describes `acw-synthetic-examples`, version
`1.0.0`, with parsed-input SHA-256
`4d2a0f6fecef0ad398944f08001c3092e90a0836ba8bc8edc964201c80e70a98`.
Its ordered cases are:

1. `synthetic-limited-control`
2. `synthetic-reviewed-defence`
3. `synthetic-incomplete-evidence`

Manifest success checks consistency, not truth, scoring validity or independent
review. If verification fails, stop the handoff and investigate; do not rewrite
the manifest to make it pass.

## Separate practice from independent research

The supplied cases include existing values, confidence labels and rationales;
even their titles can suggest an interpretation. Giving these files to a rater
is an **unblinded synthetic practice exercise**, not a blinded reliability study.
A blank response sheet does not remove that exposure. Log exactly what each
reviewer saw; do not claim independence retrospectively.

Before research use, Hritika must identify a willing second rater and review
rating anchors and the intended scoring decisions. A common scenario/evidence
packet and review protocol must be agreed before collecting independent ratings.
Preparing a packet without prior judgments is future work; deleting values
alone is insufficient when rationales and titles reveal those judgments.

For practice, make one separate worksheet copy per case per reviewer. Carry
case ID and scope exactly, then let the reviewer supply their own answers.
Do not prefill from example ratings, copy another reviewer's rationale, or
invent a date. Do not contact reviewers automatically.

## Preserve and inspect actual responses

Retain each original response separately before discussion. Check all eleven
dimensions are present and distinguish unanswered cells from deliberate unknowns.
Check value ranges, supplied confidence labels, source IDs/locators and reasons
for unknowns. Do not substitute zero for missing evidence.

A separate [JSON response validator](RESPONSE_FORMAT.md) now checks explicit
response states; it does not import or score responses. The worksheet
is Markdown and cannot be passed to `project.py` or `case_io.py`. Do not overwrite
the versioned synthetic dataset with responses. Keep completed worksheets
outside the public checkout; publication of reviewer material requires explicit
authorization and an appropriate privacy review.

Only after real responses exist, align by case ID and dimension, retain both
ratings, flag unknown/unanswered values separately, and document disagreements
without manufacturing consensus. No agreement statistic or validation claim
is supported by this template. Software tests establish software behavior only.

## Pending inputs and next software step

Pending: willing second rater, reviewed anchors/weights/floors/thresholds, and
an agreed evidence packet/protocol for any independent research exercise.
Next software step: bind response identifiers to the verified synthetic packet
and check source linkage. The current validator checks structure only.
