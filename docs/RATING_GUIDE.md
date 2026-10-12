# Draft rating guide

These are initial project conventions requiring literature review and independent-rater testing. Never infer a low risk or high control rating merely because evidence is absent. Use null with an explanation.

## Risk profile

Ratings are ordinal, not probabilities. Each dimension retains its own interpretation; do not sum or average these values.

| Dimension | 0 | 1 | 2 | 3 |
|---|---|---|---|---|
| Autonomy | Each action directly commanded | Bounded execution after approval | Multiple decisions within a bounded objective | Broad action discretion with little intervention |
| Propagation | No propagation within scenario | Fixed allowlisted hosts | Can expand within a bounded environment | Open-ended expansion described |
| Target selection | Human chooses each target | System proposes, human approves | Selects within explicit target bounds | Broad autonomous selection |
| Irreversibility | Effects demonstrably reversible | Recovery simple and verified | Recovery partial or costly | Lasting or unrecoverable effects described |
| Attribution difficulty | Strong verified provenance | Mostly traceable | Significant gaps or competing accounts | Attribution highly uncertain |
| Civilian exposure | Exclusion supported within scope | Limited potential exposure | Substantial potential exposure | Broad or critical-service exposure |

Autonomy ratings alone do not establish AI involvement. Record evidence of AI separately in the scope/rationale; automated scripted behavior is not sufficient.

## Human control

Dimensions: understand, predict, override, time, audit. Higher values indicate stronger demonstrated control within the stated scenario. Initial anchors: 0 = documented absence; 0.5 = partially demonstrated; 1 = demonstrated throughout the stated scope. Intermediate values require explicit rationale. Missing evidence remains null rather than 0.

These anchors are deliberately preliminary and cannot substantiate external validity. Confidence (low/medium/high/unknown) is a reviewer annotation and is not used as a numeric weight.

## Evidence record requirements

For every non-synthetic numeric rating, cite at least one source ID. Each source includes a title, URL and page/section locator. Record the scenario boundary and assessment date. Software checks referenced IDs exist but does not authenticate sources, resolve conflicting accounts, or infer whether claims are supported. Reviewers must do that work. Do not mix incompatible versions or scenarios into a single rating.
