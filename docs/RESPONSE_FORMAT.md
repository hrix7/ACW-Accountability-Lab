# Synthetic practice response format v1

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
| schema_version | Integer 1 |
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
Structured source linkage and repository-commit verification remain future work. Actual
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
