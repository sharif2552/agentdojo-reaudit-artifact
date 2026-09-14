# Frozen Confirmatory Analysis Plan (v5.1)

Status: frozen after the v5.0 provider-access preflight and before any v5.1 call on 2026-08-17. The 73 v5.0 attempts are an excluded operational preflight stratum.

## Population and analysis units

The target population is the complete AgentDojo 0.1.35 Workspace v1.2.2 suite under the three agent models, four defenses, and two attack templates in `results/expanded_design_v5_1.json`. The primary unit is one planned execution cell. The design contains 480 benign and 13,440 injection cells. Neither v4 nor the v5.0 provider preflight is pooled into primary v5.1 estimates.

## Record sets and denominators

- `N_planned`: cells in `results/planned_cells_v5_1.jsonl`.
- `N_attempted`: planned cells with at least one append-only attempt.
- `N_executed`: cells with a completed provider execution.
- `N_state_validated`: completed cells accepted by the canonical schema, delta/hash, and predicate validator.

Primary complete-case denominators use `N_state_validated`. Every table also reports `N_planned`, and unresolved cells receive deterministic all-fail/all-success bounds. No operational failure is recoded as task failure.

## Primary outcomes

1. Native utility: the installed task's deterministic utility predicate, by model, defense, and phase.
2. Native targeted attack success: the installed injection-task security predicate, by model, defense, and attack template.
3. Joint utility/security state under injection: `(utility, attack_succeeded)` in all four Boolean combinations.
4. Canonical evidence consistency: agreement among recomputed predicates, stored predicate values, pre/post hashes, and recomputed structural delta. Any inconsistency is a validation failure, not an outcome.

The benchmark predicates are benchmark-defined operational outcomes.

## Contrasts and multiplicity

Within each model and phase, each defense is contrasted with `no_defense`. For injection outcomes, contrasts are also stratified by attack template. Holm correction controls the family-wise error rate within each outcome/model contrast family. Unadjusted 95% intervals are labelled descriptive. Cross-model comparisons are secondary.

## Uncertainty and clustering

Report counts, proportions, and 95% intervals. Primary intervals use a two-stage clustered bootstrap: resample user tasks, then injection tasks within sampled user tasks for injection outcomes, with 10,000 replicates and seed 1729. Benign outcomes resample user tasks. A logistic mixed-effects model with user-task and injection-task random intercepts is a sensitivity analysis; convergence failures are reported without substituting a simpler model silently.

## Missingness and sensitivity analyses

Report operational failures by model, defense, phase, user task, injection task, attack, status, and attempt. Provide complete-case estimates and planned-denominator all-fail/all-success bounds. Report temporal strata separately. Repeat task-level summaries using equal task weighting, micro-averaging across cells, and exclusion of cells lacking state validation.

## Figures

Generate from frozen machine-readable artifacts only:

1. planned/attempted/executed/state-validated coverage;
2. utility versus attack-success trade-off by model and defense;
3. missingness and operational-failure composition.

Every manuscript number must be read from a generated analysis table. Manual numerical transcription into prose must be checked by a manuscript consistency test.
