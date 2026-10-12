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
