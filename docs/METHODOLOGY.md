# Methodology and open questions

M = sum(w_i s_i), where scores lie in [0,1], weights are nonnegative and sum to one. Consequently min(s) <= M <= max(s). For two weight vectors, |M(w)-M(v)| <= 0.5 ||w-v||_1 (max(s)-min(s)). Tests check implementation properties, not external validity.

The Override sweep changes weights only and holds the comparison threshold fixed. The full-simplex range is exact: when a threshold lies inside it, admissible weights can change the classification.

## Threshold review

The optional `formula_threshold(p,R)` implements t=1-p/R. With p in [0,1] and R=15, t lies in [14/15,1], approximately [0.9333,1]. It cannot yield 0.87. It contains no weights, so changing an Override weight cannot change t without an additional model. The formula and configurable 0.87 setting remain explicit alternatives pending author review. Increasing civilian probability lowers this formula's threshold; review whether this is the intended policy direction.

A weighted average does not enforce component floors. Scores (1,1,0.8,1,1) yield 0.94 under the default weights, above 14/15, while Override is 0.8, below 14/15. An aggregate threshold therefore cannot be claimed sufficient for that component constraint. Required component floors must be checked separately and independently justified.

## Evidence and validation

Keep autonomy, attribution, control and harm distinct. Scripted propagation alone does not establish AI-driven target selection. Missing public evidence does not prove absence of control. For each future rating record source, location, rationale, confidence, system version, date and scenario boundaries. Use null for unknowns; this implementation declines aggregate scoring when a dimension is missing.

Before real-world use: define observable rating anchors; establish source-backed cases; measure independent-rater agreement; elicit weights; validate against an appropriate external criterion. These tasks remain incomplete. No legal determinations or validated risk predictions are produced.

## Standalone engine (v0.2)

`project.py` separates risk profiles from control scores. It applies no threshold by default. Configurable component floors are evaluated separately. Unknown control values yield no point score; bounds use each unknown in [0,1] with fixed chosen weights. Risk ratings stay ordinal and are not aggregated. The override sweep is explicitly based on the original default weights. Sources are structurally linked, not independently authenticated by the software. See RATING_GUIDE.md for initial, unvalidated rating conventions.
