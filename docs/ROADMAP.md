# Development roadmap

The full project is underway, not complete. Stages are goals rather than claims of completed research or automatic daily commits.

| Stage | Work | Acceptance evidence | Dependency |
|---|---|---|---|
| Foundation (implemented) | Scoring, risk profiles, evidence records, report exports, tests | CLI demo + passing tests | None |
| Standalone publication (implemented) | Dedicated repository with source and tests; old nested copy removed | https://github.com/hrix7/ACW-Accountability-Lab | Complete |
| Week 1 | Interactive case editor and case comparison; draft source-backed rubric | Import/edit/export round trip; documented rating rationale | No user input needed for synthetic UI work |
| Week 1 | Research 2–3 candidate public case studies | Each claim linked to source location, unknowns retained | Choose or confirm research emphasis |
| Week 2 | Independent review and disagreement analysis | Separate reviewer records; report disagreement without fabricated consensus | Second reviewer |
| Week 2 | Weight/floor sensitivity comparisons and technical write-up | Reproducible commands, stated limitations, auditable evidence | Reviewed scoring decisions |
| Later | Versioned datasets, accessible visual comparison and release package | Versioned methods/data plus repeatable evaluation | Prior research gates |

Do not use conference publication metadata as the project backlog. Scheduled work must only target the standalone repository once it exists.

## 2026-10-21 checkpoint

- Implemented accessible side-by-side JSON and HTML comparisons for two or
  more case records. Control dimensions, evidence status, possible score
  intervals and configured component checks remain auditable by case.
- Unknowns stay explicit. Control differences are omitted where either value
  is unknown, and ordinal risk dimensions are never aggregated into a score.
- Next: rebuild validated import/export and synthetic editing from the current
  published baseline, then add multi-edit drafts.
- Independent validation remains pending a second rater and reviewed decisions
  for weights, floors, thresholds and numeric anchors.

## 2026-10-22 checkpoint

- Added strict shared JSON loading and protected case export. Assessment,
  comparison and case-copy commands now reject repeated keys and non-finite
  numbers consistently.
- Explicit nulls remain unknowns; missing rating values, malformed sources,
  duplicate case IDs and dangling references are rejected before export.
- Export creates a new file only and will not replace input, existing paths or
  symlink targets. Validation does not establish evidence truth or scoring validity.
- Next: rebuild the guarded synthetic editor on this retained foundation, then
  add multi-edit drafts. Independent validation still needs a second rater and
  reviewed weights, floors, thresholds and numeric anchors.

## 2026-10-23 checkpoint

- Added a guarded terminal editor for one synthetic control or risk rating.
  The user selects an existing synthetic case, enters a valid value or explicit
  unknown, rationale and confidence, then reviews a before/after preview.
- Only an exact confirmation exports, using the protected new-file mechanism.
  Cancellation leaves no output, non-synthetic records cannot be edited, and
  evidence links remain intact.
- Next: multi-edit drafts with an auditable change list and all-or-nothing
  confirmation. Independent validation still needs a second rater and reviewed
  weights, floors, thresholds and numeric anchors.

## 2026-10-24 checkpoint

- Added multi-edit draft preview and confirmed export for synthetic ratings.
  The ordered audit shows each target with its complete before/after record.
- Every change is validated on a copy before output. One invalid entry rejects
  the whole draft, repeated targets are rejected, preview writes nothing, and
  confirmed export retains existing-path protection.
- Next: add a read-only local browser view for comparisons, evidence and draft
  audit records. Independent validation still needs a second rater and reviewed
  weights, floors, thresholds and numeric anchors.

## 2026-10-25 checkpoint

- Added a loopback-only, read-only browser viewer for comparison tables,
  complete evidence records and optional draft audit previews.
- The viewer exposes GET/HEAD JSON endpoints only; mutation methods return 405,
  non-loopback binding is rejected, browser security headers are set and no
  input or output file is modified.
- The synthetic software workflow milestone now includes strict import/export,
  case comparison, guarded single edits, multi-edit draft audits and browser
  inspection. Numeric validation and real-case research remain separate gates.
- Next work needs input: identify a second rater and review weights, component
  floors, thresholds and rating anchors before disagreement or sensitivity
  findings are treated as research results.

## 2026-10-26 checkpoint

- Advanced repeatable evaluation with deterministic dataset/config fingerprints
  and explicit effective scoring settings in assessment/comparison JSON and HTML.
  The read-only viewer inherits the same comparison metadata.
- Regression checks establish matching metadata across both report workflows,
  sensitivity to input changes and preservation of unknowns and synthetic data.
- Next: a versioned synthetic dataset manifest and verification command. This
  software preparation does not complete the research-dependent release gate.
- Independent research validation remains pending a second rater and reviewed
  weights, floors, thresholds and rating anchors; no agreement is presumed.
