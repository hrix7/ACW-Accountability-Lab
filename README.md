# ACW Accountability Lab

**Autonomous Cyber Systems: Risk, Evidence & Human Control**  
Independent research software project by Hritika Adhikary · v0.2.0

Explore how autonomy, propagation, target selection, reversibility, attribution and civilian exposure interact with human control. This standalone project has its own code, evidence records, tests and roadmap. Its development is not tied to a conference deadline.

## Start here

Python 3.10+; no third-party packages required. From this repository root:

```bash
python project.py
python -m unittest discover -s tests -v
```

Open `reports/assessment.html` in a browser. The same results, inputs and evidence are in `reports/assessment.json`.

To explore an explicitly chosen threshold and component floors:

```bash
python project.py --config data/example_config.json
```

Generate an accessible side-by-side comparison of the synthetic examples:

```bash
python compare.py
python compare.py --config data/example_config.json
```

Open `reports/comparison.html`, or inspect the auditable matrix in
`reports/comparison.json`. Unknown values stay unknown, and ordinal risk
dimensions are displayed separately rather than collapsed into a risk score.

Validate a case dataset and optionally export a protected copy:

```bash
python case_io.py --input data/case_records.json
python case_io.py --input data/case_records.json --output my_cases.json
```

Export requires a new filename and never replaces an existing file. Assessment,
comparison and case-copy commands reject duplicate JSON keys and non-finite
numbers. Explicit `null` is retained as unknown; a missing `value` field is an
error. These checks validate structure and references, not source truth or
numeric scoring conventions.

Edit one synthetic control or risk rating through a preview-and-confirm flow:

```bash
python editor.py --input data/case_records.json --output edited_cases.json
python project.py --input edited_cases.json
```

The editor is deliberately limited to synthetic cases. It requires a rationale
and confidence label, preserves evidence links, supports explicit unknowns, and
exports through the same protected new-file path. Cancellation or anything
other than an exact `yes` confirmation writes nothing.

Preview several synthetic edits as one auditable draft:

```bash
python draft.py --draft data/example_draft.json --output drafted_cases.json
python draft.py --draft data/example_draft.json --output drafted_cases.json --confirm
```

The first command prints the ordered before/after change list and writes
nothing. The confirmed command validates every change before protected export;
one invalid entry rejects the entire draft. Repeated targets are rejected so
the audit trail remains unambiguous.

Open a loopback-only, read-only browser view:

```bash
python viewer.py --draft data/example_draft.json
```

Then visit `http://127.0.0.1:8000`. The viewer shows comparison tables,
evidence records and the draft audit. It accepts only GET/HEAD requests, exposes
no write endpoint, adds restrictive browser headers and refuses non-loopback
hosts. Use `python viewer.py --draft data/example_draft.json --check` to validate
and render in memory without starting a server.

`data/case_records.json` contains three synthetic examples. Copy their structure to create a case dataset and pass `--input my_cases.json`. The original small control calculator remains available as `python mhc.py`; its default 0.87 threshold is legacy and illustrative. The main project has no default approval threshold.

## Reproducing a report

Assessment and comparison JSON exports include `provenance`; their HTML exports
and the local viewer display the same metadata. It records a SHA-256 fingerprint
of the loaded dataset, a fingerprint of the supplied configuration, and the
actual normalized weights, threshold and numeric component floors used.

Fingerprints use Python JSON serialization with sorted object keys, compact
separators, UTF-8, unescaped Unicode and non-finite numbers rejected. JSON
whitespace and object key order do not affect them; case order, numeric
representation (for example `1` versus `1.0`), unknowns and evidence text do.
An omitted configuration is fingerprinted as `{}`. These are parsed-input
fingerprints, not hashes of original file bytes or evidence verification.

Retain the input files and repository commit alongside an exported report.
Rerun the command with those files and compare the `provenance` fields; the
existing `model_version` identifies the scoring model, not the software commit.
No timestamps, local paths or private environment information are added.

## Verifying the synthetic dataset

```bash
python dataset_manifest.py
```

This read-only command checks `data/case_records.json` against the versioned
`data/synthetic_manifest.json` (dataset `acw-synthetic-examples`, version `1.0.0`).
It validates the records, requires every case to be explicitly synthetic, and
checks ordered case IDs and the same parsed-input fingerprint used in reports.
Use `--input FILE --manifest FILE` to verify an explicitly selected pair.
Success exits 0; malformed inputs or mismatches exit 2 without writing files.

The dataset version is independent of the scoring model version. Retain the
manifest and data together at a repository commit. For an intentional dataset
revision, review the full data diff, assign a new dataset version and update the
manifest digest and ordered IDs in the same commit. Do not regenerate the
manifest merely to silence a mismatch. Verification compares against a trusted
manifest; changing both data and manifest can produce a match. It does not
verify source truth, scoring validity, or the correctness of a version label.
This initial manifest covers the three existing synthetic examples only.

## Creating a synthetic evaluation bundle

```bash
python evaluation_bundle.py --output evaluation.zip
python evaluation_bundle.py --config data/example_config.json --output configured-evaluation.zip
```

Each ZIP contains the verified synthetic dataset and manifest, supplied
configuration, assessment/comparison JSON and HTML, the required Python source
snapshot, reproduction instructions and a SHA-256 file inventory (`BUNDLE.json`).
The command checks report provenance and shared results before export. Existing
files and symlinks cannot be replaced; the output parent directory must exist.
Use `--input` and `--manifest` to select another verified synthetic dataset with
at least two cases. Invalid data or configuration produces no bundle.

Extract the ZIP and follow its README to rerun the included source into a new
`rerun/` directory. JSON objects and HTML bytes should match the included reports.
ZIP metadata is fixed for reproducible output from identical ordered inputs and
source files; the ZIP timestamp is a format constant, not an assessment date.
Checksums cover exact bytes of every included file except the inventory itself.
They do not authenticate a bundle whose files and inventory were both changed.
This is a synthetic software demonstration; research validation remains pending.

## Verifying an evaluation bundle

```bash
python verify_bundle.py evaluation.zip
```

This read-only command checks the schema-v1 file inventory, every listed SHA-256
checksum, and the synthetic dataset against its manifest and inventory identity.
It rejects missing, unexpected or duplicate members, symlinks, encrypted entries,
unsupported compression and oversized files (8 MiB per file, 32 MiB total).
It never extracts files or executes bundled source. Success exits 0; invalid
bundles exit 2. The shared strict JSON parser rejects ambiguous inventory keys.

A match establishes internal consistency only. It does not authenticate the
archive or recalculate reports: changing a file and its checksum together can
pass. Use the documented reproduction workflow with a trusted source snapshot
for report reproduction. Synthetic labels and unvalidated thresholds still apply.

The GitHub Actions workflow runs dataset verification and exports/verifies both
default and configured evaluation bundles after the test suite. See the
[reproducibility walkthrough](docs/REPRODUCIBILITY.md) to run the same checks locally
and understand what each check establishes.

## Working now

- Six-dimensional risk profiles, stored separately from human-control scores.
- Five human-control dimensions with configurable normalized weights.
- Evidence references, rationales, confidence labels, assessment dates and scenario scope.
- Unknown evidence preserved as null, with a possible score interval rather than an invented point estimate.
- Separate component-floor checks so an average cannot hide a failed control requirement.
- Weight sensitivity analysis and JSON/HTML report exports.
- Side-by-side accessible JSON/HTML case comparison.
- Strict dataset import, guarded editing and a read-only local viewer, 97 automated tests, and a GitHub
  Actions workflow.

## Full project scope

| Module | Current state | Next work |
|---|---|---|
| Assessment engine | Working | Versioned scoring conventions and reviewer feedback |
| Case and evidence records | Working JSON format | Source-backed real cases and evidence review |
| Reports | Assessment and accessible comparison HTML + JSON | Additional visual summaries |
| Assessment interface | Assessment, comparison, guarded editing and read-only browser viewing | Source management and browser editing |
| Validation | Software tests passing | Independent ratings, disagreement analysis and sensitivity study |
| Research documentation | Initial method and roadmap | Literature-backed anchors and reproducible case study |

Read [methodology](docs/METHODOLOGY.md), [rating guide](docs/RATING_GUIDE.md), [roadmap](docs/ROADMAP.md), [inputs needed](docs/INPUTS_NEEDED.md), and [progress](docs/PROGRESS.md).

## Interpretation

All examples are synthetic. The initial rating conventions, weights and thresholds are research design choices, not validated risk predictions, legal findings or safety certifications. Evidence references are checked for structure and linkage, not automatically verified for truth. Ordinal risk dimensions are deliberately not summed into one risk probability. This software contains no attack execution capability.

## Rights

Copyright (c) 2026 Hritika Adhikary. All rights reserved. See [LICENSE](LICENSE).
