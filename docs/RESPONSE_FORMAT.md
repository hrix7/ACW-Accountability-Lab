# Synthetic practice response formats v1 and v2

Run `python rating_response.py /path/outside/checkout/response.json`.
The command reads only, exits 0 for structurally valid partial or full records,
and exits 2 for invalid records. It never imports answers into case data or
calculates scores/agreement. Keep actual responses outside the public checkout.

This format implements the state distinction in the [worksheet](RATING_WORKSHEET.md).
It is currently limited to explicitly synthetic practice. It is not a replacement
for the handoff record: retain the full worksheet, materials, source inventory,
consent and protocol records separately.

## Required fields (no additional fields)

| Field | Requirement |
|---|---|
| schema_version | Integer 1 or 2 |
| synthetic | Boolean true |
| case_id, scope, exposure | Nonempty strings; describe actual materials/exposure |
| dataset_sha256 | 64 lowercase hexadecimal characters, parsed-input fingerprint |
| repository_commit | Full 40-character lowercase hexadecimal commit |
| reviewer_alias | Nonempty string when any row is answered; otherwise null allowed |
| assessed_on | Actual date, YYYY-MM-DD; required when any row is answered, otherwise null allowed |
| control | Object with exactly understand, predict, override, time, audit |
| risk | Object with exactly autonomy, propagation, target_selection, irreversibility, attribution_difficulty, civilian_exposure |

Each dimension is an object with exactly `state`, `value`, `confidence`,
`rationale`, `evidence_note`.

| State | Value | Other fields |
|---|---|---|
| unanswered | null | confidence, rationale and evidence_note must all be null |
| unknown | null | Supplied confidence and nonempty rationale/evidence_note required |
| rated | Finite number 0–1 for control; integer 0–3 for risk | Supplied confidence and nonempty rationale/evidence_note required |

Confidence is low, medium, high or unknown. Evidence notes identify source IDs
and locators in the separate inventory, synthetic scenario assumptions, or
explicitly state no source. The validator checks text presence only, not linkage
or truth. A considered unknown requires an explanation. Zero is a supplied
rating; an unanswered row is never silently converted to unknown.

A blank dimension object is:
```json
{"state":"unanswered","value":null,"confidence":null,"rationale":null,"evidence_note":null}
```
Repeat it independently for all eleven named dimensions; do not copy example
ratings. Missing fields, duplicate JSON keys, nonfinite values, boolean ratings
and unsupported fields are rejected.

## Limits

Without dataset options, the validator checks identifier syntax only. With the
options below it also checks dataset identity and scope. It does not resolve a
commit, authenticate reviewer identity or date, verify independence, or check consent. A structurally valid
record can still be fabricated or scientifically invalid. No real responses
are shipped with this feature; test records are fabricated software fixtures.
All rating anchors, weights, floors and thresholds remain unvalidated.
Repository-commit verification remains future work. Schema v2 supports the
source linkage checks described below. Actual
independent review needs a willing second rater and agreed scoring/protocol
decisions.


## Optional dataset identity check

```bash
python rating_response.py /path/outside/checkout/response.json --dataset data/case_records.json --manifest data/synthetic_manifest.json
```

Both options are required together; no dataset is selected implicitly. The
command first validates the response, verifies the selected synthetic dataset
against its manifest, and then requires an equal parsed-input fingerprint, a
matching case ID and an exactly equal scope string. Even whitespace changes to
scope fail. Review mismatches rather than editing identifiers to silence them.

The dataset and manifest must come from the intended trusted handoff. Matching
files do not authenticate each other, and the response's repository_commit is
still syntax-checked only. This mode does not compare reviewer ratings with
example ratings, convert unanswered rows, or validate free-text evidence notes.
It writes no files and keeps the same exit codes. Without these options, output
explicitly states that dataset identity was not checked.


## Version 2: structured citations

Schema v1 remains supported unchanged; it has no structured citations and the
CLI explicitly reports that source linkage was not checked. No automatic
migration or citation extraction from free text is performed.

For schema_version 2, every dimension must include one additional field,
`source_ids`: a list of unique, nonempty strings. Unanswered rows require
`[]`. Unknown and rated rows may cite sources or use `[]`; the evidence_note
must still explain the supplied evidence or explicit absence of sources.
A blank v2 dimension is:

```json
{"state":"unanswered","value":null,"confidence":null,"rationale":null,"evidence_note":null,"source_ids":[]}
```

With both dataset options, each ID must exist in the selected case's source
catalog, even if it exists elsewhere in the dataset. The verified catalog holds
titles, URLs and locators. Without dataset options only list structure is
checked, and output explicitly says linkage was not checked.

Membership does not prove that a source supports a rating, that its locator is
correct, or that a URL is available. No URLs are fetched. An empty list is valid
for synthetic practice and is not evidence of quality or completeness. Preserve
original v1 responses; create a separate v2 copy only after actual citation
review, retaining states and explanations. Do not infer citations from example
ratings or fill answers on behalf of a reviewer.


## Generate a blank v2 template

From the intended trusted checkout, supply its full commit identifier and an
explicit preparation/exposure description:

```bash
python response_template.py --dataset data/case_records.json --manifest data/synthetic_manifest.json --case-id synthetic-limited-control --repository-commit "$(git rev-parse HEAD)" --exposure "Preparation only; supplied examples are unblinded; reviewer exposure not yet recorded." --output /path/outside/checkout/blank-response.json
```

Replace the output path with a new file in an existing directory. The generator
verifies the synthetic dataset and manifest, copies the selected case's exact
scope, ID and dataset fingerprint, and validates the resulting v2 record before
exclusive file creation. Existing files and symlinks are never replaced. Invalid
inputs exit 2 without creating output; success exits 0.

All eleven rows remain unanswered with null values, confidence, rationales and
evidence notes, and empty source lists. Reviewer alias and assessment date are
null. Example answers and citations are not copied. Generation does not blind
materials or constitute a reviewer response. Record actual exposure, identity,
date and answers only when review occurs, keeping actual responses outside the
public checkout. The commit is syntax-checked only: this command does not verify
that the supplied files belong to it. Exposure is supplied text, not an observed
or authenticated event. Source truth and scoring conventions remain unvalidated.


## Compare two synthetic practice responses

```bash
python response_compare.py /path/outside/checkout/left.json /path/outside/checkout/right.json --dataset data/case_records.json --manifest data/synthetic_manifest.json
```

The command validates both records against the explicit synthetic dataset and
manifest, including v2 citation membership, then requires the same case ID,
exact scope, dataset fingerprint and repository commit string. A different
commit is rejected even when data match: review the handoff before comparison.
Commit equality does not verify that either record came from that commit.
Versions 1 and 2 can be compared; output identifies which side received source
linkage checks. V1 has no structured citations, not an inferred empty list.

JSON goes to stdout only; no files are created or changed. Success exits 0;
invalid input exits 2 with no JSON output. Keep responses and any redirected
comparison output outside the public checkout: output includes supplied reviewer
metadata, exposure text and complete per-dimension explanations and citations.
Left and right mean command argument order, not verified reviewer identities.

Each dimension has one descriptive status:

| Status | Meaning |
|---|---|
| both_unanswered | Neither row has been answered |
| one_unanswered | Exactly one row is unanswered; the other may be unknown or rated |
| both_unknown | Both deliberately record unknown; explanations may differ |
| unknown_vs_rated | One row records unknown, the other a numeric rating |
| equal_rated | Both numeric values are exactly equal, with no tolerance |
| different_rated | Both numeric values are present and unequal |

Counts are separate for the five control and six risk dimensions. No numeric
differences, averages, aggregate risk scores, agreement percentages or consensus
are calculated. Equal numeric values (including zero) do not mean equal
rationales, confidence, evidence or independent agreement. Unknown and unanswered
are never converted to numeric values. Reviewer identity, independence, supplied
dates/exposure, source truth and scoring validity remain unverified. Same-alias
records and blank templates are allowed for software practice, not evidence of
two independent raters. All thresholds remain unvalidated.
