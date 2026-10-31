# Progress log

## 2026-10-30 — CI bundle checks and reproducibility walkthrough

- Verified the standalone GitHub repository and project README and read current
  README, roadmap, progress and workflow. No applicable AGENTS.md was found.
  Started from clean published commit 50152aa; Conference-Publications was untouched.
- Extended the existing read-only GitHub Actions workflow with named steps for
  synthetic dataset verification and default/configured bundle export/verification.
- Added docs/REPRODUCIBILITY.md with matching local commands, extracted-source
  reproduction instructions, failure interpretation and research limitations.
- Local verification: all 97 tests pass; assessment generation, dataset checks
  and both bundle export/verification workflows pass; git diff --check passes.
  No new tests were added for this workflow/documentation change. Remote CI
  status is separate from local results and is not presumed here.
- Synthetic labels, unknowns and unvalidated scoring settings are preserved.
  No generated ZIPs, private material or real-case scores are included in the commit.
- Prepared for GitHub publication; remote commit verification is reported in the
  run result. Next: report accessibility/navigation review. Independent validation
  still requires a second rater and reviewed scoring decisions.

## 2026-10-29 — Read-only bundle verification

- Verified the standalone GitHub repository and project README; read current
  README, roadmap and progress. No applicable AGENTS.md was found. Started from
  clean published commit e6c3ac6; Conference-Publications was untouched.
- Added verify_bundle.py to check the fixed schema-v1 inventory, exact-byte
  hashes, synthetic dataset manifest and dataset identity without extraction or
  executing bundled code. Shared strict JSON parsing now accepts in-memory text.
- Added size limits and rejection of duplicate/unexpected members, symlinks,
  encrypted entries and unsupported compression. Documented consistency versus
  authenticity and report-reproduction limitations.
- Verification: 97 tests pass, including eight verifier tests and the existing
  extracted-source report reproduction tests; git diff --check passes.
- Synthetic labels, unknowns and unvalidated scoring settings are preserved.
  No real-case scores, manuscripts or private co-author materials were added.
- Prepared for GitHub publication; remote commit verification is reported in the
  run result. Next: continuous-integration bundle checks and reproducibility guide.
  Research validation still needs a second rater and reviewed scoring decisions.

## 2026-10-28 — Reproducible synthetic evaluation bundle

- Verified the standalone GitHub repository/README and read current README,
  roadmap and progress. No applicable AGENTS.md was found; started from clean
  published commit 3b38eac. Conference-Publications was untouched.
- Added evaluation_bundle.py: validate a synthetic dataset against its manifest,
  build both report formats, check shared results/provenance, and export a new ZIP
  containing inputs, required source files, reproduction instructions and hashes.
- ZIP timestamps are fixed format metadata, not invented progress dates. Export
  preserves existing paths and validates/renders before opening the destination.
- Verification: 89 tests pass, including six bundle tests. Extracted source
  reproduces default/configured JSON objects and HTML bytes. Checks cover file
  inventories, repeatable ZIP bytes, disagreement, malformed inputs and protected
  destinations. git diff --check passes.
- Preserved synthetic labels, explicit unknowns and unvalidated scoring settings.
  No real-case scores, private material or manuscripts were added.
- Prepared for GitHub publication; remote verification is reported in the run
  result. Next: read-only bundle integrity verification. Research validation
  remains pending a second rater and reviewed scoring decisions.

## 2026-10-27 — Versioned synthetic dataset verification

- Verified the standalone GitHub repository and README, then read the current
  roadmap, progress log and input gates. No applicable AGENTS.md was found.
  Started from published commit 96d72f1 with a clean working tree.
- Added `data/synthetic_manifest.json` version 1.0.0 for the three unchanged
  synthetic cases, plus `dataset_manifest.py` for read-only verification.
- Verification checks strict manifest structure/version, explicit synthetic
  status, ordered IDs and the existing parsed-input SHA-256 convention.
  README documents version updates and the trusted-manifest limitation.
- Checks: 83 tests pass, including eight new manifest tests and existing report,
  editing and viewer regressions. Default manifest verification and whitespace
  checks pass. Publication and remote SHA verification are reported in the run result.
- Synthetic labels, unknowns, ratings and unvalidated thresholds are unchanged.
  No real-case scores, manuscripts, private co-author material or conference files
  were added; Conference-Publications was untouched.
- Next: reproducible synthetic evaluation bundle. Independent research validation
  remains pending a second rater and reviewed scoring decisions.

## 2026-10-26 — Report reproducibility metadata

- Verified GitHub repository and README and read current roadmap, progress and
  input gates. No applicable AGENTS.md was found. Conference-Publications was
  untouched. The remote publication commit contains the same files as the five
  prior local commits; this update is based on that remote commit.
- Added shared deterministic fingerprints of the loaded dataset and supplied
  configuration, plus explicit normalized weights, threshold and numeric floors.
  Assessment/comparison JSON, HTML and browser comparison views expose metadata.
- Fingerprints describe parsed inputs, not original bytes, source authenticity
  or validated research. No scoring values, synthetic labels or evidence changed.
- Verification: 75 tests pass, including seven new reproducibility tests and
  default/configured CLI report checks. Viewer check and diff whitespace checks
  pass. Research gates remain pending a second rater and reviewed scoring choices.
- Prior local-only entries describe their original runs; those five updates are
  now published together in remote commit a4a2b72499be805add1c658b7b4d0730b5b8bf15.
- This tested update is prepared for GitHub publication; publication and remote
  SHA verification are reported in the run result rather than presumed here.
- Next: versioned synthetic dataset manifest and verification command.

## 2026-10-25 — Read-only local browser viewer

- Verified the standalone GitHub repository and project README; read the
  retained README, roadmap, progress log and input gates. No repository-level
  AGENTS.md applies, and Conference-Publications was untouched.
- Added `viewer.py` for comparison tables, evidence records and optional draft
  audit previews. It loads through the same strict validation path and performs
  no file writes.
- Restricted serving to loopback hosts. Only GET/HEAD routes are implemented;
  POST/PUT/PATCH/DELETE return 405. Responses include no-store, nosniff and a
  restrictive Content Security Policy.
- Verification: 68 tests pass, including 10 live local-server tests; default and
  configured assessment/comparison modes, case-copy, editor, draft and viewer
  check workflows pass; `git diff --check` passes.
- Synthetic labels, evidence links, explicit unknowns, weights and unvalidated
  thresholds remain unchanged. No real-case scores, manuscripts, private
  materials or conference content were added.
- The synthetic software workflow milestone is complete locally. Research
  validation is pending a second rater plus reviewed weights, floors, thresholds
  and rating anchors. Local commit only; no push.

## 2026-10-24 — Auditable multi-edit drafts

- Verified the standalone GitHub repository and project README; read the
  retained README, roadmap, progress log and input gates. No repository-level
  AGENTS.md applies, and Conference-Publications was untouched.
- Added `draft.py` and an explicitly synthetic example draft for previewing and
  confirming multiple rating changes as one operation.
- Generated audit entries contain ordered case/group/dimension targets and full
  before/after ratings. Duplicate targets are rejected as ambiguous.
- All edits are applied to a copy and validated before output; any invalid edit
  rejects the draft. Preview writes nothing, while confirmed export uses the
  protected new-file path.
- Verification: 58 tests pass, including nine draft tests; default/configured
  assessment and comparison modes pass; case-copy, single-edit and multi-edit
  CLI workflows pass; `git diff --check` passes.
- Synthetic labels, evidence links, explicit unknowns, weights and unvalidated
  thresholds remain unchanged. No real-case scores, manuscripts, private
  materials or conference content were added.
- Next: read-only local browser views for comparisons, evidence and draft audits.
  Independent validation remains pending a second rater and reviewed scoring
  decisions. Local commit only; no push.

## 2026-10-23 — Guarded synthetic rating editor

- Verified the standalone GitHub repository and project README; read the
  current retained README, roadmap, progress log and input gates. No repository
  AGENTS.md applies, and Conference-Publications was untouched.
- Added `editor.py` for a single synthetic control/risk rating edit with strict
  value validation, required rationale and confidence, preview and confirmation.
- Non-synthetic cases are blocked. Source references are preserved, explicit
  unknowns remain null, the loaded input is not mutated and protected export
  prevents replacement of existing paths.
- Cancellation at every prompt and unconfirmed previews write no output.
- Verification: 49 tests pass, including 10 editor tests; default/configured
  assessment and comparison modes pass; import/export and editor CLI round
  trips pass; `git diff --check` passes.
- Synthetic labels, weights and unvalidated thresholds are unchanged. No
  real-case scores, manuscripts, private materials or conference content were added.
- Next: multi-edit drafts with an auditable change list and atomic confirmation.
  Independent validation remains pending a second rater and reviewed scoring
  decisions. Local commit only; no push.

## 2026-10-22 — Strict dataset import and protected export

- Verified the standalone GitHub repository and project README; read the
  retained README, roadmap, progress log and input gates. No repository-level
  AGENTS.md instructions are present, and Conference-Publications was untouched.
- Added a shared strict JSON loader used by assessment, comparison and case-copy
  commands. It rejects duplicate keys and non-finite values, including exponent
  overflow.
- Added `case_io.py` to validate datasets and optionally export an exact,
  protected copy to a new path. Existing files and symlink targets are not replaced.
- Required explicit rating values (`null` means unknown), valid source objects,
  unique case/source IDs and intact evidence references before export.
- Verification: 39 tests pass, including 14 import/export tests; default and
  configured assessment and comparison modes pass; CLI round trip passes;
  `git diff --check` passes.
- Synthetic labels, unknown semantics, weights and unvalidated thresholds are
  unchanged. No real-case scores, manuscripts, private materials or conference
  content were added.
- Next: rebuild guarded synthetic editing and then multi-edit drafts. Independent
  validation remains pending a second rater and reviewed scoring decisions.
  Local commit only; no push.

## 2026-10-21 — Accessible case comparison

- Verified the standalone GitHub repository and its README, roadmap and
  progress log. Workspace maintenance had removed the local checkout and all
  unpushed commits, so the published repository was freshly cloned as the
  authoritative baseline. No Conference-Publications files were accessed.
- Added `compare.py` for side-by-side comparison of two or more cases in JSON
  and accessible HTML tables.
- Preserved explicit unknowns and synthetic labels. Human-control differences
  are shown only when comparable values exist; ordinal risk dimensions remain
  separate and are not aggregated.
- The comparison notice explicitly retains unvalidated weights, floors and
  thresholds and does not claim evidence verification or legal/safety findings.
- Verification: 25 tests pass, including eight comparison tests; default and
  configured assessment modes pass; default and configured comparison modes
  pass; `git diff --check` passes.
- No real-case scores, private materials or conference content were added.
- Next: rebuild validated import/export and synthetic editing on this retained
  baseline. Independent validation still needs a second rater and reviewed
  scoring decisions. Local commit only; no push.

## 2026-10-12 — Standalone project preparation

- Preserved the earlier five-dimensional calculator and its eight tests.
- Added structured risk profiles and per-rating evidence records.
- Added configurable component floors and missing-evidence score bounds.
- Added JSON and escaped HTML reports with full assessment details.
- Added nine tests, a draft rating guide, project scope and development roadmap.
- Local verification: 17 tests pass; default and configured CLI runs produce reports.
- Removed the project promotion from the Conference-Publications README on GitHub.
- Redirected scheduled work away from Conference-Publications.
- Created the standalone public repository with user authorization: https://github.com/hrix7/ACW-Accountability-Lab.
- Published the prepared source, test suite and documentation; removed the old nested project from Conference-Publications.
- Interactive editor, real-case research and independent validation remain pending.
