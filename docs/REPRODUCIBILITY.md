# Synthetic evaluation reproducibility

Use a trusted checkout of this standalone repository with Python 3.10+.
Record the revision with `git rev-parse HEAD`; source changes can change results.
No external data downloads or third-party Python packages are required.

## Run the checks

From the repository root, in a fresh checkout or with unused ZIP output names:

```bash
python -m unittest discover -s tests -v
python project.py
python dataset_manifest.py
mkdir -p reports/ci
python evaluation_bundle.py --output reports/ci/default-evaluation.zip
python verify_bundle.py reports/ci/default-evaluation.zip
python evaluation_bundle.py --config data/example_config.json --output reports/ci/configured-evaluation.zip
python verify_bundle.py reports/ci/configured-evaluation.zip
```

These are the checks configured in GitHub Actions. The test suite includes
extracting freshly generated bundles into temporary directories, running their
included source, and comparing regenerated JSON objects and exact HTML bytes
for default and configured settings. The two explicit export/verify steps also
exercise the command-line handoff between the exporter and verifier.

The default bundle supplies no approval threshold. The configured bundle uses
the illustrative weights/floors/threshold settings supplied by
`data/example_config.json`; these settings remain unvalidated.

## Inspect and reproduce a bundle

1. Verify the ZIP with `verify_bundle.py` from your trusted checkout.
2. Inspect the verification output. A successful exit reports 15 file checksums
   and the synthetic dataset identity. Any error must be resolved before using
   the bundle as a reproducibility record.
3. For a bundle you generated from trusted source, extract it into a new empty
   directory and follow its `README.txt`. Those commands write regenerated reports
   under `rerun/` and preserve the original `reports/` copy.
4. Compare parsed JSON objects between the two directories and compare HTML
   bytes. JSON whitespace and object key order are not significant for this check.
   Preserve the original ZIP and repository revision alongside the comparison.

The verifier never extracts or executes source. Passing its checks alone does
not establish that bundled code is trustworthy to run.

## Interpret failures

| Failure | What to inspect |
|---|---|
| Dataset fingerprint mismatch | Compare the data against its reviewed manifest; do not regenerate the manifest solely to silence a failure. |
| Existing ZIP output | Choose an unused output name; exports deliberately refuse to replace files or symlink targets. |
| Missing member or checksum mismatch | Obtain the original bundle or inspect the changed files against the trusted revision. |
| Report reproduction mismatch | Compare source snapshot, Python environment, input/configuration and report provenance. |
| CI workflow failure | Open the failed named step; local checks do not establish the remote run's status. |

CI uses Python 3.11 on its configured Ubuntu runner. Generated ZIPs remain in the
job workspace and are not uploaded as release artifacts. The workflow retains
read-only repository permissions and does not publish data or research results.

Passing tests establishes software behavior for the cases tested. Dataset and
ZIP verification establish internal consistency, not authenticity, source truth,
expert agreement, legal conclusions or safety certification. Synthetic labels,
explicit unknowns and unvalidated thresholds remain in force. Independent
research validation still requires a second rater and reviewed scoring decisions.
