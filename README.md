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

`data/case_records.json` contains three synthetic examples. Copy their structure to create a case dataset and pass `--input my_cases.json`. The original small control calculator remains available as `python mhc.py`; its default 0.87 threshold is legacy and illustrative. The main project has no default approval threshold.

## Working now

- Six-dimensional risk profiles, stored separately from human-control scores.
- Five human-control dimensions with configurable normalized weights.
- Evidence references, rationales, confidence labels, assessment dates and scenario scope.
- Unknown evidence preserved as null, with a possible score interval rather than an invented point estimate.
- Separate component-floor checks so an average cannot hide a failed control requirement.
- Weight sensitivity analysis and JSON/HTML report exports.
- Input validation, 17 automated tests, and a GitHub Actions workflow ready for publication.

## Full project scope

| Module | Current state | Next work |
|---|---|---|
| Assessment engine | Working | Versioned scoring conventions and reviewer feedback |
| Case and evidence records | Working JSON format | Source-backed real cases and evidence review |
| Reports | Working HTML + JSON export | Comparative views and accessible visual summaries |
| Assessment interface | CLI working | Interactive case editor, import/export and comparison |
| Validation | Software tests passing | Independent ratings, disagreement analysis and sensitivity study |
| Research documentation | Initial method and roadmap | Literature-backed anchors and reproducible case study |

Read [methodology](docs/METHODOLOGY.md), [rating guide](docs/RATING_GUIDE.md), [roadmap](docs/ROADMAP.md), [inputs needed](docs/INPUTS_NEEDED.md), and [progress](docs/PROGRESS.md).

## Interpretation

All examples are synthetic. The initial rating conventions, weights and thresholds are research design choices, not validated risk predictions, legal findings or safety certifications. Evidence references are checked for structure and linkage, not automatically verified for truth. Ordinal risk dimensions are deliberately not summed into one risk probability. This software contains no attack execution capability.

## Rights

Copyright (c) 2026 Hritika Adhikary. All rights reserved. See [LICENSE](LICENSE).
